import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.express as px
from stocknews import StockNews
from scipy.stats import norm


# Function for Black-Scholes model
def black_scholes(S, K, T, r, sigma, option_type='call'):
    """
    S: Current stock price
    K: Strike price
    T: Time to maturity (in years)
    r: Risk-free interest rate (annual)
    sigma: Volatility of the underlying stock (annual)
    option_type: 'call' or 'put'
    """
    d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
    d2 = d1 - sigma * np.sqrt(T)

    if option_type == 'call':
        option_price = S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)
    elif option_type == 'put':
        option_price = K * np.exp(-r * T) * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("Invalid option type. Use 'call' or 'put'.")

    return option_price

# Function to get live stock price
def get_live_stock_price(ticker):
    stock = yf.Ticker(ticker)
    live_price = stock.history(period='1d', interval='1m')['Close'].iloc[-1]
    return live_price

# Function to get stock data
def get_stock_data(ticker, period='1mo', interval='1d'):
    stock = yf.Ticker(ticker)
    hist = stock.history(period=period, interval=interval)
    return hist

# Function to calculate volatility
def calculate_volatility(hist):
    log_returns = np.log(hist['Close'] / hist['Close'].shift(1))
    volatility = log_returns.std() * np.sqrt(252)  # Annualized volatility
    return volatility

# Simple login form
st.title('Login')
username = st.text_input('Username')
password = st.text_input('Password', type='password')

if st.button('Login'):
    if username in credentials and credentials[username] == password:
        st.success('Login successful!')

        st.title('Stock Dashboard')
        ticker = st.sidebar.text_input('Ticker')
        start_date = st.sidebar.date_input('Start Date')
        end_date = st.sidebar.date_input('End Date')

        data = yf.download(ticker, start=start_date, end=end_date)
        fig = px.line(data, x=data.index, y=data['Adj Close'], title=ticker)
        st.plotly_chart(fig)

        pricing_data, news, ai, bets = st.tabs(['Pricing Data', 'Top 10 News', 'AI Generated Tips', 'Sports Bet'])

        with pricing_data:
            st.write('Price')
            data2 = data
            data2['%change'] = data['Adj Close'] / data['Adj Close'].shift(1) - 1
            data2.dropna(inplace=True)
            st.write(data2)
            annual_ret = data2['%change'].mean() * 252 * 100
            st.write('Annual Return is ', annual_ret, '%')
            stdev = np.std(data2['%change']) * np.sqrt(252)
            st.write('std dev is ', stdev * 100, '%')
            st.write('Adjusted Return', annual_ret / (stdev * 100))

        with news:
            st.header(f'News of {ticker}')
            sn = StockNews(ticker, save_news=False)
            df_news = sn.read_rss()
            for i in range(10):
                st.subheader(f'News {i + 1}')
                st.write(df_news['published'][i])
                st.write(df_news['title'][i])
                st.write(df_news['summary'][i])
                title_sentiment = df_news['sentiment_title'][i]
                st.write(f'Title Sentiment {title_sentiment}')
                news_sentiment = df_news['sentiment_summary'][i]
                st.write(f'News sentiment {news_sentiment}')

        with ai:
            st.header('Tips')
            K = st.text_input('Enter Strike Price: ')
            T = st.text_input('Enter Maturity Time: ')
            r = st.text_input('Enter Risk free interest rate: ')

            live_price = get_live_stock_price(ticker)
            hist = get_stock_data(ticker, period='1y', interval='1d')
            sigma = calculate_volatility(hist)

            if K and T and r:
                try:
                    K = float(K)
                    T = float(T)
                    r = float(r)

                    call_price = black_scholes(live_price, K, T, r, sigma, option_type='call')
                    put_price = black_scholes(live_price, K, T, r, sigma, option_type='put')
                    st.write('Call Price: ', call_price)
                    st.write('Put Price: ', put_price)
                except ValueError:
                    st.write('Please enter valid numeric inputs for strike price, maturity time, and risk-free interest rate.')

    else:
        st.error('Username or password is incorrect.')
