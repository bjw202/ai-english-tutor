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

---

## INCIDENT-002: 어휘 스트리밍 프로덕션 버그

- **날짜**: 2026-02-26
- **심각도**: Medium (기능 부분 비동작 - 스트리밍 중 표시되나 완료 시 사라짐)
- **상태**: 해결됨 (2회 커밋)
- **관련 SPEC**: SPEC-VOCAB-003

### 배경

어휘 분석 기능의 스트리밍 아키텍처가 SPEC-VOCAB 시리즈(001, 002, 003)로 구현되었습니다. 로컬 개발 환경에서는 완벽하게 동작했으나, Vercel + Railway 프로덕션 환경에서만 이상한 동작을 하였습니다.

### 인시던트 타임라인

```
2026-02-26 14:00  사용자 보고: 어휘 분석이 스트리밍 중에 표시되나 완료되면 사라짐
2026-02-26 14:15  로컬 재현 실패 (로컬에서는 정상 동작)
2026-02-26 14:30  프로덕션 로그 분석: vocabulary_chunk 이벤트가 발송되지 않음 발견
2026-02-26 14:45  근본 원인 파악: h1 heading normalization 버그 + rawContent 폴백 누락
2026-02-26 15:20  Bug-1, Bug-2 수정 배포
2026-02-26 16:00  사용자 확인: 정상 동작 확인
```

### 버그 상세

#### Bug-1: 어휘 정규화 함수의 h1 헤딩 미처리

**분류**: 경계값 미처리 (Edge case)
**영향**: LLM이 생성한 h1 헤딩을 정규화하지 못해 `vocabulary_chunk` 이벤트가 발송되지 않음
**수정 파일**: `backend/src/tutor/utils/markdown_normalizer.py`

문제의 핵심:

```python
# 수정 전: h3-h6 헤딩만 처리
def _normalize_vocab_word_headings(content: str) -> str:
    # ...
    pattern = r'^(#{3,6})\s+(.+)$'  # h3-h6만 매칭
```

어휘 분석 함수 `_parse_vocabulary_words`는 헤딩을 찾아 단어를 추출합니다. 정규화 함수에서 처리하지 못한 h1/h2는 그대로 남아있고, 이를 찾지 못하면 `words = []` 가 되어 `vocabulary_chunk` 이벤트가 조용히 발송되지 않습니다.

LLM은 비결정적(non-deterministic)이므로, 로컬 테스트에서는 h2 형식으로 생성되었으나 프로덕션에서는 때때로 h1 형식으로 생성되는 경우가 있었습니다.

**수정 내용**:

```python
# 수정 후: h1-h6 모든 헤딩 처리
pattern = r'^(#{1,6})\s+(.+)$'  # h1-h6 모두 매칭
```

패턴을 `#{3,6}`에서 `#{1,6}`으로 변경하여 h1, h2 헤딩도 정규화하도록 수정했습니다.

---

#### Bug-2: 프론트엔드 `vocabulary_chunk` 이벤트 폴백 부재

**분류**: 완벽한 경로(Happy path) 테스트만 수행
**영향**: `vocabulary_chunk` 미수신 시 파싱된 `words` 배열이 없어도 rawContent 폴백이 없음
**수정 파일**: `src/components/tutor/vocabulary-panel.tsx`

문제의 핵심:

```typescript
// 수정 전
const handleVocabularyDone = (event: CustomEvent) => {
  const { words, isStreaming } = event.detail;
  if (!words || words.length === 0) {
    setVocabularyContent({
      structured: { words: [] },
      raw: '',
    });
    return;  // rawContent를 무시하고 빈 상태로 설정!
  }
  // ...
};
```

스트리밍 아키텍처에서:
1. 스트리밍 중: 원본 텍스트 청크가 `rawContent`에 누적됨
2. 스트리밍 완료: `vocabulary_done` 이벤트가 파싱된 `words` 배열과 함께 발송됨

그런데 Bug-1 때문에 `vocabulary_chunk` 이벤트가 발송되지 않으면 `words = []`가 되고, 프론트엔드는 기존 `rawContent`를 무시하고 빈 상태로 설정했습니다.

**수정 내용**:

```typescript
// 수정 후: rawContent 폴백 추가
const handleVocabularyDone = (event: CustomEvent) => {
  const { words, isStreaming } = event.detail;
  if (!words || words.length === 0) {
    // words가 없어도 rawContent가 있으면 사용
    if (rawContent.trim()) {
      setVocabularyContent({
        structured: { words: [] },  // 파싱된 단어 없음
        raw: rawContent,             // 원본 텍스트는 표시
      });
    } else {
      setVocabularyContent({
        structured: { words: [] },
        raw: '',
      });
    }
    return;
  }
  // ... 정상 경로
};
```

---

### 근본 원인 분석 (RCA)

| 요소 | 내용 |
|------|------|
| **직접 원인** | LLM 비결정성으로 h1 헤딩 생성, `_normalize_vocab_word_headings` regex 미흡, 프론트엔드 폴백 부재 |
| **기여 원인** | 로컬 테스트는 h2 형식으로만 실행, 아키텍처 차이 (로컬 직접 연결 vs 프로덕션 Vercel 프록시) 무시 |
| **예방책** | 경계값 테스트 (h1-h6 모두), SSE 이벤트 누락 시 복원력, INCIDENT-001의 교훈 미적용 |

### 재발 방지 조치

1. **LLM 출력 파서 경계값 테스트**: `_parse_vocabulary_words`에 h1-h6 모든 헤딩 레벨 테스트 추가
2. **Markdown 정규화 함수 개선**: 주석에 "h1-h6 모두 처리" 명시, 단위 테스트에서 h1 입력 포함
3. **프론트엔드 스트림 이벤트 폴백**: 구조화된 데이터 이벤트(`vocabulary_chunk`) 미수신 시 rawContent 폴백
4. **프로덕션 SSE 테스트**: 스트리밍 이벤트 순서가 뒤바뀌거나 누락되는 경우 테스트 추가
5. **배포 전 쿼리 검증**: 어휘 분석 요청 시 다양한 LLM 응답 형식 시뮬레이션

---

## 관련 문서

- [SPEC-VOCAB-003](./../specs/SPEC-VOCAB-003/spec.md) - 통합 스트리밍 아키텍처 명세
- [VOCAB-STREAMING-LESSONS](./../learning/VOCAB-STREAMING-LESSONS.md) - 상세 학습 가이드
