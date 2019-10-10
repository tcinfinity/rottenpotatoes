import os, sys

from flask import Flask, session, render_template, make_response, redirect, url_for, flash, abort, Markup, request, escape, abort, jsonify
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from forms import LoginForm, SignUpForm, SearchForm, ReviewForm

import uuid
import requests

import omdb

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

app.config["SECRET_KEY"] = b'\x8e|\xf8\xa9\8\x1a.\xcc;Nj\xca\xa9\xf3\xcfY\x86\xb2\xac\8l\xa2\xaf\xb4'

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"), pool_size=20, max_overflow=0)
db = scoped_session(sessionmaker(bind=engine))

API_KEY = '9e67ebce'
omdb.set_default('apikey', API_KEY)

# api prevent jsonify from sorting
app.config['JSON_SORT_KEYS'] = False

@app.route("/", methods=["POST", "GET"])
def index():
    form = SearchForm()
    
    if form.validate_on_submit():
        search_query = form.search.data
        print(search_query)

        if search_query == '':
            return redirect(url_for('index'))
        else:
            return redirect('/search/{}'.format(search_query))

    return render_template('index.html', form=form)


@app.route('/search/<req>', methods=["POST", "GET"])
def search(req):
    form = SearchForm()

    if req == "":
        return redirect(url_for('index'))

    escreq = str(escape(req))

    # init
    results = None

    if escreq.isdigit():
        intreq = int(escreq)

        if len(intreq) <= 4: # check for year
            # set maximum to save time
            results = db.execute("SELECT * FROM movies WHERE year LIKE '%:year%'", {"year": intreq}).fetchmany(20)
        
        # if not year, check for imdb id
        if results is None:
            temp_id = 'tt' + escreq
            results = db.execute("SELECT * FROM movies WHERE id LIKE :id", {"id": '%'+temp_id+'%'}).fetchmany(20)

    else:
        # not an integer
        if escreq[:2] == 'tt' and len(escreq) > 3 and escreq[2:].isdigit(): # imdb id with starter tags
            results = db.execute("SELECT * FROM movies WHERE id LIKE :id", {"id": 'tt%'+escreq[:2]+'%'}).fetchmany(20)

        # not imdb id
        if results is None:
            results = db.execute("SELECT * FROM movies WHERE lower(title) LIKE lower(:title)", {"title": '%'+escreq+'%'}).fetchmany(20) # TODO: better order

        if results is None and ' ' in escreq:
            splitreq = escreq.split(' ')

            # search each word with priority first in title to last
            results = [
                db.execute("SELECT TOP 5 * FROM movies WHERE lower(title) LIKE lower(:word_like) ORDER BY CHARINDEX(lower(:word), title, 1), lower(title)", {"word": word, "word_like": '%'+word+'%'}).fetchall()
                for i, word in enumerate(splitreq)
            ]

            # remove nesting
            results = [inner for outer in results for inner in outer]


    # all queries fail - set to None (since query causes result = [])
    if len(results) == 0:
        results = None

    if results is not None:
        imageURLs = []

        for movie in results:
            # results - 0 id, 1 title, 2 year, 3 runtime, 4 imdbRating, 5 rpRating
            title = movie[1]

            # TODO: async with callback
            try:
                resp = requests.get('https://api.themoviedb.org/3/search/movie?api_key=15d2ea6d0dc1d476efbca3eba2b9bbfb&query=' + title)
                data = resp.json()

                res = 'http://image.tmdb.org/t/p/w500' + data['results'][0]['poster_path']
            except:
                # unable to get poster - missing or connection error?
                res = None
        
            imageURLs.append(res)

        print(imageURLs)

        # TODO: continue searching for more
        # temporary placeholder
        fetchall_results = results[:] # 'showing top max_results[0] of max_results[1] results'
        max_results = (len(results), len(fetchall_results))

    # submit search request (nav bar)
    if form.validate_on_submit():
        search_query = form.search.data
        return redirect('/search/{}'.format(search_query))

    # results == None handled by jinja
    print(results)

    if results is not None:
        # group into 2 for bootstrap card deck (columning)
        chunk_size = 2
        chunked_results = [results[i:i + chunk_size] for i in range(0, len(results), chunk_size)]
        chunked_urls    = [imageURLs[i:i + chunk_size] for i in range(0, len(imageURLs), chunk_size)]

        # for jinja2 for loop
        zipped = zip(chunked_results, chunked_urls)

        return render_template('search.html', form=form, search_query=escreq, results=zipped, max_results=max_results)
    else:
        return render_template('search.html', form=form, search_query=escreq, results=None)


@app.route("/login", methods=["POST", "GET"])
def login():
    form = LoginForm()

    # declare default to init key 'remember_me_preferences'
    if 'remember_me_preferences' not in session:
        session['remember_me_preferences'] = False
        session.permanent = False

    if 'is_logged' not in session:
        session['is_logged'] = False

    # check if logged in already
    if session['is_logged']:

        try:
            username_from_uuid = db.execute("SELECT username FROM users WHERE uuid = :uuid", {"uuid": str(session['logged_uuid'])}).fetchall()
            username_from_uuid = username_from_uuid[0][0]
        except: # no logged_uuid (auto-generated)? suspect tampering
            print('no logged_uuid')
            session['logged_uuid'] = None
            session['username'] = None
            session['is_logged'] = False

        # login not required - already logged in
        if username_from_uuid == session['username']:
            flash('You have already logged in.', 'warning')
            return redirect(url_for('index'))

        # suspect tampering
        else:
            session['logged_uuid'] = None
            session['username'] = None
            session['is_logged'] = False

    # on submit form
    if form.validate_on_submit():
        # get data
        q_username = form.username.data
        q_password = form.password.data
        q_remember = form.remember.data

        # check remember me - save preference
        session['remember_me_preferences'] = q_remember

        # check login
        if '@' in q_username: # email
            # check if email has account
            emails = db.execute("SELECT email FROM users").fetchall()
            emails = [x[0] for x in emails] # extract as list of strings
            if q_username in emails:
                data = db.execute("SELECT * from users WHERE email = :email", {"email": q_username}).fetchall()
                # output is nested list (0 id, 1 username, 2 email, 3 password, 4 uuid)

                if data[0][3] == q_password:
                    session['is_logged'] = True
                    session['username'] = data[0][1]
                    
                    # uuid should be created upon sign up
                    uuid = data[0][4]

                    session['logged_uuid'] = uuid

                    # remember me
                    session['remember_me_preferences'] = q_remember
                    session.permanent = q_remember

                    # redirect on success
                    flash('You have successfully logged in, {}!'.format(data[0][1]), 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Login unsuccessful - The username and password do not match.', 'danger')
        
            else: # not a valid email
                msg = Markup(render_template('login-flashes.html', datatype='email', data=q_username))
                flash(msg, 'danger')
                return redirect(url_for('login'))
                    
        else: # username
            usernames = db.execute("SELECT username FROM users").fetchall()
            usernames = [x[0] for x in usernames]

            if q_username in usernames:
                data = db.execute("SELECT * from users WHERE username = :username", {"username": q_username}).fetchall()
                # output is nested list (0 id, 1 username, 2 email, 3 password, 4 uuid)

                if data[0][3] == q_password:
                    session['is_logged'] = True
                    session['username'] = q_username
                    
                    # uuid should be created upon sign up
                    uuid = data[0][4]

                    session['logged_uuid'] = uuid

                    # remember me
                    session.permanent = q_remember

                    # redirect on success
                    flash('You have successfully logged in, {}!'.format(q_username), 'success')
                    return redirect(url_for('index'))
                else:
                    flash('Login unsuccessful - The username and password do not match.', 'danger')

            else: # not a valid username
                msg = Markup(render_template('login-flashes.html', datatype='username', data=q_username))
                flash(msg, 'danger')
                return redirect(url_for('login'))

    # has logged in before but logged out - username is last used username, autofill
    if hasattr(session, 'username'):
        username = session['username']
        return render_template('login.html', username=username, form=form)
    else:
        session['username'] = None
    
    # render normal view
    return render_template('login.html', form=form)


@app.route('/signup', methods=["POST", "GET"])
def signup():
    form = SignUpForm()

    # declare default to init key 'remember_me_preferences'
    if 'remember_me_preferences' not in session:
        session['remember_me_preferences'] = False
        session.permanent = False

    if 'is_logged' not in session:
        session['is_logged'] = False

    # check if logged in already
    if session['is_logged']:
        return redirect(url_for('login')) # contains handlers to route back to index

    if form.validate_on_submit():
        q_username = form.username.data
        q_email = form.email.data
        q_password = form.password.data
        q_remember = form.remember.data
        
        session['remember_me_preferences'] = q_remember

        data = db.execute("SELECT username, email FROM users").fetchall()
        # 0 username, 1 email

        username_taken = q_username in [x[0] for x in data]
        email_taken = q_username in [x[1] for x in data]

        if username_taken and email_taken:
            msg = Markup(render_template('signup-flashes.html', fail='ue', username=q_username, email=q_email))
            flash(msg, 'danger')
            return redirect(url_for('signup'))
        
        elif username_taken:
            msg = Markup(render_template('signup-flashes.html', fail='u', username=q_username))
            flash(msg, 'danger')
            return redirect(url_for('signup'))

        elif email_taken:
            msg = Markup(render_template('signup-flashes.html', fail='e', email=q_email))
            flash(msg, 'danger')
            return redirect(url_for('signup'))
        
        else: # create account
            
            # create user in users
            gen_uuid = str(uuid.uuid4())
            db.execute("INSERT INTO users (username, email, password, uuid) VALUES (:username, :email, :password, :uuid)", 
                {"username": q_username, "email": q_email, "password": q_password, "uuid": gen_uuid}
            )
            db.commit()

            # set session variables
            session['is_logged'] = True
            session['username'] = q_username
            session['logged_uuid'] = gen_uuid
            print(session['is_logged'], session['username'], session['logged_uuid'])

            session.permanent = q_remember

            msg = Markup('You have successfully signed up, <span class="flash-variable">{}</span>!'.format(q_username))
            flash(msg, 'success')
            return redirect(url_for('index'))

    return render_template('signup.html', form=form)


@app.route('/forgot', methods=["POST", "GET"])
def forgot_password():
    # TODO: WIP
    return redirect(url_for('index'))


# @app.route('/confirm/<username>/<code>', methods=["POST", "GET"])
# def confirm(username, code):
#     pass
#     # __________________
#     # Oops wrong project
#     # Can't use ORM ://
#     # __________________
#     user = User.objects.filter(username=username).first()
#     if user and user.change_configuration and user.change_configuration
#         if code == user.change_configuration.get('confirmation_code'):
#             user.email = user.change_configuration.get('new_email')
#             user.change_configuration = {}
#             user.email_confirmed = True
#             user.save()
#             return render_template('user/email_confirmed.html')
#     else:
#         abort(404)


@app.route('/logout', methods=["POST", "GET"])
def logout():
    referrer_route = request.referrer

    # check for invalid login status
    if 'is_logged' not in session or 'logged_uuid' not in session:
        session['is_logged'] = False
        session['logged_uuid'] = None
        flash('You are not logged in.', 'warning')
    
    if 'username' not in session:
        session['username'] = None
        session['is_logged'] = False
        session['logged_uuid'] = None
        flash('You are not logged in.', 'warning')

    # check for login status
    if session['is_logged']:
        session['is_logged'] = False
        session['logged_uuid'] = None
        flash('You have been successfully logged out!', 'success')
        # username not cleared to be reused on next login

    # send user back to current webpage
    if referrer_route is None:
        return redirect(url_for('index'))
    else:
        return redirect(referrer_route)

@app.route('/myaccount', methods=["POST", "GET"])
def myaccount():
    form = SearchForm()

    # weird None values
    if session['username'] is None:
        session['is_logged'] = False
        session['logged_uuid'] = None

    if session['is_logged'] is None or session['logged_uuid'] is None:
        session['is_logged'] = False
        session['logged_uuid'] = None

    # check for invalid login status
    if 'is_logged' not in session or 'logged_uuid' not in session or 'username' not in session:
        session['is_logged'] = False
        session['logged_uuid'] = None
        if 'username' not in session:
            session['username'] = None
        return redirect(url_for('index'))

    # check if logged in already
    if session['is_logged']:

        try:
            username_from_uuid = db.execute("SELECT username FROM users WHERE uuid = :uuid", {"uuid": str(session['logged_uuid'])}).fetchall()
            username_from_uuid = username_from_uuid[0][0]
        except: # no logged_uuid (auto-generated)? suspect tampering
            print('no logged_uuid')
            print(type(session['logged_uuid']))
            session['logged_uuid'] = None
            session['username'] = None
            session['is_logged'] = False
            flash('You have not logged in.', 'warning')
            return redirect(url_for('index'))

        # uuid does not match username - suspect tampering
        if username_from_uuid != session['username']:
            print(username_from_uuid, session['logged_uuid'], session['username'])
            session['logged_uuid'] = None
            session['is_logged'] = False
            flash('You have not logged in.', 'warning')
            return redirect(url_for('index'))

    else:
        flash('You have not logged in.', 'warning')
        return redirect(url_for('index'))

    # search bar
    if form.validate_on_submit():
        search_query = form.search.data
        print(search_query)

        if search_query == '':
            return redirect(url_for('index'))
        else:
            return redirect('/search/{}'.format(search_query))

    # get reviews
    reviews = db.execute("SELECT id, title, rating, mdata FROM reviews JOIN movies ON movies.id = reviews.movieID WHERE username = :username", {"username": session['username']}).fetchall()
    # no reviews yet
    if len(reviews) == 0:
        chunked_reviews = None
    else:
        # chunkify reviews for double column
        chunk_size = 2
        chunked_reviews = [reviews[i:i + chunk_size] for i in range(0, len(reviews), chunk_size)]

    return render_template('myaccount.html', reviews=chunked_reviews, form=form)


@app.route('/movie/<imdb_id>', methods=["POST", "GET"])
def movie_details(imdb_id):
    form = SearchForm()
    reviewform = ReviewForm()

    # check for invalid login status
    if 'is_logged' not in session or 'logged_uuid' not in session or 'username' not in session:
        session['is_logged'] = False
        session['logged_uuid'] = None
        if 'username' not in session:
            session['username'] = None
    
    # check if logged in already
    if session['is_logged']:

        print(session['is_logged'], session['username'], session['logged_uuid'])

        try:
            username_from_uuid = db.execute("SELECT username FROM users WHERE uuid = :uuid", {"uuid": str(session['logged_uuid'])}).fetchall()
            username_from_uuid = username_from_uuid[0][0]
        except: # no logged_uuid (auto-generated)? suspect tampering
            print(sys.exc_info())
            print('no logged_uuid')
            session['logged_uuid'] = None
            session['username'] = None
            session['is_logged'] = False
        else:
            # uuid and username do not match - suspect tampering
            if username_from_uuid != session['username']:
                session['logged_uuid'] = None
                session['username'] = None
                session['is_logged'] = False

    # get stored movie data
    print(imdb_id)
    movie_data = db.execute("SELECT * FROM movies WHERE id = :id", {"id": imdb_id}).fetchall()

    try:
        omdb_res = omdb.request(i=imdb_id)
        omdb_data = omdb_res.json()
    except:
        print('Cannot get response from OMDb')
        omdb_data = None

    # get poster img
    # results - 0 id, 1 title, 2 year, 3 runtime, 4 imdbRating, 5 rpRating
    title = movie_data[0][1]
    try:
        img_res = requests.get('https://api.themoviedb.org/3/search/movie?api_key=15d2ea6d0dc1d476efbca3eba2b9bbfb&query=' + title)
        img_data = img_res.json()

        img_url = 'http://image.tmdb.org/t/p/w500' + img_data['results'][0]['poster_path']
    except:
        # unable to get poster - missing or connection error?
        img_url = None


    # get reviews
    reviews = db.execute("SELECT * FROM reviews WHERE movieID = :imdb_id", {"imdb_id": imdb_id}).fetchall()
    # 0 movieID, 1 username, 2 rating, 3 review (text), 4 timestamp
    print(reviews)

    your_review = None
    # check not reviewed
    review_usernames = [review[1] for review in reviews]
    if session['username'] in review_usernames and session['is_logged']:
        # already reviewed
        not_reviewed = False

        your_review = [review for review in reviews if review[1] == session['username']][0]

        # remove own review from list of other reviews
        reviews = [review for review in reviews if review[1] != session['username']]
    else:
        not_reviewed = True

    # chunkify reviews for double column
    chunk_size = 2
    chunked_reviews = [reviews[i:i + chunk_size] for i in range(0, len(reviews), chunk_size)]

    # validate review on submit
    if reviewform.validate_on_submit():
        q_rating = reviewform.rating.data
        q_review = reviewform.review.data
        
        # handle fake post request - repeat
        check_data = db.execute("SELECT * FROM reviews WHERE movieID = :movieID AND username = :username", {"movieID": imdb_id, "username": session['username']}).fetchall()
        if len(check_data) > 0:
            # user already reviewed
            flash('You have already reviewed this movie!', 'danger')
            return redirect(url_for('movie_details', imdb_id=imdb_id))

        other_ratings = db.execute("SELECT rating FROM reviews WHERE movieID = :movieID", {"movieID": imdb_id}).fetchall()
        other_ratings = [data[0] for data in other_ratings]

        # insert
        db.execute("INSERT INTO reviews (movieID, username, rating, mdata) VALUES (:movieID, :username, :rating, :mdata)", 
            {"movieID": imdb_id, "username": session['username'], "rating": q_rating, "mdata": q_review}
        )
        db.commit()

        rating_count = len(other_ratings) + 1 # self
        rating_average = (sum(other_ratings) + q_rating) / rating_count
        print(rating_count, rating_average)

        f_rating_average = "{:.1f}".format(rating_average)

        db.execute('UPDATE movies SET rpRating = :rpRating WHERE id = :imdb_id', {"rpRating": f_rating_average, "imdb_id": imdb_id})
        db.commit()
        
        flash('Your review has been successfully submitted.', 'success')
        return redirect(url_for('movie_details', imdb_id=imdb_id))

    # render form - radio (rating stars)
    rating10, rating9, rating8, rating7, rating6, rating5, rating4, rating3, rating2, rating1 = reviewform.rating
    rating_list = {'10': rating10, '9': rating9, '8': rating8, '7': rating7, '6': rating6, '5': rating5, '4': rating4, '3': rating3, '2': rating2, '1': rating1}

    # search bar
    if form.validate_on_submit():
        search_query = form.search.data
        print(search_query)

        if search_query == '':
            return redirect(url_for('index'))
        else:
            return redirect('/search/{}'.format(search_query))


    return render_template('movie.html', form=form, id=id, reviewform=reviewform, img_url=img_url, rating_list=rating_list, reviews=chunked_reviews, data=movie_data, omdb_data=omdb_data, not_reviewed=not_reviewed, your_review=your_review)


@app.route('/api/<imdb_id>', methods=["GET"])
def fetch_api(imdb_id):

    try:
        self_data = db.execute("SELECT * FROM movies WHERE id = :id", {"id": imdb_id}).fetchall()
        # results - 0 id, 1 title, 2 year, 3 runtime, 4 imdbRating, 5 rpRating

        reviews = db.execute("SELECT rating FROM reviews WHERE movieID = :id", {"id": imdb_id}).fetchall()
        review_count = len(reviews)
        
        try:
            omdb_res = omdb.request(i=imdb_id)
            omdb_data = omdb_res.json()
            print(omdb_data)
        except:
            print('Unable to connect to OMDb')
            abort(404)

        director = omdb_data['Director']
        actors = omdb_data['Actors']

        res = {
            "title": self_data[0][1],
            "year": self_data[0][2],
            "imdb_id": imdb_id,
            "director": director,
            "actors": actors,
            "imdb_rating": self_data[0][4],
            "review_count": review_count,
            "average_score": self_data[0][5],
        }

        return jsonify(res)
    
    except:
        abort(404)


@app.errorhandler(404)
def not_found(error):
    return make_response(render_template('404.html'), 404)