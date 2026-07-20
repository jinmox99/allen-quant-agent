import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from dotenv import load_dotenv
import json
import os

# Load environment variables
load_dotenv()

# Import internal modules
import sys
# Add the src directory to sys.path to avoid Streamlit Cloud's /mount/src module collision
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'src'))

from data_loader.toss_loader import get_toss_stock_data as get_kr_stock_data, get_toss_stock_info as get_kr_stock_info, get_toss_cache_key as get_krx_cache_key
from data_loader.us_loader import get_us_stock_data, get_us_stock_info, get_us_cache_key
from analyzers.indicators import add_all_indicators
from analyzers.trend import analyze_trend
from backtester.simple import run_indicator_backtests
from analyzers.ranking import rank_stocks

# ----------------- PAGE CONFIG -----------------
st.set_page_config(
    page_title="단일 종목 기술적 분석 대시보드",
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
    
    /* Title decoration */
    .agent-title {
        background: linear-gradient(to right, #38bdf8, #818cf8);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 800;
        font-size: 40px;
        margin-bottom: 8px;
    }
    
    .status-panel {
        padding: 24px;
        border-radius: 16px;
        margin-top: 20px;
        border: 1px solid rgba(255, 255, 255, 0.1);
        display: flex;
        align-items: center;
        gap: 20px;
    }
    
    /* Star Favorite Button - minimal styling */
    button[kind="secondary"] {
        /* default Streamlit buttons - no changes */
    }
</style>
""", unsafe_allow_html=True)

# ----------------- APP HEADER -----------------
st.markdown("<h1 class='agent-title'>⚡ AI 기술적 추세 분석 대시보드</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; font-size: 16px; margin-top: -12px;'>다중 지표를 활용한 입체적 추세 진단 및 Top 50 종목 랭킹 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

tab1, tab2 = st.tabs(["📊 단일 종목 분석", "🏆 시가총액 Top 50 랭킹"])

# ----------------- FAVORITES MANAGER -----------------
FAVORITES_FILE = "favorites.json"
def load_favorites():
    if os.path.exists(FAVORITES_FILE):
        try:
            with open(FAVORITES_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            pass
    return {
        "KR": {
            "삼성전자": "005930",
            "SK하이닉스": "000660",
            "TIGER 200": "102110",
            "KODEX 200 (코스피200 ETF)": "069500"
        },
        "US": {
            "애플 (AAPL)": "AAPL",
            "반도체 ETF (SOXX)": "SOXX",
            "DRAM": "DRAM",
            "한국 ETF (EWY)": "EWY"
        }
    }

def save_favorites(favs):
    with open(FAVORITES_FILE, "w", encoding="utf-8") as f:
        json.dump(favs, f, ensure_ascii=False, indent=2)

user_favorites = load_favorites()

# ----------------- SIDEBAR & INPUT -----------------
with st.sidebar:
    st.header("🔍 종목 검색")
    
    # 데이터프레임 행 선택 감지 및 상태 동기화 (오류 방지를 위해 렌더링 전 최상단에서 처리)
    for mk in ["KR", "US", "KR_ETF", "US_ETF"]:
        df_key = f"ranking_table_{mk}"
        last_sel_key = f"last_sel_{mk}"
        
        if df_key in st.session_state:
            current_sel = st.session_state[df_key].get("selection", {}).get("rows", [])
            last_sel = st.session_state.get(last_sel_key, [])
            
            # 선택이 변경되었고 유효한 선택이 있는 경우
            if current_sel != last_sel and current_sel:
                st.session_state[last_sel_key] = current_sel
                row_idx = current_sel[0]
                
                if f'ranking_result_{mk}' in st.session_state:
                    df = st.session_state[f'ranking_result_{mk}']
                    if row_idx < len(df):
                        st.session_state.sidebar_ticker_input = df.iloc[row_idx]['Ticker']
                        # 랭킹 탭에 맞는 시장으로 사이드바 시장(Market) 드롭다운 자동 변경
                        st.session_state.market_select = "KR (한국)" if mk.startswith("KR") else "US (미국)"
            elif current_sel != last_sel:
                # 선택이 해제된 경우 상태만 업데이트
                st.session_state[last_sel_key] = current_sel

    if "market_select" not in st.session_state:
        st.session_state.market_select = "KR (한국)"
        
    market = st.selectbox("시장 (Market)", ["KR (한국)", "US (미국)"], key="market_select")
    is_kr = market.startswith("KR")
    market_key = "KR" if is_kr else "US"
    
    # 시장별 즐겨찾기 목록 구성
    FAVORITES = {"🌟 직접 입력": ""}
    FAVORITES.update(user_favorites[market_key])
    
    if "sidebar_ticker_input" not in st.session_state:
        default_ticker = FAVORITES[list(FAVORITES.keys())[1]] if len(FAVORITES) > 1 else ("102110" if is_kr else "AAPL")
        st.session_state.sidebar_ticker_input = default_ticker
        
    # 현재 입력된 종목코드가 즐겨찾기에 있는지 확인 후 드롭다운 동기화
    current_input = st.session_state.sidebar_ticker_input
    matched_fav = "🌟 직접 입력"
    for k, v in FAVORITES.items():
        if v == current_input and k != "🌟 직접 입력":
            matched_fav = k
            break
            
    st.session_state.fav_selectbox = matched_fav
    
    def on_fav_change():
        fav = st.session_state.fav_selectbox
        if fav != "🌟 직접 입력":
            st.session_state.sidebar_ticker_input = FAVORITES[fav]
            
    fav_selection = st.selectbox("⭐ 즐겨찾기 종목", list(FAVORITES.keys()), key="fav_selectbox", on_change=on_fav_change)
    
    ticker_input = st.text_input("종목 코드 (수정 후 Enter ↵)", key="sidebar_ticker_input").strip().upper()
    
    period_options = {"3개월": 90, "6개월": 180, "1년": 365, "3년": 1095}
    selected_period = st.selectbox("조회 기간", list(period_options.keys()), index=1)
    days_to_fetch = period_options[selected_period]
    
    st.markdown("---")
    st.markdown("💡 **Tip:**\n- 한국 종목은 `000660`(SK하이닉스), `005930`(삼성전자) 등의 숫자를 입력하세요.\n- 미국 종목은 `AAPL`, `TSLA`, `NVDA` 등 영문 티커를 입력하세요.")

with tab1:
    col_t1, col_t2 = st.columns([0.88, 0.12])
    with col_t2:
        if st.button("🔄 새로고침", help="최신 시세로 다시 불러오기"):
            get_kr_stock_data.clear()
            get_kr_stock_info.clear()
            get_us_stock_data.clear()
            get_us_stock_info.clear()
            st.rerun()

# ----------------- DATA FETCHING (TAB 1) -----------------
    if not ticker_input:
        st.warning("👈 왼쪽 사이드바에서 분석할 종목 코드를 입력해주세요.")
        st.stop()

    with st.spinner(f"'{ticker_input}' 종목 데이터 및 기술적 지표 계산 중..."):
        start_date = (datetime.now() - timedelta(days=days_to_fetch)).strftime('%Y-%m-%d')
        # Fetch extra 250 days to ensure indicators requiring historical lookback (like Close_6M_ago, SMA_120) are fully computed from day 1
        fetch_start_date = (datetime.now() - timedelta(days=days_to_fetch + 250)).strftime('%Y-%m-%d')
        
        if is_kr:
            cache_key = get_krx_cache_key()
            info = get_kr_stock_info(ticker_input, cache_key=cache_key)
            df = get_kr_stock_data(ticker_input, start_date=fetch_start_date, cache_key=cache_key)
            price_unit = "원"
            price_format = f"{info['current_price']:,.0f}"
        else:
            cache_key = get_us_cache_key()
            info = get_us_stock_info(ticker_input, cache_key=cache_key)
            df = get_us_stock_data(ticker_input, start_date=fetch_start_date, cache_key=cache_key)
            price_unit = "$"
            price_format = f"{info['current_price']:,.2f}"

    if df.empty or len(df) < 20:
        st.error(f"⚠️ '{ticker_input}'에 대한 충분한 시세 데이터를 불러오지 못했습니다. 종목 코드와 시장 구분을 다시 확인해주세요.")
        st.stop()

    # ----------------- INDICATOR CALCULATION -----------------
    # Calculate indicators on the full fetched dataset (with extra lookback)
    df = add_all_indicators(df)
    full_df = df.copy()

    # Slice the DataFrame to the user-selected period (for rendering and backtesting)
    df['Date_parsed'] = pd.to_datetime(df['Date'])
    df = df[df['Date_parsed'] >= pd.to_datetime(start_date)].copy()
    df = df.drop(columns=['Date_parsed']).reset_index(drop=True)

    if df.empty or len(df) < 2:
        st.error("선택한 조회 기간에 해당하는 데이터가 부족합니다.")
        st.stop()

    latest = df.iloc[-1]
    trend_result = analyze_trend(df)

    # ----------------- METRICS DASHBOARD -----------------
    col_kp1, col_kp2, col_kp3, col_kp4 = st.columns(4)

    with col_kp1:
        is_favorite = False
        fav_key = None
        for k, v in user_favorites[market_key].items():
            if v == ticker_input:
                is_favorite = True
                fav_key = k
                break

        star_icon = "⭐" if is_favorite else "☆"
        star_color = "#facc15" if is_favorite else "#64748b"
        st.markdown(f"""
        <div class='metric-card' style='position: relative;'>
            <span style='position: absolute; top: 12px; right: 14px; font-size: 22px; color: {star_color};'>{star_icon}</span>
            <div class='metric-title'>분석 대상 종목</div>
            <div class='metric-value' style='color: #818cf8; font-size: 20px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{info['name']}</div>
            <div class='metric-sub' style='color: #64748b;'>{ticker_input} ({'KRX' if is_kr else 'US'})</div>
        </div>
        """, unsafe_allow_html=True)
        fav_btn_text = "즐겨찾기 해제" if is_favorite else "즐겨찾기 추가"
        if st.button(f"{star_icon} {fav_btn_text}", key="fav_star_btn", use_container_width=True):
            if is_favorite:
                del user_favorites[market_key][fav_key]
            else:
                user_favorites[market_key][info['name']] = ticker_input
            save_favorites(user_favorites)
            st.rerun()
        
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
            <div class='metric-sub' style='color: #64748b;'>일일 변동폭</div>
        </div>
        """, unsafe_allow_html=True)
        
    with col_kp4:
        macd_hist_val = latest['MACD_Hist']
        macd_color = "#10b981" if macd_hist_val >= 0 else "#ef4444"
        st.markdown(f"""
        <div class='metric-card'>
            <div class='metric-title'>MACD 오실레이터</div>
            <div class='metric-value' style='color: {macd_color};'>{macd_hist_val:+.2f}</div>
            <div class='metric-sub' style='color: #64748b;'>상승 모멘텀(>0) / 하락 모멘텀(<0)</div>
        </div>
        """, unsafe_allow_html=True)

    # Run backtests on the full historical dataset to get absolute last trade signals
    absolute_backtest_results = run_indicator_backtests(full_df)

    trade_info_map = {}
    for key, name in [('sma', '이동평균선 (SMA)'), ('macd', 'MACD'), 
                      ('quant_momentum', '💎 퀀트 모멘텀 (알파 추구형)'), 
                      ('ema_cross', '💎 ⚡ 골든크로스 EMA (5/20)'), 
                      ('dual_momentum', '💎 🛡️ 듀얼 모멘텀')]:
        if absolute_backtest_results and name in absolute_backtest_results and absolute_backtest_results[name]['trades']:
            last_trade = absolute_backtest_results[name]['trades'][-1]
            trade_price = last_trade['Price']
            curr_price = float(latest['Close'])
            pct_change = (curr_price - trade_price) / trade_price * 100
            
            trade_info_map[key] = {
                'date': last_trade['Date'],
                'action': '매수' if last_trade['Action'] == 'BUY' else '매도',
                'pct_change': pct_change
            }

    st.markdown("### 🎯 개별 지표별 AI 분석 결과")
    col_s1, col_s2 = st.columns(2)

    def render_status_panel(title, icon, signal, last_trade=None):
        bg_color = f"rgba({int(signal['color'][1:3], 16)}, {int(signal['color'][3:5], 16)}, {int(signal['color'][5:7], 16)}, 0.15)"
        
        score_badge = ""
        if 'score' in signal:
            score_badge = f"<span style='background-color: {signal['color']}; color: #ffffff; padding: 2px 8px; border-radius: 12px; font-size: 11px; font-weight: bold;'>점수: {signal['score']}점</span>"
        
        trade_html = ""
        if last_trade:
            action_color = "#10b981" if last_trade['action'] == '매수' else "#ef4444"
            
            # 주가가 올랐으면 초록색, 내렸으면 빨간색으로 일관되게 표시
            change_color = "#10b981" if last_trade['pct_change'] >= 0 else "#ef4444"
            
            trade_html = f"<div style='margin-top: 10px; padding-top: 10px; border-top: 1px solid rgba(255,255,255,0.1); font-size: 13px; color: #cbd5e1;'>" \
                         f"<span style='color: #94a3b8;'>마지막 신호:</span> <strong style='color: {action_color}'>{last_trade['action']}</strong> ({last_trade['date']}) " \
                         f"<span style='margin: 0 6px;'>|</span> " \
                         f"<span style='color: #94a3b8;'>이후 주가 변동:</span> <strong style='color: {change_color}'>{last_trade['pct_change']:+.2f}%</strong>" \
                         f"</div>"
            
        return f"""
    <div class='status-panel' style='background-color: {bg_color}; border-color: {signal['color']}; margin-top: 0px; margin-bottom: 16px; padding: 20px;'>
    <div style='font-size: 32px;'>{icon}</div>
    <div style='flex-grow: 1;'>
    <div style='display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;'>
        <div style='color: #94a3b8; font-size: 13px; font-weight: 600;'>{title}</div>
        {score_badge}
    </div>
    <div style='color: {signal['color']}; font-size: 18px; font-weight: 800; margin-bottom: 4px;'>{signal['status']}</div>
    <div style='color: #e2e8f0; font-size: 14px; line-height: 1.4;'>{signal['message']}</div>
    {trade_html}
    </div>
    </div>
    """

    with col_s1:
        st.markdown(render_status_panel("이동평균선 (SMA)", "📊", trend_result['sma'], trade_info_map.get('sma')), unsafe_allow_html=True)

    with col_s2:
        st.markdown(render_status_panel("MACD 오실레이터", "📈", trend_result['macd'], trade_info_map.get('macd')), unsafe_allow_html=True)


    # 활성화된 퀀트 모멘텀 전략 리스트 (원하는 전략을 쉽게 추가/삭제 가능)
    ACTIVE_STRATEGIES = [
        ("퀀트 모멘텀", "💎", "quant_momentum"),
        ("EMA 5/20 교차", "⚡", "ema_cross"),
        ("듀얼 모멘텀", "🛡️", "dual_momentum")
    ]

    # 한 줄에 2개씩 패널 배치
    cols = st.columns(2)
    for i, (name, icon, key) in enumerate(ACTIVE_STRATEGIES):
        with cols[i % 2]:
            st.markdown(render_status_panel(name, icon, trend_result.get(key, {"status": "오류", "color": "#ef4444", "message": ""}), trade_info_map.get(key)), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ----------------- ADVANCED CHARTING (Plotly) -----------------
    # Candlestick colors: US (Green/Red), KR (Red/Blue)
    if is_kr:
        inc_color = '#ef4444' # Red for up in KR
        dec_color = '#3b82f6' # Blue for down in KR
    else:
        inc_color = '#10b981' # Green for up in US
        dec_color = '#ef4444' # Red for down in US

    fig = go.Figure()

    # 1. Candlestick & Moving Averages
    fig.add_trace(go.Candlestick(
        x=df['Date'], open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'],
        name="Candle",
        increasing_line_color=inc_color, decreasing_line_color=dec_color
    ))

    fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_20'], name="SMA 20", line=dict(color="#38bdf8", width=1.5)))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_50'], name="SMA 50", line=dict(color="#f59e0b", width=1.5)))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_120'], name="SMA 120", line=dict(color="#ec4899", width=1.5)))

    # Add strategy final buy/sell signals on the chart
    for idx, (name, strategy_display_name) in enumerate([
        ("이동평균선 (SMA)", "SMA"),
        ("MACD", "MACD"),
        ("💎 퀀트 모멘텀 (알파 추구형)", "퀀트모멘텀"),
        ("💎 ⚡ 골든크로스 EMA (5/20)", "EMA교차"),
        ("💎 🛡️ 듀얼 모멘텀", "듀얼모멘텀")
    ]):
        if absolute_backtest_results and name in absolute_backtest_results and absolute_backtest_results[name]['trades']:
            last_trade = absolute_backtest_results[name]['trades'][-1]
            date = last_trade['Date']
            
            # Only annotate if the trade happened within the visible chart period
            if date >= start_date:
                action = last_trade['Action']
                price = last_trade['Price']
                color = "#10b981" if action == "BUY" else "#ef4444"
                text_action = "매수" if action == "BUY" else "매도"
                
                # Stagger vertical offsets to prevent label overlap
                offset = -30 - (idx * 22) if action == "BUY" else 30 + (idx * 22)
                
                fig.add_annotation(
                    x=date,
                    y=price,
                    text=f"{strategy_display_name}: {text_action}",
                    showarrow=True,
                    arrowhead=2,
                    arrowcolor=color,
                    arrowsize=1,
                    arrowwidth=1.5,
                    ax=0,
                    ay=offset,
                    bgcolor="rgba(13, 15, 20, 0.85)",
                    bordercolor=color,
                    borderwidth=1.5,
                    borderpad=4,
                    font=dict(color=color, size=9),
                    opacity=0.95
                )

    fig.update_layout(
        title=dict(text="📊 주가 추세 및 이동평균선 (SMA 20/50/120)", font=dict(size=16, color="#94a3b8")),
        template="plotly_dark",
        height=600,
        xaxis_rangeslider_visible=False,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        margin=dict(l=40, r=40, t=50, b=40),
        paper_bgcolor='#0d0f14',
        plot_bgcolor='#0d0f14'
    )

    st.plotly_chart(fig, use_container_width=True)



    # ----------------- BACKTEST SIMULATOR -----------------
    st.markdown("---")
    st.markdown("### 🧪 지표별 수익률 백테스트 시뮬레이션")
    st.markdown(f"<p style='color:#94a3b8; font-size:14px;'>현재 설정된 기간({selected_period}) 동안 각 지표의 매매 시그널을 따랐을 때의 수익률을 비교합니다.</p>", unsafe_allow_html=True)

    if st.button("🚀 백테스트 실행하기", type="primary", use_container_width=True):
        # 현재 선택된 종목과 기간을 세션 상태에 저장하여, 셀렉트박스 변경 시에도 초기화되지 않도록 함
        st.session_state['run_bt_context'] = f"{ticker_input}_{selected_period}"

    if st.session_state.get('run_bt_context') == f"{ticker_input}_{selected_period}":
        with st.spinner("시뮬레이션 진행 중..."):
            backtest_results = run_indicator_backtests(df)
            
            if not backtest_results:
                st.error("백테스트를 위한 데이터가 부족합니다.")
            else:
                # Separate Buy & Hold from the active trading strategies
                backtest_results.pop("이동평균선 (SMA)", None)
                bh_data = backtest_results.pop("단순 보유 (Buy & Hold)", {"return": 0, "mdd": 0})
                bh_return = bh_data.get("return", 0)
                bh_mdd = bh_data.get("mdd", 0)
                
                # Find the best strategy among active ones
                best_strategy = max(backtest_results, key=lambda k: backtest_results[k]["return"])
                best_return = backtest_results[best_strategy]["return"]
                best_mdd = backtest_results[best_strategy].get("mdd", 0)
                
                diff = best_return - bh_return
                diff_text = f"{diff:+.2f}%p {'우세' if diff > 0 else '열세'}"
                
                st.success(f"**최우수 전략 (Best Strategy): 👑 {best_strategy}** (수익 {best_return:.2f}% | MDD {best_mdd:.1f}%) &nbsp; | &nbsp; 단순 보유 벤치마크: {bh_return:+.2f}% (MDD {bh_mdd:.1f}%) &nbsp;👉&nbsp; **{diff_text}**")
                
                # Prepare data for Plotly Bar Chart (Only active strategies)
                strategies = list(backtest_results.keys())
                returns = [backtest_results[s]["return"] for s in strategies]
                mdds = [backtest_results[s].get("mdd", 0) for s in strategies]
                
                # Colors: Green for positive, Red for negative, highlight Best, Purple for Smart Strategies
                bar_colors = []
                for s, r in zip(strategies, returns):
                    if s == best_strategy:
                        bar_colors.append("#38bdf8") # Highlight best with blue/cyan
                    elif "💡" in s or "💎" in s:
                        bar_colors.append("#a855f7" if r >= 0 else "#d8b4fe") # Purple for smart strategies
                    elif r >= 0:
                        bar_colors.append("#10b981") # Green
                    else:
                        bar_colors.append("#ef4444") # Red
                        
                fig_bt = go.Figure(data=[go.Bar(
                    x=strategies, 
                    y=returns,
                    text=[f"{r:+.2f}%<br>(MDD {m:.1f}%)" for r, m in zip(returns, mdds)],
                    textposition='auto',
                    marker_color=bar_colors,
                    name="전략 수익률"
                )])
                
                # Add Buy & Hold as a benchmark horizontal line
                fig_bt.add_hline(
                    y=bh_return, 
                    line_dash="dash", 
                    line_color="#f59e0b", # Amber/Orange color for benchmark
                    annotation_text=f"단순 보유 (Buy & Hold) 벤치마크: {bh_return:+.2f}% (MDD {bh_mdd:.1f}%)", 
                    annotation_position="top right",
                    annotation_font_color="#f59e0b"
                )
                
                fig_bt.update_layout(
                    title="지표별 시뮬레이션 누적 수익률 비교 (vs 단순 보유)",
                    template="plotly_dark",
                    paper_bgcolor='#0d0f14',
                    plot_bgcolor='#0d0f14',
                    yaxis_title="누적 수익률 (%)",
                    margin=dict(t=50, b=40, l=40, r=40),
                    height=400,
                    showlegend=False
                )
                
                st.plotly_chart(fig_bt, use_container_width=True)
                
                # ----------------- TRADE HISTORY CHART -----------------
                st.markdown("---")
                st.markdown("### 🔍 전략별 상세 매매 내역 보기")
                
                # Add Buy & Hold back for inspection
                backtest_results["단순 보유 (Buy & Hold)"] = bh_data
                all_strats = list(backtest_results.keys())
                
                # Default to the best strategy
                selected_strat = st.selectbox("타점을 확인하고 싶은 전략을 선택하세요:", all_strats, index=all_strats.index(best_strategy) if best_strategy in all_strats else 0)
                
                strat_data = backtest_results[selected_strat]
                st.info(f"**📖 전략 설명:** {strat_data.get('desc', '설명이 없습니다.')}")
                
                trades = strat_data.get("trades", [])
                
                fig_trades = go.Figure()
                
                # Add Price line
                fig_trades.add_trace(go.Scatter(
                    x=df['Date'], y=df['Close'],
                    mode='lines',
                    name='종가(Close)',
                    line=dict(color='#94a3b8', width=2)
                ))
                
                # Add Buy markers
                buys = [t for t in trades if t['Action'] == 'BUY']
                if buys:
                    fig_trades.add_trace(go.Scatter(
                        x=[t['Date'] for t in buys],
                        y=[t['Price'] for t in buys],
                        mode='markers',
                        name='매수 (BUY)',
                        marker=dict(symbol='triangle-up', size=14, color='#10b981', line=dict(width=1, color='white')),
                        text=[f"{t.get('Reason', '조건 만족')}<br>단가: {t['Price']:.2f}" for t in buys],
                        hoverinfo="x+text"
                    ))
                    
                # Add Sell markers
                sells = [t for t in trades if t['Action'] == 'SELL']
                if sells:
                    fig_trades.add_trace(go.Scatter(
                        x=[t['Date'] for t in sells],
                        y=[t['Price'] for t in sells],
                        mode='markers',
                        name='매도 (SELL)',
                        marker=dict(symbol='triangle-down', size=14, color='#ef4444', line=dict(width=1, color='white')),
                        text=[f"{t.get('Reason', '조건 만족')}<br>단가: {t['Price']:.2f}" for t in sells],
                        hoverinfo="x+text"
                    ))
                    
                fig_trades.update_layout(
                    title=f"{selected_strat} - 과거 매매 타점 시각화",
                    template="plotly_dark",
                    paper_bgcolor='#0d0f14',
                    plot_bgcolor='#0d0f14',
                    yaxis_title="주가",
                    xaxis_title="날짜",
                    margin=dict(t=50, b=40, l=40, r=40),
                    height=450,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                
                st.plotly_chart(fig_trades, use_container_width=True)
                
                if trades:
                    with st.expander("매매 내역 상세 표 (Table)"):
                        trades_df = pd.DataFrame(trades)
                        if not trades_df.empty:
                            trades_df = trades_df[['Date', 'Action', 'Price', 'Shares', 'Reason']]
                            st.dataframe(trades_df, use_container_width=True)
                else:
                    st.write("해당 기간 동안 발생한 매매 내역이 없습니다.")


with tab2:
    st.markdown("### 🏆 시가총액 Top 50 종목 랭킹 (5대 지표 통합 점수)")
    st.markdown("<p style='color:#94a3b8; font-size:14px;'>선택한 시장의 시가총액 상위 50개 종목을 대상으로 5가지 보조지표(이동평균선, MACD, 퀀트모멘텀, EMA교차, 듀얼모멘텀) 점수를 종합하여 가장 추세가 좋은 종목을 찾습니다.</p>", unsafe_allow_html=True)
    
    kr_tab, us_tab, kr_etf_tab, us_etf_tab = st.tabs(["🇰🇷 한국 주식", "🇺🇸 미국 주식", "🇰🇷 한국 ETF", "🇺🇸 미국 ETF"])
    
    def render_ranking_tab(market_key, label):
        cache_file = f"ranking_cache_{market_key}.pkl"
        
        # Load from file if session state is empty (e.g. after reload)
        if f'ranking_result_{market_key}' not in st.session_state:
            try:
                import os
                if os.path.exists(cache_file):
                    st.session_state[f'ranking_result_{market_key}'] = pd.read_pickle(cache_file)
            except Exception:
                pass
                
        # Generate new data button
        if st.button(f"🚀 {label} 랭킹 분석 실행", use_container_width=True, type="primary"):
            spinner_msg = f"{label} 국내 주식형 종목(약 400개) 데이터를 수집하고 분석 중입니다... (1~2분 소요)" if market_key == "KR_ETF" else f"{label} 상위 50개 종목 데이터를 수집하고 5대 지표를 분석 중입니다... (약 10~20초 소요)"
            with st.spinner(spinner_msg):
                ranking_df = rank_stocks(market_key)
                
                if ranking_df.empty:
                    st.error("데이터를 가져오는 중 오류가 발생했습니다.")
                else:
                    st.session_state[f'ranking_result_{market_key}'] = ranking_df
                    # 파일로 저장하여 새로고침 시에도 유지
                    try:
                        ranking_df.to_pickle(cache_file)
                    except Exception:
                        pass
        
        if f'ranking_result_{market_key}' in st.session_state and not st.session_state[f'ranking_result_{market_key}'].empty:
            ranking_df = st.session_state[f'ranking_result_{market_key}']
            
            st.success(f"분석 완료! 총 {len(ranking_df)}개 종목의 랭킹입니다. ({label})")
            
            display_df = ranking_df.copy()
            if market_key.startswith("KR"):
                display_df['현재가'] = display_df['현재가'].apply(lambda x: f"{x:,.0f}원")
            else:
                display_df['현재가'] = display_df['현재가'].apply(lambda x: f"${x:,.2f}")
            display_df['등락률(%)'] = display_df['등락률(%)'].apply(lambda x: f"{x:+.2f}%")
            
            st.dataframe(
                display_df,
                use_container_width=True,
                hide_index=True,
                on_select="rerun",
                selection_mode="single-row",
                key=f"ranking_table_{market_key}",
                column_config={
                    "순위": st.column_config.NumberColumn("순위", help="총점 기준 순위", width="small"),
                    "총점": st.column_config.ProgressColumn("총점 (Max 500)", help="5개 지표 점수의 합", format="%d", min_value=0, max_value=500),
                    "SMA": st.column_config.NumberColumn("SMA", help="이동평균선 점수", format="%d"),
                    "MACD": st.column_config.NumberColumn("MACD", help="MACD 점수", format="%d"),
                    "퀀트모멘텀": st.column_config.NumberColumn("퀀트모멘텀", help="퀀트모멘텀 점수", format="%d"),
                    "EMA크로스": st.column_config.NumberColumn("EMA크로스", help="EMA크로스 점수", format="%d"),
                    "듀얼모멘텀": st.column_config.NumberColumn("듀얼모멘텀", help="듀얼모멘텀 점수", format="%d"),
                    "등락률(%)": st.column_config.TextColumn("등락률(%)"),
                }
            )

    with kr_tab:
        render_ranking_tab("KR", "한국 주식")
        
    with us_tab:
        render_ranking_tab("US", "미국 주식")
        
    with kr_etf_tab:
        render_ranking_tab("KR_ETF", "한국 ETF")
        
    with us_etf_tab:
        render_ranking_tab("US_ETF", "미국 ETF")
