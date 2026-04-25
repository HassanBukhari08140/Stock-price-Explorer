<<<<<<< HEAD
# Stock Price Explorer

An interactive stock analysis dashboard built with Python, Streamlit, and Plotly.

## Features

**Single stock tab**
- Candlestick and line charts for any ticker
- Technical indicators: SMA 20, SMA 50, EMA 20, RSI (14)
- Volume bars with green/red colour coding
- Side-by-side comparison of two tickers with price correlation score
- Raw data table with CSV download

**Portfolio tab**
- Enter multiple tickers and share counts
- Calculates current value, cost basis, gain/loss per holding
- Portfolio allocation pie chart
- Normalised performance chart (all stocks start at 100)
- Portfolio CSV export

**News feed tab**
- Latest headlines for any ticker via Yahoo Finance
- Publisher name and publish time shown per article
- Direct links to full articles

## Tech stack

- Python 3.10+
- [Streamlit](https://streamlit.io) — app framework
- [yfinance](https://github.com/ranaroussi/yfinance) — market data
- [Plotly](https://plotly.com/python/) — interactive charts
- [Pandas](https://pandas.pydata.org/) — data processing

## Run locally

```bash
pip install streamlit yfinance plotly pandas
streamlit run stock_explorer.py
```

## Deploy to Streamlit Cloud

1. Push this repo to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Set main file as `stock_explorer.py`
5. Click Deploy — live URL in ~2 minutes

## Author

Muhammad Fawad · [LinkedIn](https://www.linkedin.com/in/muhammadfawad-4730a4294)
=======
# Stock-price-Explorer
>>>>>>> cca446ad3178549b4363fa01e92b242efb908c86
