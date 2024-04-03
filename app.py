from cs50 import SQL
import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from flask_session import Session
from tempfile import mkdtemp
from werkzeug.exceptions import default_exceptions, HTTPException, InternalServerError
from werkzeug.security import check_password_hash, generate_password_hash
import time

from helpers import *

# Configure application
app = Flask(__name__)

# Ensure templates are auto-reloaded
app.config["TEMPLATES_AUTO_RELOAD"] = True


# Ensure responses aren't cached
@app.after_request
def after_request(response):
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


# Custom filter
app.jinja_env.filters["usd"] = usd

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///finance.db")

# # Make sure API key is set
# if not os.environ.get("API_KEY"):
#     raise RuntimeError("API_KEY not set")

#SQLDB
db2 = SQL("sqlite:///fin2.db")

@app.route("/")
@login_required
def index():
    prices = {}       # dictionay to store current prices
    total = 0
    user_id = session["user_id"]

    """Show portfolio of stocks"""
    
    #information of stocks owned
    stocks = db.execute("SELECT * FROM portfolio WHERE user_id = ?", user_id) 
    query = "SELECT portfolio.id, portfolio.user_id, users.username, portfolio.stock_id, stocks.symbol, stocks.performance_id,stocks.name, portfolio.quantity FROM portfolio JOIN users ON portfolio.user_id = users.id JOIN stocks ON portfolio.stock_id = stocks.id WHERE users.id = ?"
    stocks = db2.execute(query, user_id)
    print(stocks)


    # querying cash remainig
    user = db2.execute("SELECT cash FROM users WHERE id = ?", user_id)

    for stock in stocks:
        # storing price of each stock price
        price = stockPrice(stock["performance_id"])
        symbol = stock["symbol"]
       
        total += (price * int(stock["quantity"]))
        # stroring prices in a dictionary
        prices[symbol] = price
    print(prices)
    print(stocks)
    return render_template("index.html", user=user, stocks=stocks, prices=prices, total=total)



@app.route("/buy", methods=[ "POST"])
@login_required
def buy():
    user_id = session["user_id"]
    user = db2.execute("SELECT username from users where id = ?", user_id)
    username = user[0]["username"]
    """Buy shares of stocks"""
    if request.method == "POST":
        name=request.form.get("name")
        id = request.form.get("id")
        price = float(request.form.get("price"))
        symbol = request.form.get("symbol")
        
        if not request.form.get("number"):
            return apology("Please provide number of stocks to buy", 400)

        number = int(request.form.get("number"))

        cost = price * number
        
        # querying data for cash
        user= db2.execute("SELECT cash FROM users WHERE id = ?", user_id)
    
        cash = float(user[0]["cash"])
        if cash < cost:
            return apology("Not enough money")
        else:
            # deductinh money from balance
            cash -= cost
            db.execute("UPDATE users SET cash = ? WHERE id = ?", cash, user_id)
            db2.execute("UPDATE users SET cash = ? WHERE id = ?", cash, user_id)

            #checking if stock cache is present
            s = db2.execute("SELECT * FROM stocks where symbol = ?", symbol)
            print("before, ", symbol)
            if s == []:
                db2.execute("INSERT INTO stocks (symbol, performance_id, name, info) values (?, ?, ?, ?)", symbol,id, name, "TO BE ADDED")
            s = db2.execute("SELECT * FROM stocks where symbol = ?", symbol)
            s=s[0]
            print(s)
            # updating history
            db.execute("INSERT INTO history (user_id,name, symbol, quantity, price) VALUES (?,?,?,?,?)", user_id, name, symbol, number, price)
            print("hererhere")
            db2.execute("INSERT INTO history (timestamp, user_id, stock_id, quantity, price) VALUES (?,?,?,?,?)",time.time(), user_id,s['id'], number, price)
          
          
            # updating personal portfolio
            stocks = db2.execute("SELECT quantity from portfolio where user_id = ? and  stock_id = ?", user_id, s['id'])
  
            # if user has purchased the stocks before, update the quantity otherwise create new entry
            if len(stocks) == 1:
                amount = int(stocks[0]["quantity"]) + number
                db.execute("UPDATE portfolio SET quantity = ? WHERE symbol = ? AND user_id = ?", amount, symbol, user_id)
                db2.execute("UPDATE portfolio SET quantity = ? WHERE stock_id = ? AND user_id = ?", amount, s[id], user_id)

            else:
                db.execute("INSERT INTO portfolio (user_id, username, stock_name, symbol, quantity) VALUES (?,?,?,?,?)", user_id, username, name, symbol, number)
                db2.execute("INSERT INTO portfolio (user_id, stock_id, quantity) values (?, ?, ?) ", user_id, s['id'], number)

    #if requested by GET, render purchase form
   

    return redirect("/")
    
    
@app.route("/history")
@login_required
def history():
    """Show history of transactions"""
    user_id = session["user_id"]

    #querying databse
    stocks = db2.execute("SELECT history.id, history.user_id, users.username, history.stock_id, stocks.symbol, stocks.name, history.quantity, history.price, history.action FROM history JOIN users ON history.user_id = users.id JOIN stocks ON history.stock_id = stocks.id WHERE users.id = ?", user_id)
    print(stocks)
    return render_template("history.html", stocks=stocks)


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        # Ensure username was submitted
        if not request.form.get("username"):
            return apology("must provide username", 403)

        # Ensure password was submitted
        elif not request.form.get("password"):
            return apology("must provide password", 403)

        # Query database for username
        stocks = db2.execute("SELECT * FROM users WHERE username = ?", request.form.get("username"))

        # Ensure username exists and password is correct
        if len(stocks) != 1 or not check_password_hash(stocks[0]["hash"], request.form.get("password")):
            return apology("invalid username and/or password", 403)

        # Remember which user has logged in
        session["user_id"] = stocks[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")


@app.route("/quote", methods=["GET", "POST"])
@login_required
def quote():
    """Get stocks quote."""
    # if visited via post
    if request.method == "POST":

        # get data from servers
        stocks = lookup(request.form.get("symbol"))

        #if valid output is recieved, turn the price into cost. otherwise pass it without altering
        try:
            return render_template("quoted.html",stocks=stocks)
        except:
            return render_template("quoted.html",stocks=stocks)
 
    else:
        return render_template("quote.html")


@app.route('/stock_details/<stock_id>')
def stock_details(stock_id):
    url = "https://ms-finance.p.rapidapi.com/stock/v2/get-realtime-data"
    name = request.args.get("name")
    symbol=request.args.get("symbol")
    

    querystring = {"performanceId":stock_id}
    
    headers = {
        "X-RapidAPI-Key": "f9eb8cf462mshda5338b49a7e35dp1cdfa9jsn7bca178e06c6",
        "X-RapidAPI-Host": "ms-finance.p.rapidapi.com"
    }

    response = requests.get(url, headers=headers, params=querystring)
    info = response.json()
    print(info)
    return render_template("info.html", info=info, symbol=symbol, name=name, id=stock_id)

@app.route('/buy_stocks', methods=["POST"])
def buy_stocks():
    name = request.form.get("stock_name")
    symbol = request.form.get("symbol")
    id=request.form.get("stock_id")
    price=request.form.get("stock_price")
    print(name, id, price)
    return render_template("buy.html", name=name, id=id, price=price, symbol=symbol)


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register user"""

    if request.method == "POST":
        # getting and validating inputs
        print(request.form.get("username"))
        print(request.form.get("password"))
        print(request.form.get("confirmation"))
        if not request.form.get("username"):
            return apology("NO username provided!", 403)

        elif not request.form.get("password") or not request.form.get("confirmation"):
            return apology("password must be provided and confirmed", 403)
    
        elif not request.form.get("password") ==  request.form.get("confirmation"):
            return apology("Passwords don't match")

        password = request.form.get("password")
        username = request.form.get("username")
        hash = generate_password_hash(password)

        #confirming unique username
        stocks = db.execute("SELECT * from users where username = ?", username)
        if len(stocks) > 0:
            return apology("Username Already Taken", 400)

        # adding user
        db.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        db2.execute("INSERT INTO users (username, hash) VALUES (?, ?)", username, hash)
        #loggin in user automatically
        id = db2.execute("SELECT id FROM users WHERE hash = ?", hash)
        session["user_id"] = id[0]["id"]
        return redirect("/") 

    else:
        return render_template("register.html")


@app.route("/sell", methods=["GET", "POST"])
@login_required
def sell():
    user_id = session["user_id"]
    # querying portfolio
    stocks = db2.execute("SELECT portfolio.id, portfolio.user_id, users.username, portfolio.stock_id, stocks.symbol, stocks.name, portfolio.quantity FROM portfolio JOIN users ON portfolio.user_id = users.id JOIN stocks ON portfolio.stock_id = stocks.id WHERE users.id = ?", user_id)
  
    """Sell shares of stocks"""
    # keeps rack of sold status
    stock_sold = False

    if request.method == "POST":
        # validating inputs
        if not request.form.get("symbol") or not request.form.get("shares"):
            return apology("No Stock Selected", 400)

        # variables
        symbol = request.form.get("symbol")
        s = db2.execute("select * from stocks where symbol=?", symbol)[0]
        price = stockPrice(s['performance_id'])  # fetches data through API
        symbol=symbol.upper()
        
        # shares owned
        stocks = db2.execute("SELECT portfolio.id, portfolio.user_id, users.username, portfolio.stock_id, stocks.symbol, stocks.name, portfolio.quantity FROM portfolio JOIN users ON portfolio.user_id = users.id JOIN stocks ON portfolio.stock_id = stocks.id WHERE users.id = ? and stocks.symbol=?", user_id, symbol)
        shares = int(stocks[0]["quantity"])
        shares_to_sell = int(request.form.get("shares"))
   
        if shares == 0:
            return apology("You Don't Own That Stock")

        elif (shares) < (shares_to_sell):
            return apology("You Don't Own Enough Shares")
        
        # removes the entry of share from portfolio if no shares are left after selling
        elif shares == shares_to_sell:
            
            db2.execute("DELETE FROM portfolio WHERE user_id = ? AND stock_id = ?", user_id, s['id'])
            stock_sold = True
        
        # decreases the number of shares owned
        elif shares > shares_to_sell:
            shares_left = shares - shares_to_sell
            db2.execute("UPDATE portfolio SET quantity = ? WHERE stock_id = ? AND user_id = ?", shares_left, s['id'], user_id)
            stock_sold = True

        # if successfully sold, then add money to balance
        if (stock_sold):
            # add entry in history
           # db.execute("INSERT INTO history (user_id, stock_id, quantity, price, action) VALUES (?, ?, ?, ?, ?, ?)", user_id, info["name"], symbol, shares_to_sell, info["price"], "SOLD")
            db2.execute("INSERT INTO history (timestamp, user_id, stock_id, quantity, price, action) VALUES (?,?,?,?,?, ?)",time.time(), user_id,s['id'], shares_to_sell, price, "SOLD")
            user = db.execute("SELECT * FROM users WHERE id = ?", user_id)
            cash = float(user[0]["cash"])
            cash += (int(shares_to_sell) * price)
            db2.execute("UPDATE users SET cash = ? WHERE id = ?", cash, user_id)
        
    else:

        if(request.args.get("stock_id") is None):
            return render_template("sell.html", stocks=stocks)
        
        else:
            symbol = request.args.get("symbol")
            name = request.args.get("stock_name")

            price=request.args.get("stock_price")
            return render_template("sell_stock.html", symbol=symbol, name=name, price=price)
    return redirect("/")


@app.route("/recharge", methods=["GET", "POST"])
@login_required
def recharge():
    user_id = session["user_id"]
    user = db2.execute("SELECT * FROM users WHERE id = ?", user_id)
    cash = float(user[0]["cash"])
    if request.method == "POST":
        amount = int(request.form.get("amount"))
        cash += amount
        quantity = 1
        dash = "-"

        #updating database
        db2.execute("UPDATE users SET cash = ? WHERE id = ?", cash, user_id)
        db2.execute("INSERT INTO history (user_id, stock_id, price, quantity, action) VALUES (?, ?, ?, ?, ?)", user_id,3, amount, quantity, "Recharge")

    else:
        return render_template("recharge.html", cash=cash)

    return redirect("/recharge")


def errorhandler(e):
    """Handle error"""
    if not isinstance(e, HTTPException):
        e = InternalServerError()
    return apology(e.name, e.code)


# Listen for errors
for code in default_exceptions:
    app.errorhandler(code)(errorhandler)
 
