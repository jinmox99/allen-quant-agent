import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import internal modules
from src.data_loader import get_kr_assets, get_kr_stock_data, get_kr_stock_info
from src.data_loader import get_us_assets, get_us_stock_data, get_us_stock_info, get_us_stock_news
from src.analyzers import add_all_indicators
from src.backtester import run_backtest
from src.analyzers.sentiment import analyze_news_sentiment
from src.agent import generate_agent_report

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="Allen Quant Agent",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ----------------- PREMIUM DARK STYLING -----------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap');
    
    /* Base theme override */
    html, body, [class*="css"] {
        font-family: 'Outfit', sans-serif;
    }
    
    /* Elegant Dark Glassmorphism Container */
    .stApp {
        background-color: #0d0f14;
        color: #e2e8f0;
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background-color: #121620 !important;
        border-right: 1px solid #1f293d;
    }
    
    /* Tabs custom styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
        background-color: #121620;
        padding: 8px 16px;
        border-radius: 12px;
        border: 1px solid #1f293d;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 8px;
        color: #94a3b8;
        font-weight: 600;
        font-size: 16px;
        transition: all 0.3s;
    }
    .stTabs [data-baseweb="tab"]:hover {
        color: #38bdf8;
    }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #38bdf8 !important;
        border-bottom-color: #38bdf8 !important;
    }
    
    /* Glassmorphic Metrics Card */
    .metric-card {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8));
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 4px 30px rgba(0, 0, 0, 0.2);
        backdrop-filter: blur(5px);
        transition: transform 0.3s, border-color 0.3s;
    }
    .metric-card:hover {
        transform: translateY(-4px);
        border-color: rgba(56, 189, 248, 0.4);
    }
    .metric-title {
        font-size: 14px;
        color: #94a3b8;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: 700;
        letter-spacing: -0.5px;
    }
    .metric-sub {
        font-size: 12px;
        margin-top: 6px;
        font-weight: 600;
    }
    
    /* Neon badges */
    .badge-positive {
        color: #10b981;
        background-color: rgba(16, 185, 129, 0.1);
        border: 1px solid rgba(16, 185, 129, 0.3);
        border-radius: 6px;
        padding: 2px 8px;
        font-weight: bold;
    }
    .badge-negative {
        color: #ef4444;
        background-color: rgba(239, 68, 68, 0.1);
        border: 1px solid rgba(239, 68, 68, 0.3);
        border-radius: 6px;
        padding: 2px 8px;
        font-weight: bold;
    }
    .badge-neutral {
        color: #94a3b8;
        background-color: rgba(148, 163, 184, 0.1);
        border: 1px solid rgba(148, 163, 184, 0.3);
        border-radius: 6px;
        padding: 2px 8px;
        font-weight: bold;
    }
    
    /* Title decoration */
    .agent-title {
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 40px;
        margin-bottom: 8px;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- SIDEBAR CONFIG -----------------
st.sidebar.markdown("<h2 style='text-align: center; color: #38bdf8;'>⚙️ Quant Agent Settings</h2>", unsafe_allow_html=True)

# Footer credits
st.sidebar.markdown("---")
st.sidebar.markdown("<div style='text-align: center; color: #64748b; font-size: 12px;'>Allen Quant Agent v1.0<br>© 2026 Pair Programming Pro</div>", unsafe_allow_html=True)

# ----------------- APP HEADER -----------------
st.markdown("<h1 class='agent-title'>⚡ Allen Quant Agent</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; font-size: 16px; margin-top: -12px;'>미국 고변동성 레버리지 ETF 퀀트 백테스터 & 한국 포트폴리오 실시간 AI 어드바이저</p>", unsafe_allow_html=True)
st.markdown("---")

# Predefined asset configurations
US_TICKERS = get_us_assets()
KR_TICKERS = get_kr_assets()

# ----------------- CACHED DATA LOADER FOR UNIFIED DASHBOARD -----------------
@st.cache_data(ttl=60)
def get_all_assets_info():
    all_info = []
    # US Markets
    for ticker in US_TICKERS:
        try:
            info = get_us_stock_info(ticker)
            all_info.append({
                'ticker': ticker,
                'name': info.get('name', 'Unknown'),
                'current_price': info.get('current_price', 0.0),
                'change_percent': info.get('change_percent', 0.0),
                'last_updated': info.get('last_updated', 'N/A'),
                'market': 'US',
                'flag': '🇺🇸'
            })
        except Exception as e:
            all_info.append({
                'ticker': ticker,
                'name': US_TICKERS[ticker],
                'current_price': 0.0,
                'change_percent': 0.0,
                'last_updated': 'Error',
                'market': 'US',
                'flag': '🇺🇸'
            })
    # KR Markets
    for ticker in KR_TICKERS:
        try:
            info = get_kr_stock_info(ticker)
            all_info.append({
                'ticker': ticker,
                'name': info.get('name', 'Unknown'),
                'current_price': info.get('current_price', 0.0),
                'change_percent': info.get('change_percent', 0.0),
                'last_updated': info.get('last_updated', 'N/A'),
                'market': 'KR',
                'flag': '🇰🇷'
            })
        except Exception as e:
            all_info.append({
                'ticker': ticker,
                'name': KR_TICKERS[ticker],
                'current_price': 0.0,
                'change_percent': 0.0,
                'last_updated': 'Error',
                'market': 'KR',
                'flag': '🇰🇷'
            })
    return all_info

# ----------------- TAB STRUCTURE -----------------
tab1, tab2, tab3 = st.tabs([
    "📈 실시간 자산 모니터링 (Market Tracker)", 
    "🚀 미국 레버리지 ETF 백테스터 (US Quant Backtester)", 
    "🤖 AI 포트폴리오 브리핑 에이전트 (AI Trading Broker)"
])

# ==========================================
# TAB 1: MARKET TRACKER (Unified US & KR)
# ==========================================
with tab1:
    st.subheader("📊 글로벌 퀀트 자산 실시간 전광판 (Unified Overview Dashboard)")
    st.markdown("추적 대상인 미국과 한국의 핵심 레버리지/배당 자산 8종의 실시간 현황입니다. **원하는 종목 카드의 [상세 분석 보기] 버튼을 누르시면** 하단에 실시간 차트와 정밀 기술 지표가 동적으로 로드됩니다.")
    
    # Initialize session state for selected ticker if not exists
    if 'selected_ticker' not in st.session_state:
        st.session_state.selected_ticker = 'SOXL'
        
    with st.spinner("실시간 전 자산 시세 수집 및 동기화 중..."):
        all_infos = get_all_assets_info()
        
    # Render unified overview cards (4 columns x 2 rows)
    for i in range(0, len(all_infos), 4):
        cols = st.columns(4)
        for j in range(4):
            if i + j < len(all_infos):
                info = all_infos[i + j]
                ticker = info['ticker']
                name = info['name']
                price = info['current_price']
                change = info['change_percent']
                flag = info['flag']
                market = info['market']
                
                # Format price
                price_unit = "$" if market == 'US' else "원"
                price_format = f"{price:,.2f}" if market == 'US' else f"{price:,.0f}"
                
                # Highlight border and background if selected
                is_selected = (st.session_state.selected_ticker == ticker)
                border_style = "border: 2px solid #38bdf8; box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);" if is_selected else "border: 1px solid rgba(255, 255, 255, 0.08);"
                bg_gradient = "linear-gradient(135deg, rgba(30, 58, 138, 0.25), rgba(15, 23, 42, 0.95))" if is_selected else "linear-gradient(135deg, rgba(30, 41, 59, 0.7), rgba(15, 23, 42, 0.8))"
                change_color = "#10b981" if change >= 0 else "#ef4444"
                
                # Format market badges beautifully for Windows and general styling
                if market == 'US':
                    market_badge = "<span style='background: rgba(56, 189, 248, 0.12); color: #38bdf8; border: 1px solid rgba(56, 189, 248, 0.25); border-radius: 6px; padding: 2px 8px; font-size: 9px; font-weight: 800; letter-spacing: 0.5px;'>🔵 US MARKET</span>"
                else:
                    market_badge = "<span style='background: rgba(239, 68, 68, 0.12); color: #ef4444; border: 1px solid rgba(239, 68, 68, 0.25); border-radius: 6px; padding: 2px 8px; font-size: 9px; font-weight: 800; letter-spacing: 0.5px;'>🔴 KR MARKET</span>"
                    
                with cols[j]:
                    st.markdown(f"""
                    <div class='metric-card' style='background: {bg_gradient}; border: {border_style}; border-radius: 16px; padding: 18px 16px; text-align: center; height: 200px; margin-bottom: 10px; display: flex; flex-direction: column; justify-content: space-between;'>
                        <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;'>
                            {market_badge}
                            <span style='color: #38bdf8; font-weight: 800; font-size: 14px; letter-spacing: -0.2px;'>{ticker}</span>
                        </div>
                        <div style='font-size: 15px; font-weight: 700; color: #ffffff; height: 44px; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; line-height: 1.4; margin-top: 10px; margin-bottom: 6px; font-family: "Outfit", sans-serif;' title='{name}'>{name}</div>
                        <div>
                            <div style='font-size: 26px; font-weight: 900; color: #ffffff; letter-spacing: -0.8px;'>{price_format} <span style='font-size: 16px; font-weight: 600; color: #94a3b8;'>{price_unit}</span></div>
                            <div style='font-size: 16px; font-weight: 800; color: {change_color}; margin-top: 2px;'>{change:+.2f}%</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button("🔍 상세 분석 보기", key=f"select_{ticker}", use_container_width=True):
                        st.session_state.selected_ticker = ticker
                        st.rerun()

    # Determine is_us and target_ticker from session_state.selected_ticker
    target_ticker = st.session_state.selected_ticker
    is_us = target_ticker in US_TICKERS
    
    st.markdown("---")
    st.subheader(f"📈 [상세 분석] {st.session_state.selected_ticker} - {US_TICKERS[target_ticker] if is_us else KR_TICKERS[target_ticker]}")
    
    with st.spinner("거래소 실시간 시세 및 재무 지표 로드 중..."):
        if is_us:
            info = get_us_stock_info(target_ticker)
            price_unit = "$"
            price_format = f"{info['current_price']:,.2f}"
        else:
            info = get_kr_stock_info(target_ticker)
            price_unit = "원"
            price_format = f"{info['current_price']:,.0f}"
            
        # Display main price summary
        col_kp1, col_kp2, col_kp3 = st.columns(3)
        with col_kp1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>자산명</div>
                <div class='metric-value' style='color: #818cf8; font-size: 22px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{info['name']}</div>
                <div class='metric-sub' style='color: #64748b;'>종목코드: {info['ticker']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_kp2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>현재 종가 (Close)</div>
                <div class='metric-value' style='color: #e2e8f0;'>{price_format} {price_unit}</div>
                <div class='metric-sub' style='color: #64748b;'>최종 업데이트: {info['last_updated']}</div>
            </div>
            """, unsafe_allow_html=True)
            
        with col_kp3:
            change = info['change_percent']
            change_color = "#10b981" if change >= 0 else "#ef4444"
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-title'>전일 대비 등락률</div>
                <div class='metric-value' style='color: {change_color};'>{change:+.2f}%</div>
                <div class='metric-sub' style='color: #64748b;'>전일 대비 변동</div>
            </div>
            """, unsafe_allow_html=True)
            
        # Draw Candlestick
        st.markdown("<br>", unsafe_allow_html=True)
        
        if is_us:
            df = get_us_stock_data(target_ticker, (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'))
        else:
            df = get_kr_stock_data(target_ticker, (datetime.now() - timedelta(days=180)).strftime('%Y-%m-%d'))
            
        if df.empty:
            st.warning("주가 차트 데이터를 가져오지 못했습니다.")
        else:
            # Calculate technical metrics
            df = add_all_indicators(df)
            latest_ind = df.iloc[-1]
            
            # Subplots: Candlestick + Volume + SMA
            fig_chart = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                   vertical_spacing=0.08, row_heights=[0.7, 0.3])
            
            # Candlestick colors dynamically based on market type
            # US style: Green is positive, Red is negative
            # Korean style: Red is positive, Blue is negative
            if is_us:
                inc_color = '#10b981'
                dec_color = '#ef4444'
            else:
                inc_color = '#ef4444'
                dec_color = '#3b82f6'
                
            # Candlestick
            fig_chart.add_trace(go.Candlestick(
                x=df['Date'], open=df['Open'], high=df['High'],
                low=df['Low'], close=df['Close'],
                name="캔들 가격",
                increasing_line_color=inc_color, decreasing_line_color=dec_color
            ), row=1, col=1)
            
            # SMA Lines
            fig_chart.add_trace(go.Scatter(
                x=df['Date'], y=df['SMA_10'],
                name="10일 이평선 (MA10)", line=dict(color="#38bdf8", width=1.2)
            ), row=1, col=1)
            fig_chart.add_trace(go.Scatter(
                x=df['Date'], y=df['SMA_25'],
                name="25일 이평선 (MA25)", line=dict(color="#f59e0b", width=1.2)
            ), row=1, col=1)
            fig_chart.add_trace(go.Scatter(
                x=df['Date'], y=df['SMA_45'],
                name="45일 이평선 (MA45)", line=dict(color="#ec4899", width=1.2)
            ), row=1, col=1)
            
            # Volume
            fig_chart.add_trace(go.Bar(
                x=df['Date'], y=df['Volume'],
                name="거래량", marker=dict(color="#64748b")
            ), row=2, col=1)
            
            fig_chart.update_layout(
                title=f"📈 {info['name']} 최근 6개월 주가 추세 및 기술 분석 차트",
                template="plotly_dark",
                height=500,
                xaxis_rangeslider_visible=False,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=20, r=20, t=50, b=20),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)'
            )
            st.plotly_chart(fig_chart, use_container_width=True)
            
            # Technical metrics grid
            st.markdown("#### **🛠️ 주요 퀀트 기술적 모멘텀 지표 (Quant Indicators)**")
            col_k_ind1, col_k_ind2, col_k_ind3, col_k_ind4 = st.columns(4)
            
            with col_k_ind1:
                rsi_val = latest_ind['RSI']
                rsi_badge = "<span class='badge-neutral'>보통</span>"
                if rsi_val >= 70: rsi_badge = "<span class='badge-negative'>과매수 과열</span>"
                elif rsi_val <= 30: rsi_badge = "<span class='badge-positive'>과매도 기회</span>"
                
                st.markdown(f"""
                <div style='background-color: #121620; border: 1px solid #1f293d; padding: 16px; border-radius: 12px;'>
                    <div style='color: #64748b; font-size: 13px;'>상대강도지수 (RSI 14)</div>
                    <div style='font-size: 20px; font-weight: 700; color: #e2e8f0; margin-top: 4px;'>{rsi_val:.2f} {rsi_badge}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_k_ind2:
                macd_val = latest_ind['MACD']
                macd_sig = latest_ind['MACD_Signal']
                macd_state = "<span class='badge-positive'>매수 강화</span>" if macd_val > macd_sig else "<span class='badge-negative'>매수 위축</span>"
                
                st.markdown(f"""
                <div style='background-color: #121620; border: 1px solid #1f293d; padding: 16px; border-radius: 12px;'>
                    <div style='color: #64748b; font-size: 13px;'>MACD 오실레이터</div>
                    <div style='font-size: 20px; font-weight: 700; color: #e2e8f0; margin-top: 4px;'>{latest_ind['MACD_Hist']:.2f} {macd_state}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_k_ind3:
                price = latest_ind['Close']
                sma25 = latest_ind['SMA_25']
                sma_state = "<span class='badge-positive'>추세 상회</span>" if price > sma25 else "<span class='badge-negative'>추세 하회</span>"
                
                st.markdown(f"""
                <div style='background-color: #121620; border: 1px solid #1f293d; padding: 16px; border-radius: 12px;'>
                    <div style='color: #64748b; font-size: 13px;'>25일 평균 괴리도</div>
                    <div style='font-size: 20px; font-weight: 700; color: #e2e8f0; margin-top: 4px;'>{((price-sma25)/sma25)*100:+.2f}% {sma_state}</div>
                </div>
                """, unsafe_allow_html=True)
                
            with col_k_ind4:
                bb_width = (latest_ind['BB_Upper'] - latest_ind['BB_Lower']) / latest_ind['BB_Mid'] * 100
                st.markdown(f"""
                <div style='background-color: #121620; border: 1px solid #1f293d; padding: 16px; border-radius: 12px;'>
                    <div style='color: #64748b; font-size: 13px;'>볼린저 밴드 너비 (변동성)</div>
                    <div style='font-size: 20px; font-weight: 700; color: #e2e8f0; margin-top: 4px;'>{bb_width:.2f}%</div>
                </div>
                """, unsafe_allow_html=True)

# ==========================================
# TAB 2: US LEVERAGED BACKTESTER
# ==========================================
with tab2:
    st.subheader("🇺🇸 미국 고레버리지 ETF 퀀트 백테스터 (3X Shares)")
    st.markdown("3배 레버리지 ETF인 **SOXL, TECL, TQQQ, UPRO**에 다양한 기술적 퀀트 전략을 시뮬레이션해 봅니다.")
    
    col_ctrl1, col_ctrl2, col_ctrl3 = st.columns([1, 1.5, 1.5])
    
    with col_ctrl1:
        us_ticker = st.selectbox("대상 자산 선택", list(US_TICKERS.keys()), format_func=lambda x: f"{x} - {US_TICKERS[x]}", key="backtest_us_ticker_select")
        strategy_type = st.selectbox("트레이딩 전략 선택", ["SMA Crossover", "RSI Momentum", "Combined"], key="backtest_strategy_select")
        initial_capital = st.number_input("초기 투자금 (USD)", min_value=1000.0, max_value=1000000.0, value=10000.0, step=1000.0, key="backtest_capital_input")
        commission = st.slider("수수료 및 슬리피지 (%)", 0.0, 1.0, 0.1, step=0.05, key="backtest_commission_slider") / 100.0
        
    with col_ctrl2:
        st.markdown("**📅 백테스팅 기간 설정**")
        start_date = st.date_input("백테스트 시작일", datetime.now() - timedelta(days=5*365), key="backtest_start_date")
        end_date = st.date_input("백테스트 종료일", datetime.now(), key="backtest_end_date")
        
    with col_ctrl3:
        st.markdown("**🛠️ 전략 매개변수 커스텀 조율**")
        if strategy_type in ["SMA Crossover", "Combined"]:
            sma_short = st.slider("단기 이동평균선 (Short MA)", 5, 50, 10, key="backtest_sma_short")
            sma_long = st.slider("장기 이동평균선 (Long MA)", 21, 200, 45, key="backtest_sma_long")
            backtest_params = {"sma_short": sma_short, "sma_long": sma_long}
        if strategy_type in ["RSI Momentum", "Combined"]:
            rsi_period = st.slider("RSI 계산 기간 (RSI Period)", 5, 30, 14, key="backtest_rsi_period")
            rsi_buy = st.slider("RSI 매수 과매도 하한선 (RSI Buy)", 10, 50, 30, key="backtest_rsi_buy")
            rsi_sell = st.slider("RSI 매도 과매수 상한선 (RSI Sell)", 50, 90, 70, key="backtest_rsi_sell")
            if 'backtest_params' not in locals():
                backtest_params = {}
            backtest_params.update({"rsi_period": rsi_period, "rsi_buy": rsi_buy, "rsi_sell": rsi_sell})
            
    # Load and Backtest
    if st.button("🚀 퀀트 백테스팅 실행 (Run Simulation)", key="run_us_backtest"):
        with st.spinner("미국 시장 역사적 시세 수집 중 및 퀀트 백테스팅 연산 중..."):
            # Fetch historical data
            raw_us_df = get_us_stock_data(us_ticker, start_date.strftime('%Y-%m-%d'), end_date.strftime('%Y-%m-%d'))
            
            if raw_us_df.empty or len(raw_us_df) < 5:
                st.error("데이터 로드 실패 또는 데이터 양이 너무 적어 시뮬레이션할 수 없습니다.")
            else:
                # Add indicators and run backtest
                df_with_ind = add_all_indicators(raw_us_df)
                results = run_backtest(df_with_ind, initial_capital, commission, strategy_type, backtest_params)
                
                metrics = results["metrics"]
                eq_df = results["equity_curve"]
                trades = results["trades"]
                
                if "error" in metrics:
                    st.error(f"오류: {metrics['error']}")
                else:
                    # Render Metrics Display
                    st.markdown("### 📊 퀀트 성과 분석 요약 (Performance Metrics)")
                    col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
                    
                    with col_m1:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-title'>최종 자산 총액</div>
                            <div class='metric-value' style='color: #38bdf8;'>${metrics['Final_Capital']:,.2f}</div>
                            <div class='metric-sub' style='color: #64748b;'>초기금액: ${metrics['Initial_Capital']:,.0f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_m2:
                        ret_color = "#10b981" if metrics['Total_Return_Pct'] >= 0 else "#ef4444"
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-title'>누적 수익률 (Strategy)</div>
                            <div class='metric-value' style='color: {ret_color};'>{metrics['Total_Return_Pct']:+.2f}%</div>
                            <div class='metric-sub' style='color: #64748b;'>벤치마크: {metrics['Benchmark_Return_Pct']:+.2f}%</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_m3:
                        cagr_color = "#10b981" if metrics['CAGR_Pct'] >= 0 else "#ef4444"
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-title'>연평균 수익률 (CAGR)</div>
                            <div class='metric-value' style='color: {cagr_color};'>{metrics['CAGR_Pct']:.2f}%</div>
                            <div class='metric-sub' style='color: #64748b;'>샤프지수: {metrics['Sharpe_Ratio']:.2f}</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_m4:
                        mdd_color = "#ef4444" if metrics['MDD_Pct'] < -20 else "#38bdf8"
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-title'>최대 낙폭 (MDD)</div>
                            <div class='metric-value' style='color: {mdd_color};'>{metrics['MDD_Pct']:.2f}%</div>
                            <div class='metric-sub' style='color: #64748b;'>위험 최소화 수준</div>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    with col_m5:
                        st.markdown(f"""
                        <div class='metric-card'>
                            <div class='metric-title'>승률 및 거래 횟수</div>
                            <div class='metric-value' style='color: #818cf8;'>{metrics['Win_Rate_Pct']:.1f}%</div>
                            <div class='metric-sub' style='color: #64748b;'>총 거래 횟수: {metrics['Trade_Count']}회</div>
                        </div>
                        """, unsafe_allow_html=True)
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    # Charting: Equity Curve Comparison
                    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                                        vertical_spacing=0.08, row_heights=[0.7, 0.3])
                    
                    # Strategy Equity Curve
                    fig.add_trace(go.Scatter(
                        x=eq_df["Date"], y=eq_df["Portfolio_Value"],
                        name="백테스팅 전략 포트폴리오", line=dict(color="#38bdf8", width=2.5)
                    ), row=1, col=1)
                    
                    # Benchmark Buy & Hold (rescaled to initial capital)
                    bench_curve = eq_df["Price"] / eq_df["Price"].iloc[0] * initial_capital
                    fig.add_trace(go.Scatter(
                        x=eq_df["Date"], y=bench_curve,
                        name="단순 보유 (Buy & Hold)", line=dict(color="#64748b", width=1.5, dash="dash")
                    ), row=1, col=1)
                    
                    # Drawdowns
                    eq_df["Peak"] = eq_df["Portfolio_Value"].cummax()
                    eq_df["DD"] = (eq_df["Portfolio_Value"] - eq_df["Peak"]) / eq_df["Peak"] * 100
                    fig.add_trace(go.Scatter(
                        x=eq_df["Date"], y=eq_df["DD"],
                        name="낙폭 (Drawdown %)", fill="tozeroy", line=dict(color="#ef4444", width=1)
                    ), row=2, col=1)
                    
                    # Layout updates
                    fig.update_layout(
                        title=f"📈 {us_ticker} 퀀트 전략 vs 단순보유 누적 수익률 비교",
                        template="plotly_dark",
                        height=550,
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                        margin=dict(l=20, r=20, t=50, b=20),
                        paper_bgcolor='rgba(0,0,0,0)',
                        plot_bgcolor='rgba(0,0,0,0)'
                    )
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Render Trade Log Expander
                    with st.expander("📋 거래 이력 로그 (Trade Transaction History)"):
                        if len(trades) == 0:
                            st.write("해당 기간 동안 거래가 발생하지 않았습니다.")
                        else:
                            trade_df = pd.DataFrame(trades)
                            # Formatting
                            trade_df["Shares"] = trade_df["Shares"].map(lambda x: f"{x:.4f}")
                            trade_df["Price"] = trade_df["Price"].map(lambda x: f"${x:,.2f}")
                            trade_df["Value"] = trade_df["Value"].map(lambda x: f"${x:,.2f}")
                            trade_df["Commission"] = trade_df["Commission"].map(lambda x: f"${x:,.2f}")
                            trade_df["Cash"] = trade_df["Cash"].map(lambda x: f"${x:,.2f}")
                            
                            st.dataframe(trade_df, use_container_width=True)

# ==========================================
# TAB 3: AI PORTFOLIO AGENT BRIEFING
# ==========================================
with tab3:
    st.subheader("🤖 Allen AI 포트폴리오 투자 브리핑 에이전트")
    st.markdown("자산을 선택하면 실시간 차트 지표, 최신 감성 뉴스, 그리고 모멘텀 점수를 종합하여 Gemini 기반 심층 에이전트 리포트를 발행합니다.")
    
    col_ag1, col_ag2 = st.columns([1.5, 2.5])
    
    with col_ag1:
        # Group both markets into a single selectbox
        asset_options = {}
        for k, v in US_TICKERS.items():
            asset_options[k] = f"🇺🇸 {k} - {v}"
        for k, v in KR_TICKERS.items():
            asset_options[k] = f"🇰🇷 {k} - {v}"
            
        target_ticker = st.selectbox("분석 대상 자산 선택", list(asset_options.keys()), format_func=lambda x: asset_options[x], key="agent_target_select")
        
        st.markdown("""
        **🧠 에이전트 분석 로직**
        1. **시세 및 이평선:** 주가와 장단기 이동평균선 격차를 분석해 트렌드를 인지합니다.
        2. **뉴스 감성 필터링:** 미국 종목의 경우 최신 뉴스를 수집해 실시간 센티먼트를 등급화합니다.
        3. **종합 의사결정 추론:** 기술 지표와 뉴스 센티먼트, 레버리지 및 상품 리스크 가이드를 통합하여 최종 권장 투자 지침서(Briefing Report)를 작성합니다.
        """)
        
        # Button trigger
        trigger_analysis = st.button("🧠 AI 에이전트 보고서 발행 (Issue Report)", key="trigger_ai_report")
        
    with col_ag2:
        if trigger_analysis:
            with st.spinner("최신 뉴스 수집 및 AI 에이전트 종합 리포트 발행 중..."):
                # 1. Fetch prices
                is_us = target_ticker in US_TICKERS
                name = US_TICKERS[target_ticker] if is_us else KR_TICKERS[target_ticker]
                
                if is_us:
                    raw_df = get_us_stock_data(target_ticker, (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
                else:
                    raw_df = get_kr_stock_data(target_ticker, (datetime.now() - timedelta(days=90)).strftime('%Y-%m-%d'))
                
                if raw_df.empty:
                    st.error("해당 종목의 분석용 최근 시세 데이터를 불러오지 못했습니다.")
                else:
                    # Append indicators
                    df_ind = add_all_indicators(raw_df)
                    
                    # 2. Get News Sentiment (US stocks fetch actual yfinance news, KR stocks fallback to basic)
                    sentiment_summary = {"score": 0.0, "label": "NEUTRAL", "reason": "국내 ETF는 실시간 뉴스 API 연동 대기 중입니다."}
                    news_list = []
                    
                    if is_us:
                        news_list = get_us_stock_news(target_ticker)
                        if news_list:
                            # Analyze average sentiment
                            scores = []
                            reasons = []
                            for art in news_list[:4]: # Analyze top 4 articles to save rate limit
                                sentiment = analyze_news_sentiment(art["title"], art["summary"])
                                scores.append(sentiment["score"])
                                reason_item = sentiment.get("reason", "뉴스 분석 완료.")
                                reasons.append(reason_item)
                                
                            avg_score = np.mean(scores) if scores else 0.0
                            label = "NEUTRAL"
                            if avg_score > 0.15: label = "BULLISH"
                            elif avg_score < -0.15: label = "BEARISH"
                            
                            sentiment_summary = {
                                "score": avg_score,
                                "label": label,
                                "reason": reasons[0] if reasons else "뉴스 분석 완료."
                            }
                    
                    # 3. Generate Agent Report
                    report = generate_agent_report(target_ticker, name, df_ind, sentiment_summary)
                    
                    # 4. Display Report UI
                    st.markdown("### 📝 AI 에이전트 분석 결과 보고서")
                    
                    # Visual sentiment card
                    col_b1, col_b2 = st.columns(2)
                    with col_b1:
                        rec_op = report.get("opinion_kr", "관망 (Hold)")
                        st.metric("포트폴리오 에이전트 최종 의견", rec_op)
                    with col_b2:
                        lbl = sentiment_summary["label"]
                        lbl_color = "🟢 BULLISH" if lbl == "BULLISH" else ("🔴 BEARISH" if lbl == "BEARISH" else "⚪ NEUTRAL")
                        st.metric("실시간 뉴스 감성 등급", f"{lbl_color} ({sentiment_summary['score']:+.2f})")
                        
                    st.markdown("---")
                    st.markdown(report.get("report_markdown", "보고서 텍스트 생성 실패."))
                    
                    # News Feed Expander for US stocks
                    if is_us and news_list:
                        with st.expander("📰 수집된 최신 글로벌 뉴스 보기 (US Market News Feed)"):
                            for art in news_list:
                                st.markdown(f"""
                                **[{art['publisher']}] {art['title']}**
                                *게시시간: {art['time']}*  
                                {art['summary']}  
                                [기사 링크 바로가기]({art['link']})
                                ---
                                """, unsafe_allow_html=True)
        else:
            st.info("왼쪽 패널에서 종목을 선택한 후 'AI 에이전트 보고서 발행' 버튼을 클릭하시면 에이전트의 브리핑 보고서가 여기에 렌더링됩니다.")
