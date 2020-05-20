import os
import requests
from flask import Flask, session, request, render_template, redirect, flash, url_for
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


# landing page
@app.route("/")
def index():
    return render_template("index.html")

#lets user register
@app.route('/register', methods=['POST'])
def register():
    return render_template("register.html")

#register backend and then redirects to landing
@app.route('/registersuc', methods = ['POST'])
def registersuc():
    
    #grabs user registering information and inserts into a table
    username= request.form.get("username")
    password = request.form.get("password")
    db.execute("INSERT INTO registry (username,password) VALUES (:username,:password)",{"username":username,"password":password})
    db.commit()
    return redirect('/')

#lets user login
@app.route('/login', methods = ['POST'])
def login():
    #grabs inputted passwords
    givenName = request.form.get("username")
    givenPass = request.form.get("password")

    #checks for blank password and username
    if(db.execute("SELECT * FROM registry WHERE username = :givenName OR password = :givenPass",{"givenName":givenName,"givenPass":givenPass}).rowcount==0):
        return render_template("index.html",error="Incorrect Credentials")
    user = db.execute("SELECT * FROM registry WHERE username = :givenName",{"givenName":givenName}).fetchone()
    
    #checks username and password and makes a session
    if(user.password==givenPass):
        session['user']=givenName
        return redirect('/user')
    
@app.route("/logout")
def logout():
    
    #ends session
    session.pop("user",None)
    return redirect('/')
    
@app.route('/user')
def user():
    #shows logged in and gives search option
    if "user" in session:
        user=session["user"]
        return render_template("loggedIn.html")
    else:
        return redirect('/')

@app.route('/search', methods = ['POST'])
def search():
    #searches for book
    query= str(request.form.get("query"))
    
    #sets book variable
    book=None
    
    #looks for author, year, title, and isbn with partial search
    books = db.execute("SELECT * FROM books WHERE lower(isbn) LIKE '%' ||lower(:val)||'%' OR lower(title) LIKE '%' ||lower(:val)||'%' OR lower(author) LIKE '%' ||lower(:val)||'%' OR  lower(year) LIKE '%' ||lower(:val)||'%'", {"val":query}).fetchall()
    if(not books):
        book="No books returned"
    return render_template("loggedIn.html",books=books,book=book)
    
@app.route('/book/<isbn>', methods = ["GET","POST"])
def book(isbn):
    
    #makes sure one person doesent review more than once
    checkReview= db.execute("SELECT * FROM reviews WHERE person=:person AND isbn=:isbn",{"person":session["user"],"isbn":isbn}).fetchone()
    if checkReview==None:
        done=False
    else:
        done=True
    
    #grabs the book from the sql table
    isbn=str(isbn)
    resultBook = db.execute("SELECT * FROM books WHERE isbn=:isbn",{"isbn":isbn}).fetchone()
    
    #pulls from api
    res = requests.get("https://www.goodreads.com/book/review_counts.json?isbns={}&key=r03xhZNVeS3gr7wwU4SA".format(isbn))
    if(res.status_code!=200):
        print(res.status_code)
        raise Exception("error:api not returning")
    data=res.json()
    avgRating = data["books"][0]["average_rating"]
    numberOfRatings = data["books"][0]["work_ratings_count"]
    
    #sends in review
    if request.method == "POST" and done==False:
        review = request.form.get("review")
        rating = request.form.get("rating")
        db.execute("INSERT INTO reviews (isbn,person,review,rating) VALUES (:isbn,:person,:review,:rating)",{"isbn":isbn,"person":session["user"],"review":review,"rating":rating})    
        db.commit()
        done=True
    
    #grabs all reviews and loads the page
    reviews = db.execute("SELECT * FROM reviews WHERE isbn=:isbn",{"isbn":isbn}).fetchall() 
    return render_template("bookPage.html",book=resultBook, avgRating = avgRating, numberOfRatings = numberOfRatings,reviews=reviews,done=done)
   