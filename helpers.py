import os
import requests
import urllib.parse
import csv
import datetime

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

    querystring = {"q":query}

    headers = {
        "X-RapidAPI-Key": "f9eb8cf462mshda5338b49a7e35dp1cdfa9jsn7bca178e06c6",
        "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)

    data = response.json()
    
    stocks = [{"name": item['name'], "ticker": item['ticker'], "id": item['performanceId']} for item in data['results'] if item['securityType'] == 'ST']
    with open("response.json", "+a") as f:
        f.write(response.text)

    
    return stocks
  
# def stockQuote(id):
  
#     url = "https://ms-finance.p.rapidapi.com/stock/v2/get-realtime-data"

#     querystring = {"performanceId":id}

#     headers = {
#         "X-RapidAPI-Key": "f9eb8cf462mshda5338b49a7e35dp1cdfa9jsn7bca178e06c6",
#         "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
#     }

#     response = requests.get(url, headers=headers, params=querystring)

#     return(response.json())

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
