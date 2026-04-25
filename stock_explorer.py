import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime

st.set_page_config(
    page_title="StockExplorer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── Dark professional theme ───────────────────────────────────────
st.markdown("""
<style>
  /* Global dark background */
  .stApp { background-color: #0f1117; }
  section[data-testid="stSidebar"] { background-color: #1a1d27; border-right: 1px solid #262936; }

  /* Main text colors */
  .stApp, .stMarkdown, p, label { color: #e0e0e0 !important; }
  h1, h2, h3 { color: #ffffff !important; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: #1a1d27;
    border: 1px solid #262936;
    border-radius: 10px;
    padding: 14px 16px;
  }
  [data-testid="metric-container"] label { color: #888 !important; font-size: 12px !important; text-transform: uppercase; letter-spacing: 0.05em; }
  [data-testid="metric-container"] [data-testid="stMetricValue"] { color: #ffffff !important; font-size: 22px !important; }
  [data-testid="metric-container"] [data-testid="stMetricDelta"] { font-size: 13px !important; }

  /* Tabs */
  .stTabs [data-baseweb="tab-list"] { background: #1a1d27; border-radius: 10px; padding: 4px; gap: 4px; }
  .stTabs [data-baseweb="tab"] { background: transparent; color: #888; border-radius: 8px; font-size: 13px; }
  .stTabs [aria-selected="true"] { background: #262936 !important; color: #fff !important; }

  /* Inputs */
  .stTextInput input, .stSelectbox select, .stTextArea textarea {
    background: #1a1d27 !important;
    border: 1px solid #262936 !important;
    color: #e0e0e0 !important;
    border-radius: 8px !important;
  }

  /* Buttons */
  .stButton button {
    background: #1D9E75 !important;
    color: #fff !important;
    border: none !important;
    border-radius: 8px !important;
    font-weight: 500 !important;
  }
  .stButton button:hover { background: #0F6E56 !important; }

  /* Divider */
  hr { border-color: #262936 !important; }

  /* Dataframe */
  .stDataFrame { border: 1px solid #262936 !important; border-radius: 8px !important; }

  /* Expander */
  .streamlit-expanderHeader { background: #1a1d27 !important; color: #e0e0e0 !important; border-radius: 8px !important; }

  /* Radio & checkbox */
  .stRadio label, .stCheckbox label { color: #aaa !important; }

  /* Sidebar header */
  .stSidebar h2, .stSidebar h3 { color: #fff !important; }

  /* Progress bar */
  .stProgress > div > div { background: #1D9E75 !important; }

  /* Info box */
  .stAlert { background: #1a1d27 !important; border: 1px solid #262936 !important; color: #e0e0e0 !important; border-radius: 8px !important; }
</style>
""", unsafe_allow_html=True)

# ── Header ────────────────────────────────────────────────────────
st.markdown("""
<div style="display:flex; align-items:center; gap:10px; margin-bottom:8px;">
  <div style="width:10px;height:10px;background:#1D9E75;border-radius:50%;"></div>
  <span style="font-size:22px;font-weight:600;color:#fff;">StockExplorer</span>
  <span style="font-size:12px;color:#555;margin-left:4px;">live market data</span>
</div>
""", unsafe_allow_html=True)

# ── Tabs ──────────────────────────────────────────────────────────
tab_single, tab_portfolio, tab_news = st.tabs(
    ["Single stock", "Portfolio", "News feed"]
)

# ── Shared helpers ────────────────────────────────────────────────
@st.cache_data(ttl=300)
def fetch(ticker, period):
    try:
        df = yf.download(
            ticker,
            period=period,
            auto_adjust=True,
            progress=False,
            group_by="column"   # ← yeh add karo
        )
        if df is None or df.empty:
            return None
        # MultiIndex columns flatten karo
        if isinstance(df.columns, pd.MultiIndex):
            df.columns = df.columns.get_level_values(0)
        else:
            df.columns = [c[0] if isinstance(c, tuple) else c
                          for c in df.columns]
        df.index = pd.to_datetime(df.index)
        # duplicate columns hata do (agar same name repeat ho)
        df = df.loc[:, ~df.columns.duplicated()]
        return df
    except Exception as e:
        st.warning(f"Error fetching {ticker}: {e}")
        return None
def add_indicators(df):
    df = df.copy()
    df["SMA20"] = df["Close"].rolling(20).mean()
    df["SMA50"] = df["Close"].rolling(50).mean()
    df["EMA20"] = df["Close"].ewm(span=20, adjust=False).mean()
    delta = df["Close"].diff()
    gain  = delta.clip(lower=0).rolling(14).mean()
    loss  = (-delta.clip(upper=0)).rolling(14).mean()
    rs    = gain / loss.replace(0, 1e-9)
    df["RSI"] = 100 - (100 / (1 + rs))
    return df

@st.cache_data(ttl=600)
def fetch_news(ticker):
    try:
        return yf.Ticker(ticker).news or []
    except Exception:
        return []

DARK_LAYOUT = dict(
    plot_bgcolor="#1a1d27",
    paper_bgcolor="#1a1d27",
    font_color="#e0e0e0",
    xaxis=dict(gridcolor="#262936", showgrid=True),
    yaxis=dict(gridcolor="#262936", showgrid=True),
    margin=dict(l=0, r=0, t=10, b=0),
    hovermode="x unified",
    hoverlabel=dict(bgcolor="#262936", font_color="#fff", bordercolor="#444"),
    legend=dict(orientation="h", yanchor="bottom", y=1.02,
                xanchor="left", x=0, font_color="#aaa"),
)

period_map = {
    "1 month": "1mo", "3 months": "3mo", "6 months": "6mo",
    "1 year": "1y",   "2 years": "2y",   "5 years": "5y",
}


# ════════════════════════════════════════════════════════════════════
# TAB 1 — SINGLE STOCK
# ════════════════════════════════════════════════════════════════════
with tab_single:
    with st.sidebar:
        st.markdown("### Settings")
        ticker1 = st.text_input("Ticker symbol", value="AAPL").upper().strip()
        ticker2 = st.text_input("Compare with (optional)", value="").upper().strip()
        period_label = st.selectbox("Time period", list(period_map.keys()), index=3)
        period = period_map[period_label]
        chart_type = st.radio("Chart type", ["Candlestick", "Line"])
        st.markdown("---")
        st.markdown("### Indicators")
        show_sma20  = st.checkbox("SMA 20",   value=True)
        show_sma50  = st.checkbox("SMA 50",   value=True)
        show_ema20  = st.checkbox("EMA 20",   value=False)
        show_volume = st.checkbox("Volume",   value=True)
        show_rsi    = st.checkbox("RSI (14)", value=True)

    df = fetch(ticker1, period)
    if df is None:
        st.error(f"Could not fetch data for **{ticker1}**. Check the ticker symbol.")
        st.stop()
    df = add_indicators(df)

    df2 = None
    if ticker2:
        df2 = fetch(ticker2, period)
        if df2 is not None:
            df2 = add_indicators(df2)

    latest     = float(df["Close"].iloc[-1])
    prev       = float(df["Close"].iloc[-2])
    change     = latest - prev
    change_pct = (change / prev) * 100
    high_52w   = float(df["High"].max())
    low_52w    = float(df["Low"].min())
    avg_vol    = int(df["Volume"].mean())

    # Ticker + price header
    delta_color = "#1D9E75" if change >= 0 else "#D85A30"
    arrow = "▲" if change >= 0 else "▼"
    st.markdown(f"""
    <div style="display:flex;align-items:baseline;gap:16px;margin-bottom:16px;">
      <span style="font-size:28px;font-weight:700;color:#fff;">{ticker1}</span>
      <span style="font-size:32px;font-weight:600;color:#fff;">${latest:.2f}</span>
      <span style="font-size:14px;color:{delta_color};background:rgba(29,158,117,0.1);
             padding:4px 12px;border-radius:20px;">{arrow} {abs(change):.2f} ({abs(change_pct):.2f}%)</span>
    </div>
    """, unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("52w high",   f"${high_52w:.2f}")
    c2.metric("52w low",    f"${low_52w:.2f}")
    c3.metric("Avg volume", f"{avg_vol:,}")
    c4.metric("Period",     period_label)

    st.markdown("---")

    # Build chart
    row_count   = 1
    row_vol = row_rsi = None
    row_heights = [0.6]
    if show_volume:
        row_count += 1; row_vol = row_count; row_heights.append(0.2)
    if show_rsi:
        row_count += 1; row_rsi = row_count; row_heights.append(0.2)

    fig = make_subplots(rows=row_count, cols=1, shared_xaxes=True,
                        vertical_spacing=0.03, row_heights=row_heights)

    if chart_type == "Candlestick":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"], name=ticker1,
            increasing_line_color="#1D9E75", decreasing_line_color="#D85A30",
            increasing_fillcolor="#1D9E75", decreasing_fillcolor="#D85A30",
        ), row=1, col=1)
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], name=ticker1,
            line=dict(color="#1D9E75", width=2),
            fill="tozeroy", fillcolor="rgba(29,158,117,0.08)"
        ), row=1, col=1)

    if df2 is not None:
        norm2 = df2["Close"] / df2["Close"].iloc[0] * df["Close"].iloc[0]
        fig.add_trace(go.Scatter(
            x=df2.index, y=norm2, name=f"{ticker2} (norm.)",
            line=dict(color="#7F77DD", width=1.5, dash="dot")
        ), row=1, col=1)

    if show_sma20:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA20"], name="SMA 20",
            line=dict(color="#EF9F27", width=1.2)), row=1, col=1)
    if show_sma50:
        fig.add_trace(go.Scatter(x=df.index, y=df["SMA50"], name="SMA 50",
            line=dict(color="#D4537E", width=1.2)), row=1, col=1)
    if show_ema20:
        fig.add_trace(go.Scatter(x=df.index, y=df["EMA20"], name="EMA 20",
            line=dict(color="#5DCAA5", width=1.2, dash="dash")), row=1, col=1)

    if show_volume and row_vol:
        colors = ["#1D9E75" if c >= o else "#D85A30"
                  for c, o in zip(df["Close"], df["Open"])]
        fig.add_trace(go.Bar(x=df.index, y=df["Volume"], name="Volume",
            marker_color=colors, opacity=0.6), row=row_vol, col=1)
        fig.update_yaxes(title_text="Volume", title_font_color="#666",
                         tickfont_color="#666", row=row_vol, col=1)

    if show_rsi and row_rsi:
        fig.add_trace(go.Scatter(x=df.index, y=df["RSI"], name="RSI (14)",
            line=dict(color="#7F77DD", width=1.5)), row=row_rsi, col=1)
        fig.add_hrect(y0=70, y1=100, fillcolor="rgba(216,90,48,0.05)",
                      line_width=0, row=row_rsi, col=1)
        fig.add_hrect(y0=0, y1=30, fillcolor="rgba(29,158,117,0.05)",
                      line_width=0, row=row_rsi, col=1)
        fig.add_hline(y=70, line_dash="dash", line_color="#D85A30",
                      line_width=0.8, row=row_rsi, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="#1D9E75",
                      line_width=0.8, row=row_rsi, col=1)
        fig.update_yaxes(title_text="RSI", range=[0, 100],
                         title_font_color="#666", tickfont_color="#666",
                         row=row_rsi, col=1)

    fig.update_layout(height=640, xaxis_rangeslider_visible=False, **DARK_LAYOUT)
    fig.update_xaxes(gridcolor="#262936", tickfont_color="#666")
    fig.update_yaxes(gridcolor="#262936", tickfont_color="#666")
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("View raw data"):
        cols = ["Open", "High", "Low", "Close", "Volume"]
        st.dataframe(df[cols].sort_index(ascending=False).round(2),
                     use_container_width=True)
        st.download_button("Download CSV", df[cols].to_csv(),
                           f"{ticker1}_{period}.csv", "text/csv")

    if df2 is not None:
        idx = df.index.intersection(df2.index)
        if len(idx) > 10:
            corr = df.loc[idx, "Close"].corr(df2.loc[idx, "Close"])
            st.info(f"Price correlation — **{ticker1}** vs **{ticker2}**: **{corr:.3f}**")


# ════════════════════════════════════════════════════════════════════
# TAB 2 — PORTFOLIO
# ════════════════════════════════════════════════════════════════════
with tab_portfolio:
    st.markdown("### Portfolio tracker")
    st.caption("Enter your holdings below. Format: TICKER,SHARES — one per line.")

    raw_input = st.text_area(
        "Your holdings",
        value="AAPL,10\nMSFT,5\nGOOGL,3\nTSLA,8\nNVDA,6",
        height=160
    )
    port_period = period_map[st.selectbox("Performance period",
                             list(period_map.keys()), index=3, key="pp")]

    if st.button("Calculate portfolio"):
        holdings, errors = [], []
        for line in raw_input.strip().split("\n"):
            line = line.strip()
            if not line: continue
            parts = line.split(",")
            if len(parts) != 2:
                errors.append(f"Bad format: {line}"); continue
            tick = parts[0].strip().upper()
            try: shares = float(parts[1].strip())
            except: errors.append(f"Invalid shares: {tick}"); continue
            holdings.append((tick, shares))

        for e in errors: st.warning(e)

        if holdings:
            rows, price_hist = [], {}
            prog = st.progress(0, text="Fetching data…")
            for i, (tick, shares) in enumerate(holdings):
                data = fetch(tick, port_period)
                prog.progress((i+1)/len(holdings), text=f"Loading {tick}…")
                if data is None: st.warning(f"Skipped {tick}"); continue
                price_hist[tick] = data["Close"]
                lp = float(data["Close"].iloc[-1])
                op = float(data["Close"].iloc[0])
                val = lp * shares; cost = op * shares
                gain = val - cost
                rows.append({"Ticker": tick, "Shares": shares,
                             "Price": round(lp,2), "Value ($)": round(val,2),
                             "Cost ($)": round(cost,2), "Gain ($)": round(gain,2),
                             "Gain (%)": round((gain/cost)*100 if cost else 0, 2)})
            prog.empty()

            if rows:
                port_df = pd.DataFrame(rows)
                tv = port_df["Value ($)"].sum()
                tc = port_df["Cost ($)"].sum()
                tg = tv - tc
                port_df["Weight (%)"] = (port_df["Value ($)"] / tv * 100).round(2)

                m1,m2,m3,m4 = st.columns(4)
                m1.metric("Total value", f"${tv:,.2f}")
                m2.metric("Total cost",  f"${tc:,.2f}")
                m3.metric("Total gain",  f"${tg:,.2f}", f"{(tg/tc*100):.2f}%")
                m4.metric("Holdings",    len(rows))

                st.markdown("---")
                cl, cr = st.columns(2)
                with cl:
                    st.markdown("**Holdings breakdown**")
                    st.dataframe(port_df[["Ticker","Shares","Price",
                                          "Value ($)","Gain (%)","Weight (%)"]],
                                 use_container_width=True, hide_index=True)
                with cr:
                    pie = px.pie(port_df, values="Value ($)", names="Ticker",
                                 color_discrete_sequence=["#1D9E75","#378ADD",
                                 "#EF9F27","#D4537E","#7F77DD","#5DCAA5"])
                    pie.update_layout(paper_bgcolor="#1a1d27",
                                      plot_bgcolor="#1a1d27",
                                      font_color="#e0e0e0",
                                      margin=dict(l=0,r=0,t=30,b=0))
                    pie.update_traces(textfont_color="#fff")
                    st.plotly_chart(pie, use_container_width=True)

                st.markdown("**Normalised performance** — all start at 100")
                pf = go.Figure()
                colors_list = ["#1D9E75","#378ADD","#EF9F27",
                               "#D4537E","#7F77DD","#5DCAA5","#D85A30"]
                for i, (tick, series) in enumerate(price_hist.items()):
                    norm = series / series.iloc[0] * 100
                    pf.add_trace(go.Scatter(x=norm.index, y=norm.values,
                        name=tick, mode="lines",
                        line=dict(width=2, color=colors_list[i % len(colors_list)])))
                pf.add_hline(y=100, line_dash="dash",
                             line_color="#444", line_width=1)
                pf.update_layout(height=360, **DARK_LAYOUT)
                pf.update_xaxes(gridcolor="#262936", tickfont_color="#666")
                pf.update_yaxes(gridcolor="#262936", tickfont_color="#666")
                st.plotly_chart(pf, use_container_width=True)

                st.download_button("Download CSV", port_df.to_csv(index=False),
                                   "portfolio.csv", "text/csv")


# ════════════════════════════════════════════════════════════════════
# TAB 3 — NEWS FEED
# ════════════════════════════════════════════════════════════════════
with tab_news:
    st.markdown("### Latest news")
    st.caption("Real-time headlines via Yahoo Finance.")

    news_raw = st.text_input("Tickers (comma separated)", value="AAPL, MSFT, TSLA")
    news_tickers = [t.strip().upper() for t in news_raw.split(",") if t.strip()]

    if st.button("Fetch news"):
        for tick in news_tickers:
            st.markdown(f"#### {tick}")
            articles = fetch_news(tick)
            if not articles:
                st.caption("No news found."); continue
            for art in articles[:6]:
                title     = art.get("title", "No title")
                link      = art.get("link", "#")
                publisher = art.get("publisher", "")
                pt        = art.get("providerPublishTime")
                pub_str   = datetime.fromtimestamp(pt).strftime("%d %b %Y, %H:%M") if pt else ""
                st.markdown(
                    f"**[{title}]({link})**  \n"
                    f"<span style='font-size:12px;color:#666;'>"
                    f"{publisher} · {pub_str}</span>",
                    unsafe_allow_html=True
                )
                st.markdown("---")
