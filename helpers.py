import os
import requests
import urllib.parse
import csv
import datetime
import yfinance as yf
import plotly.graph_objects as go

import uuid

from flask import redirect, render_template, request, session
from functools import wraps


def apology(message, code=400):
    """Render message as an apology to user."""
    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s
    return render_template("apology.html", top=code, bottom=escape(message)), code


def login_required(f):
    """
    Decorate routes to require login.

    https://flask.palletsprojects.com/en/1.1.x/patterns/viewdecorators/
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function


def lookup(query):

    url = "https://ms-finance.p.rapidapi.com/market/v2/auto-complete"

    querystring = {"q": query}

    headers = {
        "X-RapidAPI-Key": "f9eb8cf462mshda5338b49a7e35dp1cdfa9jsn7bca178e06c6",
        "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    data = response.json()

    stocks = [{"name": item['name'], "ticker": item['ticker'], "id": item['performanceId']}
              for item in data['results'] if item['securityType'] == 'ST']
    with open("response.json", "+a") as f:
        f.write(response.text)

    return stocks


def stockPrice(perf_id):

    url = "https://ms-finance.p.rapidapi.com/stock/v2/get-realtime-data"

    querystring = {"performanceId": perf_id}

    headers = {
        "X-RapidAPI-Key": "f9eb8cf462mshda5338b49a7e35dp1cdfa9jsn7bca178e06c6",
        "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    price = response.json()["lastPrice"]

    return price


"""
YAHOO finance
def lookup(symbol):
    

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(
            url,
            cookies={"session": str(uuid.uuid4())},
            headers={"Accept": "*/*", "User-Agent": "python-requests"},
        )
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        price = round(float(quotes[-1]["Adj Close"]), 2
                )

        print(url)
        return {"price": price, "symbol": symbol, "name": "noName"}
    except (KeyError, IndexError, requests.RequestException, ValueError):
        return None

"""

"""

iex cloud

def lookup(symbol):

    # Contact API
    try:
        api_key = os.environ.get("API_KEY")
        url = f"https://cloud.iexapis.com/stable/stock/{urllib.parse.quote_plus(symbol)}/quote?token={api_key}"
        response = requests.get(url)
        response.raise_for_status()
    except requests.RequestException:
        pass

    # Parse response
    try:
        quote = response.json()
        return {
            "name": quote["companyName"],
            "price": float(quote["latestPrice"]),
            "symbol": quote["symbol"]
        }
    except (KeyError, TypeError, ValueError):
        return {
            "name": "Invalid",
            "price": "Invalid",
            "symbol": "Invalid"
        }
"""


def usd(value):
    """Format value as USD."""
    return f"${value:,.2f}"


def fetch_stock_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data


def create_plotly_candlestick(data, ticker):
    fig = go.Figure(data=[go.Candlestick(x=data.index,
                    open=data['Open'],
                    high=data['High'],
                    low=data['Low'],
                    close=data['Close'])])

    fig.update_layout(title=ticker + ' Candlestick Chart',
                      xaxis_title='Date',
                      yaxis_title='Price')

    # Convert the figure to HTML and return it
    return fig.to_html()


def getHistory(perf_id):
    url = "https://ms-finance.p.rapidapi.com/stock/get-histories"

    querystring = {"PerformanceId": perf_id}

    print(perf_id)

    headers = {
        "X-RapidAPI-Key": "401ceb6114mshb8344c5c815e42dp14234ajsn44ff51554ddf",
        "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    json_data = response.json()
    return json_data
   
    # datetime_1Y = [item["DateTime"] for item in json_data[0]["5Y"]]
    # prices = [entry['Price'] for entry in json_data[0]["5Y"]]
    # print("Dates", datetime_1Y)
    # print("Price", prices)
    # return datetime_1Y, prices


def generate_plot(perf_id):
    data=getHistory(perf_id)
    dates3M=[item["DateTime"] for item in data[0]["3M"]]
    prices3M=[item['Price'] for item in data[0]["3M"]]

    dates1Y=[item["DateTime"] for item in data[0]["1Y"]]
    prices1Y=[item["Price"] for item in data[0]["1Y"]]

    dates5Y=[item["DateTime"] for item in data[0]["5Y"]]
    prices5Y=[item["Price"] for item in data[0]["5Y"]]

    datesMax=[item["DateTime"] for item in data[0]["MAX"]]
    pricesMax=[item["Price"] for item in data[0]["MAX"]]

    layout = go.Layout(title='Stock Price History', xaxis=dict(
        title='Date'), yaxis=dict(title='Price'))
    # Create a Plotly scatter plot
    trace1 = go.Scatter(x=dates3M, y=prices3M, mode='lines', name='Stock Price')
    fig1 = go.Figure(data=[trace1], layout=layout)

    trace2=go.Scatter(x=dates1Y, y=prices1Y, mode='lines', name='Stock Price')
    fig2=go.Figure(data=[trace2], layout=layout)

    trace3=go.Scatter(x=dates5Y, y=prices5Y, mode='lines', name='Stock Price')
    fig3=go.Figure(data=[trace3], layout=layout)

    trace4=go.Scatter(x=datesMax, y=pricesMax, mode='lines', name='Stock Price')
    fig4=go.Figure(data=[trace4], layout=layout)
    # Convert the Plotly figure to html
    plot1 = fig1.to_html(full_html="False")
    plot2 = fig2.to_html(full_html="False")
    plot3 = fig3.to_html(full_html="False")
    plot4 = fig4.to_html(full_html="False")

    plots=[plot1,plot2,plot3,plot4]

    

    return plots

def getTrailingReturns(perf_id):
    url = "https://ms-finance.p.rapidapi.com/stock/v2/get-trailing-total-returns"

    querystring = {"performanceId":"0P0000OQN8"}

    headers = {
    "X-RapidAPI-Key": "401ceb6114mshb8344c5c815e42dp14234ajsn44ff51554ddf",
    "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    return response.json()

def generateReturnsPlot(perf_id):
    data=getTrailingReturns(perf_id)
    '''to store x and y coordinates'''
    x_values=[]
    y_values=[]
    for return_period in ['1 Day', '1 Week', '1 Month', '3 Month', '6 Month', 'Year To Date', '1 Year', '3 Year', '5 Year', '10 Year', '15 Year']:
        if data['trailingTotalReturnsList'][0][f'trailing{return_period.replace(" ", "")}Return']:
            y_values.append(float(data['trailingTotalReturnsList'][0][f'trailing{return_period.replace(" ", "")}Return']))
            x_values.append(return_period)

# Create a line trace for the stock returns
    line_trace = go.Scatter(
        x=x_values,
        y=y_values,
        mode='lines+markers',
        name='Stock Returns'
    )

    # Create a line trace for the zero line
    zero_line_trace = go.Scatter(
        x=[x_values[0], x_values[-1]],
        y=[0, 0],
        mode='lines',
        line=dict(color='black', dash='dash'),
        name='Zero Line'    
    )

    layout = go.Layout(
        title='Stock Returns',
        yaxis={'title': 'Return Value'},
        xaxis={'title': 'Return Period'},
        autosize=True
    )

    fig = go.Figure(data=[line_trace, zero_line_trace], layout=layout)

    plotly_returns= fig.to_html()

    return plotly_returns