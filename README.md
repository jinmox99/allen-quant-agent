# ⚡ Allen Quant Agent

> **미국 3배 레버리지 ETF 퀀트 백테스터 & 한국 자산 실시간 AI 투자 브리핑 에이전트**
>
> 이 솔루션은 미국 시장의 대표적인 고변동성 3배 레버리지 ETF(TQQQ, SOXL, TECL, UPRO)에 대한 고도화된 퀀트 전략 백테스팅 엔진과, 한국 주요 ETF/ETN 자산의 실시간 시세 트래킹 및 Google Gemini LLM 기반의 AI 투자 전략 브리핑을 제공하는 통합 퀀트 솔루션입니다.

---

## 🌟 핵심 기능 (Key Features)

### 1. 📈 실시간 자산 모니터링 (Market Tracker)
* **📊 글로벌 퀀트 자산 실시간 전광판 (Unified Overview Dashboard):** 한 화면에서 미국 및 한국 시장의 8대 핵심 자산 시세 및 변동률을 한눈에 실시간 그리드로 확인 가능한 모니터링 대시보드.
* **✨ 인터랙티브 포커싱 및 렌더링:** 현재 선택된 종목은 네온 스카이블루 외곽선과 카드 배경 그라디언트로 강조되며, 각 카드의 `상세 분석 보기` 클릭 시 즉시 하단의 주가 및 오실레이터 차트 데이터가 갱신.
* **동적 가격 분석 차트:** Plotly 서브플롯을 적용하여 캔들스틱 가격 차트, 10일/25일/45일 이동평균선(SMA), 거래량 지표를 동적으로 렌더링.
* **기술적 퀀트 모멘텀 지표:** RSI(14), MACD 오실레이터, 25일 평균 괴리도, 볼린저 밴드 너비를 분석해 과매수/과매도 구간 및 추세 상회/하회 상태를 실시간 배지로 출력.

### 2. 🚀 미국 레버리지 ETF 퀀트 백테스터 (US Quant Backtester)
* **3배 레버리지 ETF 전용:** SOXL, TECL, TQQQ, UPRO 대상 백테스팅 제공.
* **전략 시뮬레이터:**
  * **SMA Crossover:** 단기/장기 이동평균선 교차 전략.
  * **RSI Momentum:** 과매도 구간 매수, 과매수 구간 매도 전략.
  * **Combined Strategy:** RSI 과매도/과매수 필터와 SMA 골든/데드크로스를 결합한 하이브리드 전략.
* **정밀한 성과 측정:** 최종 자산, 누적 수익률(vs 단순 보유 벤치마크), 연평균 수익률(CAGR), MDD(최대 낙폭), Sharpe Ratio, 승률(Win Rate) 및 총 거래 횟수 자동 산출.
* **차트 및 로그 브리핑:** 누적 수익률 곡선과 Drawdown 낙폭 차트 실시간 시각화 및 상세 거래 이력(거래일, 매매종류, 거래량, 체결가, 수수료, 거래대금, 잔고) 표 제공.

### 3. 🤖 AI 포트폴리오 브리핑 에이전트 (AI Trading Broker)
* **Gemini 기반 심층 추론:** Google Gemini API를 활용하여 퀀트 기술 지표와 시장 환경을 입체적으로 추론하여 맞춤 브리핑 작성.
* **뉴스 감성 필터링 (Sentiment Analysis):** 미국 종목의 실시간 야후 파이낸스 뉴스 피드를 수집하여 긍정/부정/중립 감성을 평가하고 통합 감성 모멘텀 스코어 산정.
* **종합 의사결정 리포트:** 최종 투자 의견(매수/매도/관망), 감성 분석 스코어 정보와 함께 리스크 관리를 포함한 심층 마크다운 리포트 실시간 자동 발행.

### 4. 🧮 퀀트 수학적 모델 및 성능 최적화 (Advanced Scoring & Performance)
* **비선형 스무딩 수학 모델 (`math.tanh`):** 지표의 극단적인 이상치(Outlier)로 인한 점수 왜곡(혼조세 상태임에도 100점 만점이 산출되는 현상 등)을 방지하기 위해 Hyperbolic Tangent(`math.tanh`) 함수를 스케일링 엔진에 전면 도입.
* **통계적 정규화 (Z-Score):** 각 종목별/지표별 변동폭을 보정하기 위해 과거 50일간의 표준편차를 활용한 Z-Score 정규화 기법을 적용, 0~100점의 스코어가 시장 상황(강세/횡보/약세)에 완벽하게 바인딩되어 계산됨.
* **동적 캐시 키 바스터 (Dynamic Cache Key Buster):** `Streamlit`의 `@st.cache_data`와 시장(KR/US) 개장 시간을 동기화하여 장중에는 `5분` 단위 최신화, 장 마감 이후에는 `1시간` 단위 캐싱을 동적으로 전환 적용. (불필요한 API 호출 방지 및 로딩 속도 0.01초 최적화 달성)

---

## 📂 프로젝트 구조 (Architecture)

```text
c:\dev\quant
├── .env                  # 환경 변수 정의 (Gemini API Key 등)
├── main.py               # Streamlit 메인 대시보드 웹 애플리케이션
├── requirements.txt      # 프로젝트 의존성 라이브러리 목록
└── src/                  # 내부 비즈니스 로직 및 코어 모듈
    ├── __init__.py
    ├── agent/            # AI 브리핑 에이전트 레이어
    │   ├── __init__.py
    │   └── orchestrator.py  # Gemini API 연동 및 종합 리포트 생성
    ├── analyzers/        # 퀀트 분석 및 데이터 가공 레이어
    │   ├── __init__.py
    │   ├── indicators.py    # 기술적 모멘텀 지표 (RSI, MACD, Bollinger Bands 등) 계산
    │   └── sentiment.py     # 뉴스 기사 텍스트 감성 분석 (Gemini LLM 연동)
    ├── backtester/       # 퀀트 시뮬레이션 백테스팅 레이어
    │   ├── __init__.py
    │   └── engine.py        # 포트폴리오 백테스팅 코어 엔진 및 성과 지표 산출
    └── data_loader/      # 금융 시장 데이터 적재 레이어
        ├── __init__.py
        ├── kr_loader.py     # 한국 ETF/ETN 시세 데이터 적재 (FinanceDataReader)
        └── us_loader.py     # 미국 주식 시세 데이터 및 실시간 뉴스 수집 (yfinance)
```

---

## 🛠️ 개발 환경 설정 및 설치 가이드 (Setup)

### 1. 환경 변수 설정 (`.env`)
프로젝트 루트 디렉토리에 `.env` 파일을 생성하거나 기존 파일을 확인하여 다음과 같이 Google Gemini API 키를 설정합니다.
```env
GEMINI_API_KEY=your_google_gemini_api_key_here
```

### 2. 가상 환경 생성 및 의존성 설치 (`uv` 기반)
이 프로젝트는 파이썬 초고속 프로젝트/패키지 관리 도구인 **`uv`**를 기반으로 관리됩니다.

```powershell
# 1. 가상 환경 생성 (이미 존재하는 경우 생략 가능)
uv venv

# 2. requirements.txt 파일에 명시된 패키지들을 가상 환경에 초고속 설치
uv pip install -r requirements.txt
```

---

## 🚀 실행 방법 (How to Run)

`uv`를 사용하면 번거롭게 가상 환경 활성화(Activate) 절차를 거치지 않고도 **`uv run`** 명령어를 통해 바로 가상 환경 내 패키지를 활용해 실행할 수 있습니다.

### 1. 전체 웹 대시보드 애플리케이션 실행
터미널에서 다음 명령어를 실행하여 Streamlit 로컬 개발 서버를 구동합니다.
```bash
uv run streamlit run main.py
```
* 서버가 성공적으로 가동되면 브라우저에 `http://localhost:8501` 페이지가 열리며 인터랙티브한 대시보드를 사용할 수 있습니다.

### 2. 특정 데이터 로더 모듈 단독 테스트
한국 자산 데이터 로더(`kr_loader.py`)의 테스트 블록 단독 실행도 `uv run`으로 간편하게 처리됩니다:
```bash
uv run python src/data_loader/kr_loader.py
```

---

## 📦 핵심 의존성 (Core Dependencies)
* **Streamlit (>= 1.30.0):** 글래스모피즘 스타일의 프리미엄 반응형 대시보드 UI 구현.
* **yfinance (>= 0.2.38):** 미국 고변동성 ETF 실시간 시세 및 뉴스 피드 수집.
* **finance-datareader (>= 0.9.84):** 한국 ETF 및 ETN 시장 가격 데이터 로드.
* **Plotly (>= 5.18.0):** 기술 분석 차트 및 누적 성과 곡선 시각화.
* **Google Generative AI (>= 0.4.0):** 뉴스 감성 판독 및 브리핑 보고서 발행용 Gemini LLM.
* **Pandas / Numpy:** 고속 퀀트 연산 및 시계열 데이터프레임 가공.
