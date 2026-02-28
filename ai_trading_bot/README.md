# 🤖 AI 주식 자동매매 봇 (AI Trading Bot)

한국투자증권(KIS) API와 퀀트(Quant) 알고리즘을 결합하여 한국 주식을 분석하고, 텔레그램 메신저를 통해 모니터링할 수 있는 **반자동 트레이딩 봇**입니다.

이 프로젝트는 완전한 무인 자동매매를 지향하기보다는, **"데이터에 기반한 퀀트 분석 리포트를 텔레그램으로 받아보고, 깊은 전략은 AI 어시스턴트와 직접 상의한 뒤 매매를 결정하는 방식"**에 최적화되어 있습니다.

---

## ✨ 핵심 기능

1. **한국투자증권(KIS) API 연동**
   - 계좌 잔고 및 종목 현재가 조회
   - 과거 캔들(OHLCV) 차트 데이터 수집
   - 지정가 매수/매도 주문 실행
2. **퀀트(Quant) 보조지표 자동 분석**
   - 14일 RSI (상대강도지수) 과매수/과매도 분석
   - MACD 크로스오버 트렌드 분석
   - 20일 볼린저 밴드 상/하단 이탈 여부 탐지
3. **텔레그램(Telegram) 알림 봇 연동**
   - 설정된 시간에 퀀트 요약 리포트를 스마트폰으로 즉시 발송
   - 외부에서 확인 후 수동 매매 명령어 입력 대기

---

## 🛠️ 개발 환경 및 필수 라이브러리

- **Python 3.8+ 이상 권장**
- [requests](https://pypi.org/project/requests/): KIS API RESTful 통신용
- [pandas](https://pypi.org/project/pandas/): 수집된 금융 데이터의 프레임워크 조작
- [ta (Technical Analysis)](https://github.com/bukosabino/ta): RSI, MACD 등 퀀트 지표 계산
- [python-dotenv](https://pypi.org/project/python-dotenv/): 보안이 필요한 API 키 로드
- [python-telegram-bot](https://python-telegram-bot.org/): 텔레그램 메신저 통신
- *(참고)* `yfinance`: KIS API 키 연동 전, 모의 테스트를 위한 임시 주가 데이터 수집 라이브러리

---

## 🚀 시작하기 (Getting Started)

### 1단계: 저장소(Repository) 준비
1. 프로젝트를 클론하거나 폴더를 다운로드합니다.
2. `ai_trading_bot` 폴더 내부로 이동합니다.

### 2단계: 필수 패키지 설치
터미널을 열고 아래 명령어를 실행하여 필수 라이브러리를 설치합니다.
```bash
pip install -r requirements.txt
```

### 3단계: API 키 설정 (.env 파일)
API 키 유출을 방지하기 위해 환경 변수 파일을 사용합니다.

1. 프로젝트 최상위 폴더에 있는 `.env.example` 파일의 이름을 `.env`로 변경합니다.
2. 파일을 열어 각 항목에 본인의 발급받은 실제 키 값을 입력합니다.

#### 🔑 필수 발급 항목:
*   **한국투자증권 API 키**: KIS Developers(오픈 API) 사이트 가입 후 App Key, App Secret, 모의투자/실전투자 계좌번호 발급
*   **텔레그램 Bot Token**: 텔레그램 앱의 `BotFather`에게 봇 생성 요청 후 받은 Token, 그리고 본인의 사용자 Chat ID

> **주의**: `.env` 파일은 절대 Github 등 외부에 공개되거나 커밋되지 않도록 주의해야 합니다. (.gitignore 설정 필수)

### 4단계: 봇 실행
모든 설정이 끝났다면 메인 스크립트를 실행합니다.
```bash
python ai_trading_bot.py
```
실행 후 텔레그램으로 봇의 작동 확인 메시지와 분석 리포트가 수신되는지 확인합니다.

---

## 📂 프로젝트 파일 구조 (Architecture)

```text
ai_trading_bot/
├── ai_trading_bot.py      # 전체 봇의 실행 흐름을 제어하는 메인 엔진 (스케줄러 포함)
├── kis_api_client.py      # KIS 서버와 통신(토큰 갱신, 종목 가격, 매수/매도) 모듈
├── quant_analyzer.py      # 주가 데이터를 바탕으로 MACD, RSI 등을 계산하는 코어 분석기
├── requirements.txt       # 파이썬 의존성 패키지 리스트
└── .env (or .env.example) # 보안 키 관리 파일
```

---

## 🤝 사용 팁 (Workflow)
1. 외출 중이거나 장중(AM 9:00 ~ PM 3:30)에 텔레그램으로 전송되는 퀀트 리포트 알림을 확인합니다.
2. 기계적인 매매 지시가 필요할 경우, 텔레그램 봇 채팅창에서 `/buy 삼성전자 10` 같은 단축 명령어로 즉시 주문을 넘길 수 있습니다. (추후 연동 예정)
3. 복잡한 매매 결정과 포트폴리오 상담이 필요하다면, 리포트 텍스트를 복사하여 PC의 **Antigravity AI 대화창**에 붙여넣고 "이거 살까 팔까?" 상의하시면 완벽한 승률 전략을 세울 수 있습니다.

---

## 🔮 향후 고도화 계획 (Roadmap)
현재 시스템은 퀀트 수학 지표 기반의 자동 매매(옵션 A)로 작동하지만, 추후 **대형 언어 모델(LLM) 두뇌 탑재 (옵션 B)** 방향으로 업그레이드를 고려 중입니다.
* **[옵션 B] 생성형 AI (Gemini) 직접 탑재**: 매 5분마다 주식 데이터를 LLM 프롬프트로 전송하여, 단순 수치 계산을 넘어 시황과 정성적 맥락을 종합 판단한 뒤 LLM이 직접 매수/매도 지시(JSON 포맷 등)를 내리도록 하는 '초지능형 트레이더' 체제를 준비합니다.
