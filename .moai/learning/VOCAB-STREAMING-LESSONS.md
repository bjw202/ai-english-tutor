# 어휘 스트리밍 배포 학습 가이드

## 문서 정보

- **작성일**: 2026-02-26
- **관련 SPEC**: SPEC-VOCAB-003
- **기술 스택**: FastAPI, Next.js, Vercel, Railway, SSE 스트리밍
- **대상 독자**: 이 프로젝트의 현재 및 미래 개발자
- **목적**: 어휘 스트리밍 버그에서 얻은 교훈을 체계화하여 유사한 스트리밍 아키텍처 버그를 예방

---

## 섹션 1: 문제 요약

### 무엇이 잘못되었나

어휘 분석 스트리밍 기능이 프로덕션에서만 이상한 동작을 하였습니다. 사용자 관점에서는 분석 결과가 스트리밍 중에 화면에 표시되다가, 스트리밍이 완료되면 사라져버리는 현상이었습니다.

최종 사용자 경험:
1. 어휘 분석 시작 후 스트리밍 중 콘텐츠가 정상 표시됨
2. 스트리밍이 끝나면 (isStreaming = false 이벤트 수신)
3. 화면에 "아직 어휘 분석이 없습니다" 메시지 표시
4. 로컬에서는 완벽하게 동작함

### 아키텍처 차이: 로컬 vs 프로덕션

**로컬 환경**:
```
브라우저 → Next.js dev 서버 → FastAPI 백엔드 (직접 연결)
```
- 모든 SSE 이벤트가 순서대로 도착
- 지연이 최소화됨
- 프록시가 없어서 타임아웃 문제 없음

**프로덕션 환경**:
```
브라우저 → Vercel (Next.js 프록시) → Railway (FastAPI 백엔드)
```
- Vercel CDN/프록시가 SSE 스트림을 버퍼링
- 큰 청크는 일괄 전달, 작은 청크는 누적되어 일괄 전달
- 이벤트 순서가 뒤바뀔 가능성, 일부 이벤트가 누락될 가능성

이 구조적 차이가 로컬에서는 숨겨지고 프로덕션에서만 드러났습니다.

### 발견된 두 개의 버그

**Bug-1: 마크다운 정규화 함수의 h1 헤딩 미처리**

```python
# 문제: 정규식이 h3-h6만 매칭
pattern = r'^(#{3,6})\s+(.+)$'
```

LLM이 생성하는 마크다운의 헤딩 레벨이 비결정적입니다:
- 로컬에서는 `## word` (h2) 형식이 나옴
- 프로덕션에서는 `# word` (h1) 형식이 나옴 (때때로)

정규화 함수가 h1을 처리하지 못하면, 어휘 파싱 함수가 단어를 찾지 못하고 `words = []`가 됩니다.

**Bug-2: 프론트엔드 이벤트 누락 시 폴백 부재**

```typescript
// 문제: vocabulary_chunk 이벤트 미수신 → rawContent 무시
const handleVocabularyDone = (event: CustomEvent) => {
  const { words } = event.detail;
  if (!words?.length) {
    setVocabularyContent({
      structured: { words: [] },
      raw: '',  // rawContent 무시!
    });
  }
};
```

스트리밍 중에 rawContent에 원본 텍스트가 누적되지만, `vocabulary_chunk` 이벤트가 발송되지 않으면(Bug-1의 원인) `words = []`가 되고 rawContent까지 무시됩니다.

---

## 섹션 2: 왜 초반에 놓쳤는가?

### 이유 1: 로컬 아키텍처와 프로덕션 아키텍처의 근본적 차이

**핵심 문제**: 로컬 개발 환경에는 Vercel 프록시가 없습니다.

로컬에서:
- 백엔드 → 프론트엔드로 직접 연결
- SSE 스트림이 순서 변경 없이 도착
- 모든 이벤트가 누락되지 않음

프로덕션에서:
- 백엔드 → Vercel 프록시 → 브라우저
- Vercel의 프록시가 스트림을 버퍼링
- 이벤트 순서 변경 가능, 일부 이벤트가 누락될 수 있음

INCIDENT-001(이미지 분석)에서 이 문제를 이미 경험했는데, SPEC-VOCAB 개발 중에 이 교훈을 충분히 적용하지 않았습니다.

**교훈 미적용 지점**:
- INCIDENT-001: 프로덕션 환경에서만 SSE 타임아웃 발생 (Vercel 프록시의 idle timeout)
- SPEC-VOCAB-003: 같은 Vercel 프록시 환경인데, 프로덕션 테스트를 충분히 하지 않음

### 이유 2: LLM 비결정성(Non-determinism) 미처리

**핵심 문제**: LLM이 같은 프롬프트에 대해 다른 형식으로 응답할 수 있습니다.

어휘 분석 프롬프트 설계:
```
"다음 텍스트의 어휘를 분석하고 ## word_name 형식으로 작성하시오"
```

프롬프트에서 h2(`##`)를 지정했지만, LLM은:
- 로컬에서: 지정된 h2로 응답 (대부분의 경우)
- 프로덕션에서: 때때로 h1(`#`)로 응답 (토큰 샘플링의 다양성)

마크다운 정규화 함수는 h3-h6(`#{3,6}`)만 처리했으므로, h1이 나오면 아무것도 매칭되지 않습니다.

**LLM 비결정성의 원인**:
- Temperature 파라미터 > 0 (창의성)
- 다양한 학습 데이터로부터 학습한 여러 패턴
- 프롬프트 해석의 미묘한 차이
- 프로덕션 환경의 다양한 요청 패턴

### 이유 3: 침묵하는 실패 패턴 (Silent Failures)

**핵심 문제**: 예외가 발생하지 않고 조용히 실패합니다.

```python
# backend/src/tutor/routers/tutor.py
if data.get("words"):
    await queue.put({"type": "vocabulary_chunk", "data": {"words": data["words"]}})
# words가 없으면 아무도 모름 (로그 없음, 예외 없음)
```

프론트엔드는:
- `vocabulary_chunk` 이벤트를 기다림
- 이벤트가 오지 않으면 `words = []`로 간주
- 에러 메시지 없음

결과: 사용자가 보기에 "결과가 없다"는 인상만 줌

### 이유 4: 프론트엔드 이벤트 수신 실패 케이스 미테스트

**핵심 문제**: 행복한 경로(Happy path)만 테스트했습니다.

테스트 케이스가 누락된 부분:
```typescript
// 테스트됨: vocabulary_chunk + vocabulary_done 모두 수신
✓ test("스트리밍 중 단어 추출", ...)

// 테스트 누락: vocabulary_chunk 없이 vocabulary_done만 수신
✗ test("vocabulary_chunk 미수신 시 rawContent 폴백", ...)
```

스트리밍 아키텍처에서는 이벤트 순서나 누락을 대비한 방어적 설계가 필수인데, 단위 테스트에는 정상 경로만 포함되어 있었습니다.

### 이유 5: INCIDENT-001 교훈의 불완전한 적용

INCIDENT-001에서 배운 교훈:

```markdown
## Vercel 프록시 SSE 이슈 해결책
- Heartbeat를 5초 간격으로 발송 (idle timeout 방지)
- maxDuration을 명시적으로 설정 (execution timeout 방지)
```

그런데 SPEC-VOCAB-003 개발 시:
1. SSE 하트비트는 다른 엔드포인트에 추가했음
2. 어휘 분석 엔드포인트는 이미 하트비트가 있으므로 타임아웃 우려 없음
3. **But**: 타임아웃 외의 다른 Vercel 프록시 문제(이벤트 누락, 순서 변경)는 대비하지 않음

### 이유 6: 파싱 함수의 경계값 테스트 부족

마크다운 정규화 함수 주석:

```python
def _normalize_vocab_word_headings(content: str) -> str:
    """어휘 분석 결과에서 h3-h6 헤딩을 정규화합니다.

    주석: "잘못된 헤딩 레벨: h3-h6만 지원"
    """
    pattern = r'^(#{3,6})\s+(.+)$'
```

주석이 의도를 명시했지만, 질문이 부족했습니다:
- "왜 h3-h6만 선택했는가?"
- "h1, h2는 정말 나올 수 없는가?"
- "LLM 응답이 항상 이 형식을 따르는가?"

단위 테스트도:

```python
# 실제 테스트
def test_normalize_vocab_word_headings():
    # h3 헤딩만 테스트
    assert "## word" in normalize_vocab_word_headings("### word\n...")
    # h1, h2 케이스는 테스트 안 함
```

---

## 섹션 3: 핵심 교훈

### 교훈 1: 로컬과 프로덕션 아키텍처 차이 문서화

**원칙**: 서버리스/클라우드 환경에서는 아키텍처 차이를 명시적으로 이해하고 테스트하라.

프로덕션 환경에만 존재하는 요소:
- CDN/프록시 버퍼링으로 인한 이벤트 순서 변경 가능성
- idle timeout (연속 데이터 없을 때)
- 연결 체이닝 (브라우저 → 프록시 → 백엔드)
- 네트워크 지연과 패킷 손실

이를 대비하는 설계:
```
✓ SSE 하트비트 추가 (idle timeout 방지)
✓ 이벤트 누락 시 폴백 추가 (버퍼링 대비)
✓ 이벤트 순서 무관한 설계 (비순차 도착 대비)
✓ 프로덕션 환경 테스트 (로컬과 동일한 환경에서 테스트)
```

### 교훈 2: LLM 비결정성은 서비스 시작부터 고려하라

**원칙**: LLM이 생성하는 출력은 항상 변할 수 있다고 가정하라.

마크다운 파싱의 경우:

```python
# 안 좋은 예: 하나의 형식만 가정
pattern = r'^(#{3,6})\s+(.+)$'  # h3-h6만

# 좋은 예: 모든 가능한 형식 대비
pattern = r'^(#{1,6})\s+(.+)$'  # h1-h6 모두
```

LLM 응답 파서 설계 원칙:
1. **관대한 파싱**: 유연한 정규식으로 여러 형식 수용
2. **폴백**: 정상 파싱 실패 시 원본 텍스트 사용
3. **에러 로깅**: 예상과 다른 형식 발견 시 로그 기록
4. **점진적 개선**: 로그 분석으로 실제 LLM 출력 패턴 파악 후 최적화

### 교훈 3: 침묵하는 실패를 방지하라

**원칙**: 조용한 실패(silent failure)보다는 명시적 에러가 낫다.

현재 코드:
```python
# 나쁜 예: 무조건 발송 (단어가 없으면 조용히 실패)
if data.get("words"):
    await queue.put({"type": "vocabulary_chunk", ...})
```

개선 코드:
```python
# 좋은 예: 명시적 로깅
words = data.get("words", [])
if words:
    await queue.put({"type": "vocabulary_chunk", ...})
else:
    logger.warning(f"No vocabulary words parsed from content, raw: {content[:100]}")
    # 또는
    await queue.put({"type": "vocabulary_parsing_failed", "raw_content": content})
```

### 교훈 4: 스트리밍 아키텍처에서는 모든 이벤트를 선택적으로 처리하라

**원칙**: 스트리밍 이벤트가 누락될 수 있다고 가정하고 폴백을 준비하라.

스트리밍 이벤트 설계:

```typescript
// 정상 흐름 (모든 이벤트 도착)
raw_chunk → raw_chunk → vocabulary_chunk → vocabulary_chunk → vocabulary_done

// 가능한 문제 상황
raw_chunk → vocabulary_done (vocabulary_chunk 누락!)
raw_chunk → raw_chunk → vocabulary_done (chunk 누락!)
```

폴백 설계:

```typescript
const handleVocabularyDone = (event: CustomEvent) => {
  const { words, isStreaming } = event.detail;

  if (words && words.length > 0) {
    // 정상: 파싱된 단어 사용
    setVocabularyContent({ structured: { words }, raw: rawContent });
  } else if (rawContent.trim()) {
    // 폴백: 파싱 실패 시 원본 텍스트 표시
    setVocabularyContent({ structured: { words: [] }, raw: rawContent });
  } else {
    // 최후의 수단: 비어있음
    setVocabularyContent({ structured: { words: [] }, raw: '' });
  }
};
```

### 교훈 5: INCIDENT 교훈을 체계화하고 재적용 메커니즘을 만들어라

**원칙**: 과거의 실수를 반복하지 않으려면 체계적인 검토 프로세스가 필요하다.

현재 상황:
- INCIDENT-001: "프로덕션 SSE 문제" 해결
- SPEC-VOCAB-003: 같은 환경에서 같은 유형의 문제 발생

근본 원인: 새 SPEC 개발 시 과거 인시던트 교훈을 자동으로 적용하는 메커니즘 부재

개선 방안:

```markdown
## 배포 전 체크리스트: 스트리밍 기능 (INCIDENT-001, 002 기반)

### 아키텍처 검토
- [ ] 로컬과 프로덕션 환경의 네트워크 경로 다이어그램 확인
- [ ] Vercel 프록시의 영향 범위 파악
- [ ] SSE 이벤트 순서가 변경될 수 있음을 명시

### LLM 출력 파싱
- [ ] LLM 응답이 다양한 형식으로 나올 수 있음을 가정
- [ ] 마크다운 헤딩 h1-h6 모두 테스트
- [ ] 파싱 실패 시 폴백 준비

### 스트리밍 이벤트
- [ ] 각 이벤트가 누락될 수 있음을 가정
- [ ] 원본 데이터(rawContent)에 폴백 준비
- [ ] 침묵하는 실패에 대한 로깅 추가

### 테스트
- [ ] 정상 경로 테스트 (행복한 경로)
- [ ] 이벤트 누락 시나리오 테스트
- [ ] 이벤트 순서 변경 시나리오 테스트
```

### 교훈 6: 경계값 테스트와 설계 리뷰

**원칙**: 파싱, 정규화, 상태 관리 함수는 모든 가능한 입력을 테스트하라.

마크다운 정규화 함수 테스트:

```python
def test_normalize_vocab_word_headings_all_levels():
    """h1부터 h6까지 모든 헤딩 레벨 테스트"""
    for level in range(1, 7):
        heading = "#" * level + " word"
        content = f"{heading}\n어휘 설명"
        result = _normalize_vocab_word_headings(content)
        assert "##" in result or level >= 2  # 최소 h2로 정규화
```

---

## 섹션 4: 재발방지 체크리스트

### 스트리밍 기능 배포 전 필수 검사

**아키텍처 확인**

- [ ] 로컬 개발 환경과 프로덕션 환경의 네트워크 경로 명시
- [ ] 프록시, CDN 등 중간 계층의 SSE 처리 방식 이해
- [ ] Vercel 문서의 "Long-running serverless functions" 섹션 검토
- [ ] 타임아웃 설정 (maxDuration, idle timeout, connection timeout)

**LLM 출력 파싱**

- [ ] LLM 응답이 생성할 수 있는 모든 형식 나열
- [ ] 마크다운 파싱: h1-h6 모든 헤딩 레벨 테스트
- [ ] JSON 파싱: 선택적 필드, 빈 배열, null 값 테스트
- [ ] 파싱 실패 시 대체 전략 준비 (원본 텍스트 사용 등)
- [ ] 파싱 규칙을 주석으로 문서화 (왜 이 범위인가)

**스트리밍 이벤트 설계**

- [ ] 각 이벤트가 필수인지 선택적인지 명시
- [ ] 이벤트 누락 시나리오에 대한 폴백 정의
- [ ] 이벤트 순서 변경에 대한 영향 분석
- [ ] 침묵하는 실패에 대한 로깅 (경고 레벨 이상)

**프론트엔드 상태 관리**

- [ ] rawContent와 structured 데이터 둘 다 유지
- [ ] structured 데이터 이벤트 미수신 시 rawContent로 폴백
- [ ] 이벤트 순서 무관한 상태 관리
- [ ] 타임아웃 시나리오 처리

**테스트**

- [ ] 정상 경로 통합 테스트 (모든 이벤트 도착)
- [ ] 비정상 경로 테스트 (이벤트 누락, 순서 변경)
- [ ] LLM 응답 다양성 테스트 (여러 형식의 입력)
- [ ] 프로덕션 환경에서의 테스트 (로컬과 동일한 네트워크 경로 재현)

**배포**

- [ ] 스테이징 환경에서 프로덕션과 동일한 네트워크 설정으로 테스트
- [ ] 배포 직후 모니터링 강화 (에러 로그, 스트리밍 성공률 추적)
- [ ] 이벤트 누락/순서 변경 감지 알림 설정
- [ ] 롤백 계획 수립

---

## 섹션 5: 패턴 라이브러리 - 미래 프로젝트를 위한 방어 패턴

### 패턴 1: 관대한 마크다운 파싱

```python
def parse_markdown_flexible(content: str, min_heading_level: int = 1, max_heading_level: int = 6):
    """
    모든 헤딩 레벨을 수용하는 관대한 마크다운 파서.

    LLM이 생성하는 마크다운은 예측할 수 없으므로,
    최소~최대 헤딩 레벨 범위를 설정하여 유연성 확보.
    """
    pattern = rf'^(#{{{min_heading_level},{max_heading_level}}})\s+(.+)$'
    matches = re.findall(pattern, content, re.MULTILINE)
    return [{"level": len(m[0]), "text": m[1]} for m in matches]

# 사용 예시
# 어휘: h1-h6 모두 수용
words = parse_markdown_flexible(content, min_heading_level=1, max_heading_level=6)

# 섹션: h2-h4만 수용 (h1은 제목, h5-h6은 잡음)
sections = parse_markdown_flexible(content, min_heading_level=2, max_heading_level=4)
```

### 패턴 2: 다층 폴백 전략

```typescript
// 스트리밍 데이터 수신 시
const handleStreamData = (event: StreamEvent) => {
  if (event.type === "structured_data") {
    // 레벨 1: 파싱된 구조화된 데이터 (최우선)
    setStructuredData(event.data);
    setFallbackLevel(0);
  } else if (event.type === "raw_content") {
    // 레벨 2: 원본 데이터 누적
    rawContent += event.data;
    if (structuredData.length === 0) {
      setFallbackLevel(1);  // 현재 이 레벨로 표시 중
    }
  }
};

// 스트리밍 완료 시
const handleStreamComplete = () => {
  if (structuredData.length > 0) {
    // 레벨 1 폴백: 파싱된 데이터 사용
    display(structuredData);
  } else if (rawContent.trim().length > 0) {
    // 레벨 2 폴백: 원본 데이터 사용
    display(rawContent);
  } else {
    // 레벨 3 폴백: 비어있음
    display("데이터 없음");
  }
};
```

### 패턴 3: 이벤트 누락 감지 및 로깅

```python
import logging
import asyncio

logger = logging.getLogger(__name__)

class EventMonitor:
    """스트리밍 이벤트가 예상대로 도착하는지 모니터링"""

    def __init__(self):
        self.expected_events = {
            "raw_chunk": 0,
            "structured_chunk": 0,
            "stream_done": False,
        }
        self.received_events = {k: 0 for k in self.expected_events}

    async def on_event(self, event_type: str):
        self.received_events[event_type] += 1

    async def on_complete(self):
        """스트리밍 완료 후 누락된 이벤트 분석"""
        if self.received_events["structured_chunk"] == 0 and self.received_events["raw_chunk"] > 0:
            logger.warning(
                "No structured_chunk received despite raw_chunk. "
                f"This indicates parsing failure. raw_chunk count: {self.received_events['raw_chunk']}"
            )

        if self.received_events["raw_chunk"] > 0 and self.received_events["structured_chunk"] == 0:
            logger.info("Fallback to raw content because structured data is missing")

# 사용
monitor = EventMonitor()
async for event in stream:
    await monitor.on_event(event.type)
await monitor.on_complete()
```

### 패턴 4: 프로덕션 환경 SSE 테스트

```bash
# Vercel 프록시를 거친 실제 SSE 스트림 테스트
# 로컬 환경에서는 이 테스트를 건너뜀

curl -N "https://your-app.vercel.app/api/stream" \
  -H "Authorization: Bearer $TEST_TOKEN" \
  --show-error \
  --verbose

# 예상되는 이벤트 순서와 실제 도착 순서 비교
# - 타임스탬프 확인
# - 이벤트 순서 변경 여부 확인
# - 이벤트 누락 여부 확인
```

### 패턴 5: 프론트엔드 에러 바운더리

```typescript
// React Error Boundary로 스트리밍 오류 캡처
<ErrorBoundary
  fallback={<div>어휘 분석 중 오류 발생</div>}
  onError={(error) => {
    logger.error("Vocabulary streaming error", {
      error: error.message,
      fallback_level: fallbackLevel,
      raw_content_length: rawContent.length,
      structured_data_count: structuredData.length,
    });
  }}
>
  <VocabularyPanel />
</ErrorBoundary>
```

### 패턴 6: 배포 후 모니터링 대시보드

```python
# 모니터링할 메트릭
metrics = {
    "streaming_events_total": Counter(
        "Count of all streaming events",
        ["event_type", "endpoint"]
    ),
    "streaming_events_missing": Counter(
        "Count of missing expected events",
        ["event_type", "endpoint"]
    ),
    "parsing_failures": Counter(
        "Count of LLM output parsing failures",
        ["content_type"]
    ),
    "fallback_usage": Counter(
        "Count of times fallback strategy was used",
        ["fallback_level"]
    ),
}

# 대시보드 쿼리
"""
- Streaming events by type over time
- Missing events rate
- Parsing failure rate
- Fallback usage pattern
- Correlation between events and failures
"""
```

---

## 섹션 6: INCIDENT-001과의 비교

### 유사점

| 특성 | INCIDENT-001 (이미지) | INCIDENT-002 (어휘) |
|------|-------|-------|
| **발생 환경** | 프로덕션만 | 프로덕션만 |
| **로컬 환경** | 정상 동작 | 정상 동작 |
| **근본 원인** | 프록시 타임아웃 | 프록시 버퍼링 + LLM 비결정성 |
| **SSE 관련** | Yes (idle timeout) | Yes (이벤트 누락) |
| **Vercel 환경** | Yes | Yes |
| **해결 방법** | heartbeat 추가 | 정규식 확장 + 폴백 추가 |

### 차이점

| 특성 | INCIDENT-001 | INCIDENT-002 |
|------|-------|-------|
| **감지 난이도** | 쉬움 (명시적 타임아웃 오류) | 어려움 (조용한 실패) |
| **근본 원인 수** | 4개 (복잡) | 2개 (단순) |
| **수정 난이도** | 높음 (여러 파일) | 낮음 (2개 파일) |
| **LLM 관련** | No | Yes (응답 형식 불일치) |

### 교훈 적용의 격차

INCIDENT-001 후:
- ✓ SSE 하트비트 추가됨
- ✓ maxDuration 설정됨
- ✗ **"프록시의 다른 문제(이벤트 누락)는 대비하지 않음"**

SPEC-VOCAB-003 개발:
- ✓ 하트비트 상속됨
- ✓ 명시적 테스트는 정상 경로만
- ✗ **"이벤트 누락 시나리오 테스트 없음"**
- ✗ **"LLM 응답 다양성 고려 부족"**

---

## 요약: 핵심 원칙 6가지

1. **아키텍처 차이 문서화**: 로컬과 프로덕션의 네트워크 경로가 다르면 특별한 처리가 필요하다

2. **LLM 비결정성 수용**: LLM 응답은 항상 변할 수 있다. 여러 형식에 대응하는 관대한 파싱을 설계하라

3. **침묵하는 실패 방지**: 예외 없는 실패보다는 명시적 로깅과 폴백이 중요하다

4. **스트리밍 이벤트 무관성**: 프록시 버퍼링으로 인해 이벤트가 누락되거나 순서가 뒤바뀔 수 있다고 가정하고 폴백을 준비하라

5. **과거 교훈 재적용**: INCIDENT 기반 체크리스트를 새 SPEC 개발에 자동으로 적용하는 프로세스 필요

6. **경계값 테스트**: 파싱, 정규화 함수는 모든 가능한 입력으로 테스트하고 함수 주석에 범위를 명시하라

---

## 관련 문서

- [DEPLOYMENT-INCIDENTS.md](./../docs/DEPLOYMENT-INCIDENTS.md) - INCIDENT-002 상세 기록
- [SPEC-VOCAB-003](./../specs/SPEC-VOCAB-003/spec.md) - 통합 스트리밍 아키텍처 명세
- [IMAGE-ANALYSIS-DEPLOYMENT-LEARNINGS](./../learning/IMAGE-ANALYSIS-DEPLOYMENT-LEARNINGS.md) - INCIDENT-001 상세 학습 가이드
