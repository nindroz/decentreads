import os

from flask import Flask, session, request, render_template, redirect
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

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
    #return ('h %s'%info)
    if(givenName!=None or givenPass!=None):
        if(db.execute("SELECT * FROM registry WHERE username = :givenName",{"givenName":givenName}).rowcount==0):
            return "sorry doesent exist"
        user = db.execute("SELECT * FROM registry WHERE username = :givenName",{"givenName":givenName}).fetchone()
        if(user.password==givenPass):
            return redirect('/user/%s'%user.id)
@app.route('/user/<int:user_id>')
def user(user_id):
    return "%s"%user_id
