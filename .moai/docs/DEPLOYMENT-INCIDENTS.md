# 배포 인시던트 보고서

이 문서는 AI English Tutor 프로덕션 배포 과정에서 발생한 인시던트를 기록합니다.

---

## INCIDENT-001: 이미지 분석 파이프라인 4중 버그

- **날짜**: 2026-02-24
- **심각도**: High (핵심 기능 완전 비동작)
- **상태**: 해결됨 (3회 커밋)
- **관련 SPEC**: SPEC-IMAGE-001

### 배경

이미지 분석 기능(교과서 사진 → OCR → 영어 튜터 분석)이 최초 구현 후 첫 프로덕션 배포에서 전혀 동작하지 않았습니다. 로컬 환경에서는 동작하였으나 Vercel + Railway 환경에서 여러 버그가 중첩하여 나타났습니다.

### 인시던트 타임라인

```
2026-02-24 00:30  이미지 분석 기능 배포 완료
2026-02-24 00:40  사용자 테스트: 결과가 항상 비어있음 발견
2026-02-24 01:12  Bug-1 수정 커밋 (e624069): TutorState 필드 추가
2026-02-24 01:40  Bug-2 수정 커밋 (477f00b): Vercel 타임아웃 + SSE 하트비트
2026-02-24 06:36  Bug-3/4 수정 커밋 (31f9fb9): GraphRecursionError + response.ok
2026-02-24 07:00  사용자 확인: "잘 동작한다"
```

### 버그 상세

#### Bug-1: TutorState 누락 필드

**분류**: 설계 결함
**영향**: 이미지 데이터가 LangGraph 노드에 전달되지 않음
**수정 파일**: `backend/src/tutor/state.py`

LangGraph StateGraph는 TypedDict에 정의된 키만 상태로 유지합니다. `image_data`와 `mime_type` 필드가 TypedDict에 없었기 때문에 Frontend에서 전달한 이미지 데이터가 그래프 내부에서 조용히 사라졌습니다.

**수정 내용**:
```python
# 추가된 필드
image_data: NotRequired[str | None]
mime_type: NotRequired[str | None]
```

---

#### Bug-2: Vercel 서버리스 함수 타임아웃

**분류**: 인프라 제약 미반영
**영향**: 이미지 분석이 10초 후 중단, "분석중" 상태로 멈춤
**수정 파일**: `src/app/api/tutor/analyze-image/route.ts`, `backend/src/tutor/routers/tutor.py`

OpenAI Vision API는 이미지 처리에 25-35초가 필요합니다. Vercel Hobby 플랜의 기본 함수 실행 시간은 10초이며, 추가로 프록시 idle timeout(연속 데이터 없을 때 10초 후 연결 종료)도 적용됩니다.

**수정 내용**:
- `maxDuration = 60`: Next.js Route Handler에 Vercel 최대 실행 시간 설정 (Hobby 플랜 최대값)
- SSE 하트비트: 5초마다 `: comment\n\n` 전송 (브라우저/프록시가 무시하는 SSE 주석 형식)

```typescript
// route.ts
export const maxDuration = 60;
```

```python
# tutor.py - 하트비트 생성기
async def heartbeat_producer():
    while not stop_event.is_set():
        await asyncio.sleep(5)
        await queue.put(": comment\n\n")  # SSE comment - ignored by clients
```

---

#### Bug-3: LangGraph GraphRecursionError

**분류**: LangGraph Send() API 동작 오해
**영향**: "Recursion limit of 25 reached" 오류로 분석 실패
**수정 파일**: `backend/src/tutor/agents/image_processor.py`

LangGraph의 `Send()` API는 지정된 노드에 커스텀 입력 상태를 제공하지만, 이 입력이 그래프 전역 상태(graph-level state)를 업데이트하지는 않습니다. 따라서 `image_processor_node`가 `task_type`을 반환하지 않으면, 그래프 상태는 여전히 `task_type="image_process"`를 유지합니다.

`route_by_task("image_process")` → `image_processor` → `route_by_task("image_process")` → ... 무한 루프가 발생하여 LangGraph의 기본 재귀 한도(25)에 도달했습니다.

**수정 내용**:
```python
# 수정 전
return {"extracted_text": extracted_text, "input_text": extracted_text}

# 수정 후
return {"extracted_text": extracted_text, "input_text": extracted_text, "task_type": "analyze"}
```

재귀 한도도 25 → 50으로 증가 (안전망 역할).

---

#### Bug-4: HTTP 오류 무증상 처리

**분류**: 방어적 코딩 누락
**영향**: 오류 발생 시 사용자에게 빈 화면 표시, 디버깅 불가
**수정 파일**: `src/hooks/use-tutor-stream.ts`

`use-tutor-stream.ts` 훅이 `response.ok`를 확인하지 않아 HTTP 4xx/5xx 응답을 성공으로 간주하고 빈 스트림을 읽으려 했습니다.

**수정 내용**:
```typescript
const response = await fetchFn();
if (!response.ok) {
  const errorText = await response.text().catch(() => "");
  let errorMessage = `Analysis failed (${response.status})`;
  try {
    const errorData = JSON.parse(errorText);
    errorMessage = errorData.error || errorData.detail || errorMessage;
  } catch { /* not JSON */ }
  throw new Error(errorMessage);
}
```

---

### 근본 원인 분석 (RCA)

| 요소 | 내용 |
|------|------|
| **직접 원인** | LangGraph TypedDict 필드 누락, Vercel 타임아웃 설정 누락, Send() API 동작 오해 |
| **기여 원인** | 로컬 환경에서는 타임아웃이 없어 이슈 미발견, LangGraph Send() 문서 미숙지 |
| **예방책** | 배포 전 체크리스트, 인프라 제약 문서화, LangGraph 패턴 문서 작성 |

### 재발 방지 조치

1. **TutorState 변경 가이드라인**: 새 필드 추가 시 TypedDict 업데이트 필수
2. **Vercel 배포 체크리스트**: 타임아웃 민감 기능은 `maxDuration` 명시 필수
3. **SSE 하트비트 패턴**: 장시간 실행 SSE 엔드포인트에 기본 적용
4. **response.ok 검증**: 모든 스트리밍 핸들러에 기본 패턴으로 적용
5. **LangGraph Send() 주의사항**: 노드 출력에 `task_type` 포함 필수

---

## 관련 문서

- [SPEC-IMAGE-001](./../specs/SPEC-IMAGE-001/spec.md) - 이미지 분석 파이프라인 명세
- [IMAGE-ANALYSIS-DEPLOYMENT-LEARNINGS](./../learning/IMAGE-ANALYSIS-DEPLOYMENT-LEARNINGS.md) - 상세 학습 가이드
