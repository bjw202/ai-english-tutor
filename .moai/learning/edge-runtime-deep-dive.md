# Edge Runtime 심층 이해

## 핵심 요약

Edge Runtime은 전 세계 CDN 노드에서 V8 엔진만으로 코드를 실행하는 환경이다.
Web Streams API 기반으로 함수 종료와 스트림 전송을 분리하여 타임아웃 없이 스트리밍 가능.

---

## 1. 기존 Serverless vs Edge Runtime 비교

| 항목 | Node.js Runtime | Edge Runtime |
|------|----------------|--------------|
| 실행 환경 | V8 + Node.js (VM) | V8만 (CDN 노드) |
| 실행 위치 | 특정 데이터센터 | 사용자 인접 CDN |
| 콜드 스타트 | 100-500ms | 0-5ms |
| 스트리밍 타임아웃 | 60초 (Hobby) | 없음 |
| 메모리 제한 | 1GB | 128MB |
| 사용 가능 API | 전체 Node.js | Web API만 |

---

## 2. 스트리밍 타임아웃이 없는 원리

Edge Runtime은 `ReadableStream`을 반환하는 순간 함수 실행이 "종료"된다.
스트림 자체는 독립적으로 데이터를 흘려보낸다.

```typescript
// 함수는 여기서 즉시 종료
return new Response(
  new ReadableStream({
    async start(controller) {
      // 스트림은 독립적으로 계속 실행
      for await (const chunk of longRunningStream) {
        controller.enqueue(chunk);
      }
      controller.close();
    }
  })
);
```

---

## 3. 비용 모델 차이 (설계 철학)

- Serverless: VM이 살아있는 시간 = 비용 → 60초 타임아웃 필요
- Edge: CDN 노드는 24시간 상시 운영 → 스트리밍 여부가 추가 비용에 영향 없음

---

## 4. Edge Runtime 제약사항

사용 불가능한 것들:
- `node:` 모듈 전체 (`fs`, `path`, `crypto` 등)
- Node.js 전용 API
- 128MB 이상의 메모리 사용

사용 가능한 것들:
- `fetch`, `Request`, `Response`
- `ReadableStream`, `WritableStream`
- Web Crypto API
- `TextEncoder`, `TextDecoder`

---

## 5. 이 프로젝트에서의 적용 가능성

`src/app/api/tutor/analyze/route.ts`는 Railway 백엔드에 fetch로 SSE를 중계하는 역할이다.
Node.js 특화 API를 거의 사용하지 않으므로 Edge Runtime 전환 가능성이 높다.

전환 방법:
```typescript
export const runtime = 'edge';
// export const maxDuration = 60;  // 불필요 (Edge는 스트리밍 타임아웃 없음)
```

확인 필요 사항:
- import 하는 패키지의 Edge 호환 여부
- Request/Response 객체가 Web API 기반인지

---

## 체크리스트

- [ ] Edge Runtime의 실행 위치 이해 (CDN 노드)
- [ ] 함수 종료와 스트림 전송이 분리되는 원리 이해
- [ ] Node.js Runtime과 비용 모델 차이 이해
- [ ] 제약사항 (128MB 메모리, Web API만 사용) 인지
- [ ] 이 프로젝트 route.ts에 적용 가능 여부 판단

---

작성일: 2026-02-26
관련 버그: INCIDENT-002 (어휘 스트리밍 Vercel 60초 타임아웃)
