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
from src.data_loader import get_kr_stock_data, get_kr_stock_info
from src.data_loader import get_us_stock_data, get_us_stock_info
from src.analyzers.indicators import add_all_indicators
from src.analyzers.trend import analyze_trend
from src.backtester.simple import run_indicator_backtests

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
    
    /* Star Button Customization */
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) > div[data-testid="column"]:nth-of-type(1) {
        position: relative;
    }
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) > div[data-testid="column"]:nth-of-type(1) button {
        position: absolute !important;
        top: 20px !important;
        right: 20px !important;
        background: transparent !important;
        border: none !important;
        box-shadow: none !important;
        color: #facc15 !important;
        font-size: 28px !important;
        padding: 0 !important;
        width: auto !important;
        min-height: 0 !important;
        height: auto !important;
        line-height: 1 !important;
        z-index: 999 !important;
    }
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) > div[data-testid="column"]:nth-of-type(1) button:hover {
        transform: scale(1.15);
        background: transparent !important;
    }
    div[data-testid="stHorizontalBlock"]:nth-of-type(1) > div[data-testid="column"]:nth-of-type(1) button:focus {
        background: transparent !important;
        color: #facc15 !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------- APP HEADER -----------------
st.markdown("<h1 class='agent-title'>⚡ AI 기술적 추세 분석 대시보드</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: #94a3b8; font-size: 16px; margin-top: -12px;'>한 종목에 대한 다중 지표(이동평균, MACD, RSI, 볼린저밴드)를 활용한 입체적 추세 진단 시스템</p>", unsafe_allow_html=True)
st.markdown("---")

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
    market = st.selectbox("시장 (Market)", ["KR (한국)", "US (미국)"], index=0)
    is_kr = market.startswith("KR")
    market_key = "KR" if is_kr else "US"
    
    # 시장별 즐겨찾기 목록 구성
    FAVORITES = {"🌟 직접 입력": ""}
    FAVORITES.update(user_favorites[market_key])
    
    fav_selection = st.selectbox("⭐ 즐겨찾기 종목", list(FAVORITES.keys()), index=1 if len(FAVORITES) > 1 else 0)
    
    if fav_selection == "🌟 직접 입력":
        default_ticker = "000660" if is_kr else "AAPL"
        ticker_input = st.text_input("종목 코드 (Ticker) 직접 입력", value=default_ticker).strip().upper()
    else:
        ticker_input = FAVORITES[fav_selection]
        st.text_input("선택된 종목 코드", value=ticker_input, disabled=True)
    
    period_options = {"3개월": 90, "6개월": 180, "1년": 365, "3년": 1095}
    selected_period = st.selectbox("조회 기간", list(period_options.keys()), index=1)
    days_to_fetch = period_options[selected_period]
    
    st.markdown("---")
    st.markdown("💡 **Tip:**\n- 한국 종목은 `000660`(SK하이닉스), `005930`(삼성전자) 등의 숫자를 입력하세요.\n- 미국 종목은 `AAPL`, `TSLA`, `NVDA` 등 영문 티커를 입력하세요.")

# ----------------- DATA FETCHING -----------------
if not ticker_input:
    st.warning("👈 왼쪽 사이드바에서 분석할 종목 코드를 입력해주세요.")
    st.stop()

with st.spinner(f"'{ticker_input}' 종목 데이터 및 기술적 지표 계산 중..."):
    start_date = (datetime.now() - timedelta(days=days_to_fetch)).strftime('%Y-%m-%d')
    
    if is_kr:
        info = get_kr_stock_info(ticker_input)
        df = get_kr_stock_data(ticker_input, start_date=start_date)
        price_unit = "원"
        price_format = f"{info['current_price']:,.0f}"
    else:
        info = get_us_stock_info(ticker_input)
        df = get_us_stock_data(ticker_input, start_date=start_date)
        price_unit = "$"
        price_format = f"{info['current_price']:,.2f}"

if df.empty or len(df) < 20:
    st.error(f"⚠️ '{ticker_input}'에 대한 충분한 시세 데이터를 불러오지 못했습니다. 종목 코드와 시장 구분을 다시 확인해주세요.")
    st.stop()

# ----------------- INDICATOR CALCULATION -----------------
df = add_all_indicators(df)
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
            
    btn_label = "⭐" if is_favorite else "☆"
    if st.button(btn_label, key="fav_star_btn", help="즐겨찾기 추가/해제"):
        if is_favorite:
            del user_favorites[market_key][fav_key]
        else:
            user_favorites[market_key][info['name']] = ticker_input
        save_favorites(user_favorites)
        st.rerun()

    st.markdown(f"""
    <div class='metric-card' style='margin-top: -65px; position: relative; z-index: 1;'>
        <div class='metric-title'>분석 대상 종목</div>
        <div class='metric-value' style='color: #818cf8; font-size: 20px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>{info['name']}</div>
        <div class='metric-sub' style='color: #64748b;'>{ticker_input} ({'KRX' if is_kr else 'US'})</div>
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

# ----------------- INDICATOR CALCULATION -----------------
df = add_all_indicators(df)
latest = df.iloc[-1]
trend_result = analyze_trend(df)

# Run backtests to get last trade info
backtest_results = run_indicator_backtests(df)

trade_info_map = {}
for key, name in [('sma', '이동평균선 (SMA)'), ('macd', 'MACD'), 
                  ('quant_momentum', '💎 퀀트 모멘텀 (알파 추구형)'), 
                  ('ema_cross', '💎 ⚡ 골든크로스 EMA (5/20)'), 
                  ('dual_momentum', '💎 🛡️ 듀얼 모멘텀')]:
    if backtest_results and name in backtest_results and backtest_results[name]['trades']:
        last_trade = backtest_results[name]['trades'][-1]
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
<div>
<div style='color: #94a3b8; font-size: 13px; font-weight: 600; margin-bottom: 2px;'>{title}</div>
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

st.markdown("<br>", unsafe_allow_html=True)

# ----------------- AI SMART STRATEGIES PANELS -----------------
st.markdown("### 💎 초과 수익 달성형 (알파) 지표 상태")
st.markdown("<p style='color:#94a3b8; font-size:14px;'>Buy & Hold 벤치마크를 넘어서기 위해 설계된 공격적 추세 추종 전략들의 현재 시그널입니다.</p>", unsafe_allow_html=True)

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

fig = make_subplots(
    rows=2, cols=1, 
    shared_xaxes=True, 
    vertical_spacing=0.05, 
    row_heights=[0.7, 0.3],
    subplot_titles=(
        f"📊 주가 추세 및 이동평균선 (SMA 20/50/120)", 
        "📈 MACD 오실레이터"
    )
)

# 1. Candlestick & Moving Averages
fig.add_trace(go.Candlestick(
    x=df['Date'], open=df['Open'], high=df['High'],
    low=df['Low'], close=df['Close'],
    name="Candle",
    increasing_line_color=inc_color, decreasing_line_color=dec_color
), row=1, col=1)

fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_20'], name="SMA 20", line=dict(color="#38bdf8", width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_50'], name="SMA 50", line=dict(color="#f59e0b", width=1.5)), row=1, col=1)
fig.add_trace(go.Scatter(x=df['Date'], y=df['SMA_120'], name="SMA 120", line=dict(color="#ec4899", width=1.5)), row=1, col=1)

# Bollinger Bands Outline (Light grey fill)
fig.add_trace(go.Scatter(
    x=df['Date'].tolist() + df['Date'].tolist()[::-1],
    y=df['BB_Upper'].tolist() + df['BB_Lower'].tolist()[::-1],
    fill='toself',
    fillcolor='rgba(255, 255, 255, 0.05)',
    line=dict(color='rgba(255,255,255,0)'),
    hoverinfo="skip",
    name="Bollinger Bands"
), row=1, col=1)


# 2. MACD
colors_macd = ['#10b981' if val >= 0 else '#ef4444' for val in df['MACD_Hist']]
fig.add_trace(go.Bar(x=df['Date'], y=df['MACD_Hist'], marker_color=colors_macd, name="MACD Hist"), row=2, col=1)
fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD'], line=dict(color="#38bdf8", width=1.5), name="MACD"), row=2, col=1)
fig.add_trace(go.Scatter(x=df['Date'], y=df['MACD_Signal'], line=dict(color="#f59e0b", width=1.5), name="Signal"), row=2, col=1)


fig.update_layout(
    template="plotly_dark",
    height=700,
    xaxis_rangeslider_visible=False,
    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    margin=dict(l=40, r=40, t=50, b=40),
    paper_bgcolor='#0d0f14',
    plot_bgcolor='#0d0f14'
)

# Update subplot titles formatting
for annotation in fig['layout']['annotations']: 
    annotation['font'] = dict(size=14, color="#94a3b8")

st.plotly_chart(fig, use_container_width=True)

# ----------------- DETAILED METRICS TABLE -----------------
st.markdown("### 📋 최근 5일 기술적 지표 상세 내역")
recent_df = df.tail(5)[['Date', 'Close', 'SMA_20', 'SMA_50', 'MACD', 'MACD_Signal', 'MACD_Hist']]
recent_df['Date'] = pd.to_datetime(recent_df['Date']).dt.strftime('%Y-%m-%d')
recent_df = recent_df.sort_values(by='Date', ascending=False).reset_index(drop=True)

# Format numerical columns
format_dict = {
    'Close': '{:,.2f}' if not is_kr else '{:,.0f}',
    'SMA_20': '{:,.2f}',
    'SMA_50': '{:,.2f}',
    'MACD': '{:.3f}',
    'MACD_Signal': '{:.3f}',
    'MACD_Hist': '{:.3f}'
}

st.dataframe(
    recent_df.style.format(format_dict).map(
        lambda x: 'color: #ef4444' if isinstance(x, (int, float)) and x < 0 else ('color: #10b981' if isinstance(x, (int, float)) and x > 0 else ''),
        subset=['MACD_Hist']
    ), use_container_width=True)

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
