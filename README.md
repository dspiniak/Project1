# Project 1

*Web Programming with Python and JavaScript*

Overview: this webpage allows users to search for books, returning reviews
and review statistics from GoodReads, as well as requesting a book's
information via an API.

*Templates*
**apology.html**
Simple template that just displays an error message.

**book.html**
Displays a specific book:
 a) Details: isbn, title, author, and year
 b) Goodreads average reviews and number of reviews count
 c) User reviews and ratings
Also, allows a user to rate and comment a book via a form.

**index.html**
Displays a search box whereby users can search for books by entering a book's isbn, author, or title. Incomplete search also finds matches and it's case sensitive.

**layout.html**
Layout used across other templates. Consists of a simple navbar. Register and Login are only displayed when user is not logged in.

**login.html**
Allows user to login by submitting username and password via a form.

**register.html**
Allows user to register by submitting username, password, and password check via a form.

**searched.html**
Displays the book's search results: isbn, title, and author. Results link to a book's page.

*Styles*
**styles.css**
Padding for body class, fixes footer to bottom, and styles the book search box.

*Apps*
**application.py**
  1. index:
    Uses GET and POST method.
    GET: returns index.html.
    POST: gets form submission, searches books table for results, and returns results to searched.html.

  2. book:
    Receives book's isbn string via GET method, making sure book exists in books table. Gets books reviews from reviews table. Gets book's avg. reviews and # of reviews via GoodReads API. Returns this information to book.html.

  3. add_review:
    Uses POST method. Gets a book's isbn, rating and comment from form. Checks if user has already submitted review for book. Inserts rating, comment, and user into reviews table and commits tu database.

  4. API:
    Receives a book's isbn via GET method. Makes sure isbn entered is correct and that book exists in database. Gets book details from books table and book reviews stats (review count and avg. rating) from reviews table. Returns JSON with bookk details and reviews stats.

  5. login:
    Uses GET and POST methods.
    GET: returns login.html
    POST: gets username and password from form. Ensures username and password were submitted. Queries database for username. Ensures username exists and password is correct. finally, remembers user_id via session, redirecting to index.html. Adds username and password to users database. Inserts the new user into users table, storing a hash of the user's password, not the password itself. Hashes the user’s password with generate_password_hash. Commits data to database. Finally it remember user's id via session, redirecting to index.html

  6. logout: Logs out a user by clearing session.

  7. register:
  Uses GET and POST methods.
  GET: directs to register.html
  POST: gets username, password, and password confirmation from form. Does a server-side check for username and passwords submission.

**helpers.py**
Redirects users to /login if there's no active session.

*Database model*
3 tables: books, reviews, and users.

**books**
-- Table: public.books

-- DROP TABLE public.books;

CREATE TABLE public.books
(
    isbn text COLLATE pg_catalog."default" NOT NULL,
    title text COLLATE pg_catalog."default" NOT NULL,
    author text COLLATE pg_catalog."default" NOT NULL,
    year integer NOT NULL,
    CONSTRAINT books_pkey PRIMARY KEY (isbn)
)

TABLESPACE pg_default;

ALTER TABLE public.books
    OWNER to adkdslfjaqxvqh;

**reviews**
-- Table: public.reviews

-- DROP TABLE public.reviews;

CREATE TABLE public.reviews
(
    review_id integer NOT NULL DEFAULT nextval('reviews_review_id_seq'::regclass),
    isbn text COLLATE pg_catalog."default" NOT NULL,
    user_id integer NOT NULL,
    rating smallint NOT NULL,
    comment text COLLATE pg_catalog."default",
    CONSTRAINT review_id PRIMARY KEY (review_id),
    CONSTRAINT isbn FOREIGN KEY (isbn)
        REFERENCES public.books (isbn) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION,
    CONSTRAINT user_id FOREIGN KEY (user_id)
        REFERENCES public.users (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
)

TABLESPACE pg_default;

ALTER TABLE public.reviews
    OWNER to adkdslfjaqxvqh;

**users**
-- Table: public.users

-- DROP TABLE public.users;

CREATE TABLE public.users
(
    id integer NOT NULL DEFAULT nextval('users_id_seq'::regclass),
    username text COLLATE pg_catalog."default" NOT NULL,
    password text COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT users_pkey PRIMARY KEY (id),
    CONSTRAINT username UNIQUE (username)
)

TABLESPACE pg_default;

ALTER TABLE public.users
    OWNER to adkdslfjaqxvqh;
