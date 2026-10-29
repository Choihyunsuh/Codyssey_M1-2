# USD/KRW AI 비서

USD/KRW 일별 환율을 Firestore에 저장하고, 요약을 바탕으로 질문에 답하는 개인 데이터 비서입니다. 환율은 **1 USD당 KRW**입니다. 값이 오르면 달러 강세/원화 약세, 내리면 달러 약세/원화 강세로 해석합니다.

## 기술 스택
- Python 3.10+, FastAPI, Pydantic, Firebase Admin/Firestore, OpenAI API
- HTML/CSS/Vanilla JavaScript
- Render (API), Vercel (정적 프론트엔드)

## 포함된 기능
- 환율 레코드 CRUD와 기간/개수/평균/최고/최저/최근값/변화율 요약
- 데이터 요약을 시스템 메시지에 넣는 AI 채팅과 대화 자동 저장
- 대화 목록, 특정 대화 불러오기, 대화 삭제 API
- Swagger UI: `/docs`

## 데이터
`data/usd_krw_2025.csv`는 FRED 시계열 DEXKOUS의 2025년 관측값입니다. 유효 거래일 250건이며 점(.) 결측값은 제외했습니다. FRED 수치는 USD 1달러당 원화 환율입니다.
출처: [FRED DEXKOUS](https://fred.stlouisfed.org/data/DEXKOUS)

## 로컬 실행
1. Python 3.10 이상을 준비하고 가상환경을 만든 뒤 `pip install -r requirements.txt`를 실행합니다.
2. `.env.example`을 참고해 환경변수를 설정합니다. Firebase 서비스 계정 JSON은 한 줄 JSON 문자열로 `FIREBASE_SERVICE_ACCOUNT_JSON`에 넣습니다.
3. Firebase Console에서 Firestore를 생성합니다.
4. 저장소 루트에서 `python backend/seed_data.py`를 실행해 CSV 250건을 Firestore의 `data` 컬렉션에 가져옵니다.
5. `uvicorn backend.main:app --reload`로 API를 실행하고 `http://localhost:8000/docs`에서 확인합니다.
6. 정적 서버로 `frontend/`를 제공합니다. API 주소는 `frontend/config.js`의 `window.API_BASE_URL`에 설정합니다. 로컬에서는 기본 `http://localhost:8000`입니다.

## 환경 변수
- `OPENAI_API_KEY`: OpenAI API 키
- `FIREBASE_SERVICE_ACCOUNT_JSON`: Firebase 서비스 계정 JSON 문자열
- `ALLOWED_ORIGINS`: 허용 프론트엔드 origin 목록(쉼표 구분)
- `OPENAI_MODEL`: 선택 사항, 기본 `gpt-4o-mini`
- 프론트엔드 API 주소: `frontend/config.js`의 `window.API_BASE_URL`

키 파일은 저장소에 커밋하지 마세요. `.env.example`에는 실제 비밀값을 넣지 않습니다.

## 배포
### Render
저장소를 연결하고 `render.yaml`의 Blueprint 설정을 사용합니다. 위 환경 변수를 Render 서비스에 설정하고 `ALLOWED_ORIGINS`에 Vercel 도메인을 넣습니다. `https://<render-host>/docs`에서 Swagger를 확인합니다. 무료 인스턴스는 유휴 후 첫 요청에 지연이 있을 수 있습니다.

### Vercel
Vercel 프로젝트의 Root Directory를 `frontend`로 지정해 정적 사이트로 배포합니다. 배포 전에 `frontend/config.js`의 API 주소를 Render 서비스 URL로 바꿉니다. 배포 URL은 실제 배포 후 이 README에 기록하세요.

## 제출 스크린샷
배포 후 아래 화면을 캡처해 저장소 또는 제출 문서에 첨부하세요.
- 데이터 요약과 질문/답변이 보이는 채팅
- 데이터 추가 또는 삭제 동작
- 이전 대화 선택 후 메시지 불러오기

## API 개요
- `POST/GET /api/data`, `PUT/DELETE /api/data/{id}`, `GET /api/data/summary`
- `POST/GET /api/conversations`, `GET/DELETE /api/conversations/{id}`
- `POST /api/chat`
