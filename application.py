import os

import requests

from flask import Flask, session, request, render_template, redirect, jsonify
from flask_session.__init__ import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from werkzeug.exceptions import default_exceptions, HTTPException
from werkzeug.exceptions import InternalServerError

from werkzeug.security import check_password_hash, generate_password_hash

from helpers import login_required

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


@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    # Return list of matching results or message if no results
    # Also return partial matches

    if request.method == "POST":

        # Get form submission
        search = request.form.get("search")

        # Search for ISBN, book title, and author matches in books table
        # Return matches including partial ones

        results = db.execute("SELECT isbn, title, author "
                             "FROM books "
                             "WHERE isbn like :search OR "
                             "title like :search OR "
                             "author like :search",
                             {"search": "%" + search + "%"}
                             ).fetchall()

        if results is None:
            return render_template("apology.html",
                                   message="No results, try again.")

        return render_template("searched.html", results=results), 200

    else:

        return render_template("/index.html"), 200


@app.route("/book/<string:isbn>", methods=["GET"])
@login_required
def book(isbn):

    if request.method == "GET":

        # make sure isbn was entered, if not redirect to search
        if isbn is None:
            return redirect("search.html"), 200

        # make sure book exits
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                          {"isbn": isbn}
                          ).fetchone()

        if book is None:
            return render_template("apology.html", message="No such book.")

        # Get book reviews
        reviews = db.execute("SELECT rating, comment "
                             "FROM reviews "
                             "WHERE isbn = :isbn",
                             {"isbn": isbn}).fetchall()

        print(reviews)
        
        # display avg. ratings and number of ratings in goodreads data
        res = requests.get(
                           "https://www.goodreads.com/book/review_counts.json",
                           params={"key": "kTZWyk5P19ddQpRmXj18ZA",
                                   "isbns": isbn,
                                   "format": "json"
                                   }
                           )

        if res.status_code != 200:
            raise Exception("ERROR: API request unsuccessful.")

        data = res.json()

        return render_template(
           "book.html", book=book,
           reviews=reviews,
           goodreads_review_count=data['books'][0]['work_ratings_count'],
           goodreads_avg_review=data['books'][0]['average_rating']
           ), 200


@app.route("/add_review", methods=["POST"])
@login_required
def add_review():

    if request.method == "POST":
        print("got into POST")
        # Get rating and comment from form and check that inputs are valid
        isbn = request.form.get("isbn")
        rating = request.form.get("rating")
        comment = request.form.get("comment")

        print(isbn, rating, comment)

        # check if user has already submitted review for book
        user_id = db.execute("SELECT user_id "
                             "FROM reviews "
                             "WHERE user_id = :user_id AND isbn = :isbn",
                             {"user_id": session["user_id"],
                              "isbn": isbn
                              }
                             ).fetchone()

        if user_id is not None:
            return render_template("apology.html",
                                   message="You already entered a comment "
                                   "for this book"
                                   ), 400

        if isbn is None:
            return render_template("apology.html",
                                   message="Must enter isbn"
                                   ), 400

        if rating is None or comment is None:
            return render_template("apology.html",
                                   message="Must enter rating and comment"
                                   ), 400

        # Insert rating, comment, and user into review database,
        # and commit to database
        db.execute("INSERT INTO reviews (isbn, rating, comment, user_id) "
                   "VALUES (:isbn, :rating, :comment, :user_id)",
                   {"isbn": isbn,
                    "rating": rating,
                    "comment": comment,
                    "user_id": session["user_id"]
                    }
                   )

        db.commit()

        return render_template("index.html"), 200


@app.route("/api/<string:isbn>", methods=["GET"])
@login_required
def api(isbn):

    if request.method == "GET":

        # make sure isbn was entered, if not return error
        if isbn is None:
            return jsonify({"error": "No isbn entered"}), 404

        # make sure book exits, if not return error
        book = db.execute("SELECT * FROM books WHERE isbn = :isbn",
                          {"isbn": isbn}
                          ).fetchone()

        if book is None:
            return jsonify({"error": "Invalid isbn"}), 404

        # get book details from data
        book = db.execute("SELECT title, author, year, isbn "
                          "FROM books "
                          "WHERE isbn = :isbn",
                          {"isbn": isbn}
                          ).fetchone()

        reviews = db.execute("SELECT count(*) AS count, avg(rating) AS avg "
                             "FROM reviews "
                             "WHERE isbn = :isbn "
                             "GROUP BY user_id",
                             {"isbn": isbn}
                             ).fetchone()

        if reviews is None:
            reviews = {}
            reviews['count'] = 0
            reviews['avg'] = 0

        print(reviews)
        # return redirect("book.html"), 200
        return jsonify({
            "title": book['title'],
            "author": book['author'],
            "year": book['year'],
            "isbn": book['isbn'],
            "review_count": reviews['count'],
            "average_score": "{:.1f}".format(reviews['avg'])
            })


@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":

        username = request.form.get("username")
        password = request.form.get("password")

        # Ensure username was submitted
        if not username:
            return render_template(
                                   "apology.html",
                                   message="must provide username"
                                   ), 400

        # Ensure password was submitted
        elif not password:
            return render_template(
                                   "apology.html",
                                   message="must provide password"
                                   ), 400

        # Query database for username
        userdata = db.execute("SELECT * "
                              "FROM users "
                              "WHERE username = :username",
                              {"username": username}
                              ).fetchone()

        # Ensure username exists and password is correct
        if not userdata or not check_password_hash(userdata["password"],
                                                   password
                                                   ):
            return render_template(
                                   "apology.html",
                                   message="invalid username and/or password"
                                   ), 400

        # Remember which user has logged in
        session["user_id"] = userdata["id"]

        # Redirect user to home page
        return redirect('/'), 302

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html"), 200


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/"), 302


@app.route("/register", methods=["GET", "POST"])
def register():
    """Register User"""

    # check for POST method
    if request.method == "POST":

        # get username and password from client
        username = request.form.get("username")
        password1 = request.form.get("password1")
        password2 = request.form.get("password2")

        # server-side check for username and passwords submission
        if not username or not password1 or not password2:
            return render_template(
                                   "apology.html",
                                   message="enter username, password, "
                                           "and password confirmation"

                                           ), 400
        if password1 != password2:
            return render_template(
                                   "apology.html",
                                   message=("passwords must match")
                                   ), 400

        # check if username doesn't exist
        if db.execute("SELECT * "
                      "FROM users "
                      "WHERE username = :username",
                      {"username": username}
                      ).fetchone():
            return render_template(
                                   "apology.html",
                                   message=("username already exists")
                                   ), 400

        # add username and password to users database
        # INSERT the new user into users, storing a hash of the user’s
        # password, not the password itself.
        # Hash the user’s password with generate_password_hash.
        db.execute("INSERT INTO users (username, password) "
                   "VALUES (:username, :password)",
                   {"username": username,
                    "password": generate_password_hash(
                                               password1,
                                               'pbkdf2:sha256', 8
                                               )}
                   )

        db.commit()

        # remember users session
        userdata = db.execute("SELECT *"
                              "FROM users"
                              "WHERE username = :username",
                              {"username": username}
                              )
        session["user_id"] = userdata[0]["id"]

        return redirect("/"), 302

    else:
        return render_template("register.html"), 200
