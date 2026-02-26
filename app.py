import os
import streamlit as st
import yfinance as yf
import plotly.graph_objects as go
from groq import Groq
from dotenv import load_dotenv
def plot_stock_chart(data, ticker):
    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=data.index,
        y=data["Close"],
        mode="lines",
        name="Close Price"
    ))

    fig.update_layout(
        title=f"{ticker} Stock Price",
        xaxis_title="Date",
        yaxis_title="Price (USD)",
        template="plotly_white"
    )

    st.plotly_chart(fig, use_container_width=True)
st.set_page_config(
    page_title="Finance AI Agent Pro",
    page_icon="💰",
    layout="wide"
)

load_dotenv()

client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.title("💰 Finance AI Agent Pro")

# ---------------- PORTFOLIO ANALYZER ----------------

def get_stock_price(symbol):
    stock = yf.Ticker(symbol)
    plot_stock_chart(data, ticker)
    data = stock.history(period="1d")
    if not data.empty:
        return data["Close"].iloc[-1]
    return None


def analyze_portfolio(portfolio_text):
    try:
        items = portfolio_text.split(",")
        total_value = 0
        breakdown = []

        for item in items:
            symbol, qty = item.strip().split(":")
            qty = float(qty)

            stock = yf.Ticker(symbol.strip())
            data = stock.history(period="1d")

            if data.empty:
                continue

            price = data["Close"].iloc[-1]
            value = price * qty
            total_value += value

            breakdown.append(
                f"{symbol.upper()} → Qty: {qty}, Price: ${price:.2f}, Value: ${value:.2f}"
            )

        return total_value, breakdown
    except Exception as e:
        return None, str(e)
        import feedparser

import requests

def get_stock_news(symbol):
    try:
        api_key = os.getenv("NEWS_API_KEY")
        url = (
    f"https://newsapi.org/v2/everything?"
    f"q={symbol}&language=en&sortBy=publishedAt&apiKey={api_key}"
)

        response = requests.get(url)
        data = response.json()

        headlines = []
        for article in data.get("articles", [])[:5]:
            headlines.append(article["title"])

        return headlines
    except Exception as e:
        return []


# ---------------- UI ----------------

st.subheader("📊 Portfolio Analyzer")

portfolio_input = st.text_input(
    "Enter portfolio (e.g., AAPL:10, TSLA:5)"
)

if st.button("Analyze Portfolio"):
    if portfolio_input:
        total, details = analyze_portfolio(portfolio_input)

        if total is None:
            st.error("Invalid format. Use: STOCK:QTY")
        else:
            st.success(f"💰 Total Portfolio Value: ${total:.2f}")
            st.subheader("📊 Stock Charts")

            items = portfolio_input.split(",")

            for item in items:
                symbol = item.split(":")[0].strip()
                stock = yf.Ticker(symbol)
                data = stock.history(period="1mo")

                if not data.empty:
                    plot_stock_chart(data, symbol)

            st.write("### 📋 Breakdown")
            for d in details:
                st.write(d)

            analysis_prompt = (
                f"Portfolio value is ${total:.2f}. Holdings: {details}. "
                "Give a brief investment insight."
            )

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a financial advisor."},
                    {"role": "user", "content": analysis_prompt},
                ],
            )

            st.write("### 🤖 AI Insight")
            st.write(response.choices[0].message.content)
            st.subheader("📰 Stock News Analyzer")

news_symbol = st.text_input("Enter stock for news (e.g., AAPL)")

if st.button("Get News"):
    if news_symbol:
        news_list = get_stock_news(news_symbol)

        if not news_list:
            st.error("No news found.")
        else:
            st.write("### 🗞 Latest Headlines")
            for n in news_list:
                st.write(f"- {n}")

            summary_prompt = (
                f"Summarize the sentiment of these news headlines: {news_list}"
            )

            response = client.chat.completions.create(
                model="llama-3.1-8b-instant",
                messages=[
                    {"role": "system", "content": "You are a financial news analyst."},
                    {"role": "user", "content": summary_prompt},
                ],
            )

            st.write("### 🤖 News Sentiment")
            st.write(response.choices[0].message.content)
            st.divider()


# ---------------- CHAT MEMORY ----------------

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a helpful finance assistant."}
    ]

st.subheader("💬 Ask Finance Questions")

user_query = st.text_input("Ask finance question or stock symbol:")

for msg in st.session_state.messages[1:]:
    if msg["role"] == "user":
        st.write(f"🧑‍💼 You: {msg['content']}")
    elif msg["role"] == "assistant":
        st.write(f"🤖 AI: {msg['content']}")

if user_query:
    st.session_state.messages.append(
        {"role": "user", "content": user_query}
    )

    if user_query.isupper() and len(user_query) <= 5:
        price = get_stock_price(user_query)
        if price:
            reply = f"📈 {user_query} price is ${price:.2f}"
        else:
            reply = "Stock not found."
    else:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=st.session_state.messages,
        )
        reply = response.choices[0].message.content

    st.session_state.messages.append(
        {"role": "assistant", "content": reply}
    )

    st.rerun()