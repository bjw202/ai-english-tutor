# 배포 가이드: Vercel (프론트엔드) + Railway (백엔드)

> 이 가이드만 따라하면 AI English Tutor를 완전히 배포할 수 있습니다.
> 예상 소요 시간: **15~20분**

---

## 구조 한눈에 보기

```
[사용자 브라우저]
       ↓
[Vercel] Next.js 앱 (프론트엔드)
       ↓ API 요청
[Railway] FastAPI 앱 (백엔드)
       ↓
[OpenAI Vision / GPT-4o-mini]
```

---

## 배포 전 준비 체크리스트

- [ ] OpenAI API 키 보유 (https://platform.openai.com/api-keys)
- [ ] GitHub에 코드 push 완료
- [ ] Railway 계정 생성 (https://railway.app)
- [ ] Vercel 계정 생성 (https://vercel.com)

---

## 1단계: Railway — 백엔드 배포

### 1-1. Railway 프로젝트 생성

1. [railway.app](https://railway.app) 접속 → **New Project** 클릭
2. **Deploy from GitHub repo** 선택
3. 이 프로젝트 저장소를 선택

### 1-2. Root Directory 설정 ⚠️ 중요

Railway 프로젝트 생성 직후:

1. 생성된 서비스 클릭 → **Settings** 탭
2. **Source** 섹션에서 **Root Directory** 찾기
3. `backend` 입력 후 저장

> 이 설정이 없으면 배포가 실패합니다. 반드시 설정하세요.

### 1-3. 환경변수 설정

**Variables** 탭으로 이동 후 아래 변수를 추가합니다.

**필수 항목:**

| 변수명 | 값 | 설명 |
|--------|-----|------|
| `OPENAI_API_KEY` | `sk-proj-...` | OpenAI API 키 |

**선택 항목 (기본값으로 충분):**

| 변수명 | 기본값 | 설명 |
|--------|--------|------|
| `ENVIRONMENT` | `production` | 운영 환경 |
| `LOG_LEVEL` | `INFO` | 로그 레벨 |
| `CORS_ORIGINS` | *(2단계 후 설정)* | 허용된 프론트엔드 주소 |

> `PORT`는 Railway가 자동으로 설정합니다. 직접 설정하지 마세요.

### 1-4. 배포 확인

1. **Deployments** 탭에서 배포 로그 확인
2. 다음 메시지가 보이면 성공:
   ```
   INFO:     Application startup complete.
   INFO:     Uvicorn running on http://0.0.0.0:XXXX
   ```
3. **Settings → Networking → Generate Domain** 클릭
4. 생성된 URL 복사 (예: `https://ai-english-tutor-production.up.railway.app`)

> 이 URL을 2단계에서 사용합니다.

---

## 2단계: Vercel — 프론트엔드 배포

### 2-1. 프로젝트 Import

1. [vercel.com](https://vercel.com) → **Add New Project**
2. GitHub 저장소 선택
3. **Framework Preset**: `Next.js` (자동 감지됨)
4. **Root Directory**: `/` (프로젝트 루트 그대로)

### 2-2. 환경변수 설정

**Environment Variables** 섹션에서 추가:

| 변수명 | 값 |
|--------|-----|
| `BACKEND_URL` | Railway에서 복사한 URL (예: `https://ai-english-tutor-production.up.railway.app`) |

> 끝에 슬래시(`/`) 없이 입력하세요.

### 2-3. 배포

**Deploy** 버튼 클릭 → 완료 후 Vercel URL 복사

(예: `https://ai-english-tutor.vercel.app`)

---

## 3단계: CORS 설정 업데이트

백엔드가 프론트엔드 요청을 허용하도록 설정합니다.

1. Railway → 서비스 → **Variables** 탭
2. `CORS_ORIGINS` 변수 추가:
   ```
   https://ai-english-tutor.vercel.app
   ```
   (2단계에서 받은 실제 Vercel URL로 교체)
3. Railway가 자동으로 재배포됩니다 (1~2분 대기)

> 여러 도메인 허용 시 쉼표로 구분:
> `https://ai-english-tutor.vercel.app,https://custom-domain.com`

---

## 4단계: 동작 확인

### 백엔드 헬스체크

브라우저에서 접속:
```
https://[Railway URL]/docs
```
FastAPI Swagger UI가 보이면 정상입니다.

### 프론트엔드 확인

1. Vercel URL 접속
2. 이미지 업로드 또는 카메라 촬영 시도
3. 분석 결과가 스트리밍으로 표시되면 성공

---

## 문제 해결

### 배포 오류: `ModuleNotFoundError: No module named 'tutor'`

- **원인**: Root Directory가 `backend`로 설정되지 않음
- **해결**: Railway → Settings → Root Directory → `backend` 설정

### CORS 오류 (브라우저 콘솔에서 확인)

```
Access to fetch at 'https://...railway.app' from origin 'https://...vercel.app' has been blocked
```

- **원인**: `CORS_ORIGINS`에 Vercel URL이 없음
- **해결**: Railway 환경변수 `CORS_ORIGINS`에 Vercel URL 추가

### 백엔드 500 에러

- **원인**: `OPENAI_API_KEY` 미설정 또는 잘못된 키
- **해결**: Railway Variables에서 `OPENAI_API_KEY` 확인

### 이미지 업로드 후 응답 없음

- **원인**: `BACKEND_URL` 미설정 또는 잘못된 URL
- **해결**: Vercel → Settings → Environment Variables에서 `BACKEND_URL` 확인

---

## 환경변수 최종 정리

### Railway (백엔드)

```env
OPENAI_API_KEY=sk-proj-...          # 필수
ENVIRONMENT=production              # 선택 (기본: development)
LOG_LEVEL=INFO                      # 선택 (기본: INFO)
CORS_ORIGINS=https://your-app.vercel.app  # 3단계 후 설정
```

### Vercel (프론트엔드)

```env
BACKEND_URL=https://your-app.up.railway.app  # Railway URL
```

---

## 배포 후 유지보수

### 코드 업데이트

`main` 브랜치에 push하면 Vercel과 Railway 모두 **자동으로 재배포**됩니다.

### 비용 예상

| 서비스 | 플랜 | 월 비용 |
|--------|------|---------|
| Vercel | Hobby (무료) | $0 |
| Railway | Starter | $5 (사용량 기반) |
| OpenAI | 사용량 기반 | 이미지 100장 ≈ $0.004 |

---

*마지막 업데이트: 2026-02-23*
