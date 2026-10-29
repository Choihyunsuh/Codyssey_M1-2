# USD/KRW AI 비서

USD/KRW 일별 환율을 Firestore에 저장하고, 데이터 요약을 바탕으로 질문에 답하는 AI 비서입니다.

## 현재 상태

프로젝트 초기 구성 중입니다. 환율 데이터는 FRED 시계열 `DEXKOUS`에서 가져옵니다. 이 시리즈는 미국 달러 1달러당 원화 환율(KRW per USD)을 나타냅니다.

## 데이터

`data/usd_krw_2025.csv`에는 2025년 거래일 기준 250개의 유효한 관측값이 있습니다. `.` 결측값은 제외했습니다.

## 기술 스택

- FastAPI, Firebase Firestore, OpenAI API
- HTML, CSS, Vanilla JavaScript
- Render (API), Vercel (정적 웹)

## 환경 변수

- `OPENAI_API_KEY`
- `FIREBASE_SERVICE_ACCOUNT_JSON` (서비스 계정 JSON 문자열)
- `ALLOWED_ORIGINS` (쉼표로 구분한 허용 origin 목록)
- 프론트엔드 `API_BASE_URL`

## 데이터 출처

[FRED DEXKOUS](https://fred.stlouisfed.org/data/DEXKOUS)
