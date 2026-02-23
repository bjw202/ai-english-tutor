# 배포 비용 분석 (2026-02-23 조사)

배포 전 검토용 자료. 1인 사용 기준, 월 약 100건 요청 시나리오.

---

## API 비용 (OpenAI gpt-4o-mini)

### 모델 변경 전 → 후 비교

| 항목 | 변경 전 | 변경 후 |
|------|--------|--------|
| Supervisor | claude-haiku-4-5 | gpt-4o-mini |
| Grammar | gpt-4o | gpt-4o-mini |
| Reading | claude-sonnet-4-5 | gpt-4o-mini |
| Vocabulary | claude-sonnet-4-5 | gpt-4o-mini |

### 월별 API 비용 (gpt-4o-mini: $0.15/M input, $0.60/M output)

| 요청 수 | Input 토큰 | Output 토큰 | 월 비용 |
|--------|-----------|-----------|--------|
| 100건 | 590K | 1,030K | **~$0.71** |
| 1,000건 | 5.9M | 10.3M | **~$7.08** |
| 10,000건 | 59M | 103M | **~$70.8** |

> **SPEC-MODEL-001 결과**: 변경 전 대비 95.4% 절감 (1,000건 기준 $152.90 → $7.08)

---

## 프론트엔드: Vercel

- **비용**: $0 (Hobby 플랜 무료)
- **제약**: 상업적 대규모 서비스 시 Pro 플랜($20/월) 필요
- **결론**: 1인 개인 사용 → 무료로 충분

---

## 백엔드 호스팅 옵션 비교

### 무료 옵션

| 서비스 | 무료 스펙 | Cold Start | 추천도 | 비고 |
|--------|----------|-----------|-------|------|
| **Koyeb** | 512MB RAM, 0.1 vCPU, 2GB SSD | 2~5초 | ⭐⭐⭐⭐⭐ | 영구 무료, Scale-to-Zero |
| **Google Cloud Run** | 2M req/월, 180K vCPU-초/월 | 5~15초 | ⭐⭐⭐⭐ | 서버리스, 무거운 라이브러리로 느림 |
| **Render** | 512MB RAM | 30~60초 | ⭐⭐⭐ | 15분 미사용 시 강제 Sleep |
| Railway | ❌ 없음 | - | - | 최소 $5/월 |
| Fly.io | ❌ 없음 | - | - | 무료 티어 종료됨 |

### 유료 옵션

| 서비스 | 플랜 | 월 비용 | 스펙 |
|--------|------|--------|------|
| Railway Hobby | $5/월 기본 + 사용량 | ~$5~10 | 48GB RAM 한도, 사용량 과금 |
| Railway Pro | $20/월 기본 + 사용량 | ~$20+ | 1TB RAM 한도 |

#### Railway 사용량 단가

- RAM: $10/GB/월
- CPU: $20/vCPU/월
- 네트워크 송신: $0.05/GB

#### 이 스택 예상 리소스 사용 (FastAPI + LangGraph + langchain)

| 리소스 | 예상치 | 비고 |
|--------|-------|------|
| RAM | 400~512MB | Python + LangGraph 라이브러리 |
| CPU (평균) | 0.05~0.1 vCPU | 대부분 OpenAI API 대기 |
| 네트워크 | ~5MB/월 | 100건 × 50KB SSE |

---

## 추천 배포 전략 (1인 사용)

### 1순위: Koyeb 무료 + Vercel 무료

```
총 비용: $0/월 + OpenAI API $0.71/월 ≈ 월 ₩1,000
```

- 512MB RAM 제한 주의 → 배포 전 메모리 사용량 확인 필요
- Scale-to-Zero: 미사용 시 절전, 첫 요청 시 2~5초 콜드스타트
- 개인 사용이므로 콜드스타트 감수 가능

**배포 전 메모리 확인 방법:**
```bash
cd backend
docker stats  # 또는 실제 배포 후 Koyeb 대시보드에서 확인
```

### 2순위: Google Cloud Run + Vercel 무료

```
총 비용: $0/월 + OpenAI API $0.71/월 ≈ 월 ₩1,000
```

- 100건/월은 무료 할당량(2M req/월) 내 완전 무료
- Python 라이브러리가 무거워 콜드스타트 5~15초 예상
- Docker 컨테이너 빌드 설정 필요

### 3순위: Railway Hobby + Vercel 무료 (유료지만 안정적)

```
총 비용: ~$5~7/월 + OpenAI API $0.71/월 ≈ 월 ₩10,000
```

- 상시 실행, 콜드스타트 없음
- 트래픽이 늘어도 안정적으로 확장 가능

---

## 결론

| 시나리오 | 호스팅 | API | 월 합계 |
|---------|--------|-----|--------|
| 무료 최적 | Koyeb (무료) | ~$0.71 | **~₩1,000** |
| 유료 안정 | Railway Hobby | ~$0.71 | **~₩10,000** |
| 트래픽 증가 시 | Railway Pro | 비례 증가 | **~₩30,000+** |

**개인 1인 사용**: Koyeb 무료 플랜으로 시작, 문제 발생 시 Railway Hobby로 전환

---

## 참고 링크

- [Koyeb 요금제](https://www.koyeb.com/pricing)
- [Koyeb FastAPI 배포 가이드](https://www.koyeb.com/docs/deploy/fastapi)
- [Google Cloud Run 요금](https://cloud.google.com/run/pricing)
- [Railway 요금제](https://docs.railway.com/reference/pricing/plans)
- [Vercel Hobby 플랜](https://vercel.com/pricing)
