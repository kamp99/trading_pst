import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta
import plotly.graph_objects as go
import requests
from bs4 import BeautifulSoup

def get_stock_data(ticker):
    df = yf.download(ticker, period="3mo", interval="1d")
    df["RSI"] = ta.rsi(df['Close'], length=14)
    df["MACD"], df["MACD_signal"] = ta.macd(df['Close'])[['MACD_12_26_9', 'MACDs_12_26_9']]
    df["SMA_20"] = df['Close'].rolling(20).mean()
    return df

def get_fundamentals(ticker):
    url = f"https://finviz.com/quote.ashx?t={ticker}"
    headers = {'User-Agent': 'Mozilla/5.0'}
    soup = BeautifulSoup(requests.get(url, headers=headers).content, 'html.parser')
    table = soup.find_all('table', class_='snapshot-table2')[0]
    data = {tds[0].text: tds[1].text for tds in zip(*[iter(table.find_all('td'))]*2)}
    return data

def plot_stock(df, ticker):
    fig = go.Figure()
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'],
        low=df['Low'], close=df['Close'], name='OHLC'
    ))
    fig.add_trace(go.Scatter(x=df.index, y=df['SMA_20'], mode='lines', name='SMA 20', line=dict(color='blue')))
    fig.update_layout(title=f'{ticker} Price & SMA', xaxis_title='Date', yaxis_title='Price')
    return fig

def plot_rsi(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['RSI'], mode='lines', name='RSI', line=dict(color='purple')))
    fig.update_layout(title='RSI', yaxis=dict(range=[0, 100]))
    return fig

def plot_macd(df):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD'], mode='lines', name='MACD', line=dict(color='green')))
    fig.add_trace(go.Scatter(x=df.index, y=df['MACD_signal'], mode='lines', name='Signal', line=dict(color='red')))
    fig.update_layout(title='MACD')
    return fig

# --- STREAMLIT UI ---
st.set_page_config(page_title="Swing Trade Dashboard", layout="wide")
st.title("📊 Swing Trade Screener Dashboard")

ticker = st.text_input("Enter a stock ticker (e.g., AAPL, TSLA)", value="AAPL")

if ticker:
    df = get_stock_data(ticker)
    fundamentals = get_fundamentals(ticker)

    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.plotly_chart(plot_stock(df, ticker), use_container_width=True)
        st.plotly_chart(plot_rsi(df), use_container_width=True)
        st.plotly_chart(plot_macd(df), use_container_width=True)

    with col2:
        st.subheader("🧠 Fundamentals")
        for key in ["Market Cap", "P/E", "EPS past 5Y", "Dividend %", "Debt/Eq", "ROE"]:
            if key in fundamentals:
                st.write(f"**{key}:** {fundamentals[key]}")

    st.download_button("Download Data to CSV", df.to_csv().encode(), file_name=f"{ticker}_data.csv")

