import os
import requests
from flask import Flask, session, request, render_template, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)
app.secret_key="dfjskgkfvjdgljkldfmjnmgl;m"
# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))



@app.route("/")
def index():
    return render_template("index.html")


@app.route('/register', methods=['POST'])
def register():
    return render_template("register.html")

@app.route('/registersuc', methods = ['POST'])
def registersuc():
    username= request.form.get("username")
    password = request.form.get("password")
    db.execute("INSERT INTO registry (username,password) VALUES (:username,:password)",{"username":username,"password":password})
    db.commit()
    return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    return render_template("login.html")

@app.route('/loginsuc', methods = ['POST'])
def loginsuc():
    givenName = request.form.get("username")
    givenPass = request.form.get("password")
    if(givenName!=None or givenPass!=None):
        if(db.execute("SELECT * FROM registry WHERE username = :givenName",{"givenName":givenName}).rowcount==0):
            return "sorry doesent exist"
        user = db.execute("SELECT * FROM registry WHERE username = :givenName",{"givenName":givenName}).fetchone()
        if(user.password==givenPass):
            session['user']=givenName
            return redirect('/user')

@app.route("/logout")
def logout():
    session.pop("user",None)
    return redirect('/')
    
@app.route('/user')
def user():
    if "user" in session:
        user=session["user"]
        return render_template("loggedIn.html")
    else:
        return redirect('/')

@app.route('/search', methods = ['POST'])
def search():
    query= str(request.form.get("query"))
    books = db.execute("SELECT * FROM books WHERE isbn LIKE '%' ||:val||'%' OR title LIKE '%' ||:val||'%' OR author LIKE '%' ||:val||'%' OR  year LIKE '%' ||:val||'%'", {"val":query}).fetchall()
    db.commit()
    return render_template("search.html",books=books)

@app.route('/results/<isbn>')
def results(isbn):
    resultBook = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
    db.commit()
    request = requests.get("https://www.goodreads.com/book/review_counts.json?isbns={}&key=r03xhZNVeS3gr7wwU4SA".format(isbn))
    if(request.status_code!=200):
        raise Exception("error:api not returning")
    data=request.json()
    avgRating= data["books"][0]["average_rating"]
    numberOfRatings = data["books"][0]["work_ratings_count"]
    return render_template("bookPage.html",book=resultBook, avgRating = avgRating, numberOfRatings = numberOfRatings)