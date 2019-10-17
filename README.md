# Rotten Potatoes

![image](static/assets/icon64.png)

A movie review website application made using Python and Flask.

## Installing

This web application uses **flask** on **Python 3.6**+.  
(See full list of [Dependencies](#Dependencies) for more information).

Ensure that you have [Python](https://www.python.org/downloads/) and [pip](https://pip.pypa.io/en/stable/installing/) installed.  
You can install the dependencies of this project using:

```unix
pip install -r requirements.txt
```

## Running

### Unix Bash (Mac / Linux, etc.)

```unix
$ export FLASK_APP=application.py
$ export DATABASE_URL=postgres://miwfafoighpxaf:0812642b1f8362b1fa91d70c6054443ac20ef250e40d29eff90b1424aa0aca68@ec2-174-129-29-101.compute-1.amazonaws.com:5432/d4gha1nsrvq385
```

### Windows CMD

```unix
> set FLASK_APP=application.py
> set DATABASE_URL=postgres://miwfafoighpxaf:0812642b1f8362b1fa91d70c6054443ac20ef250e40d29eff90b1424aa0aca68@ec2-174-129-29-101.compute-1.amazonaws.com:5432/d4gha1nsrvq385
```

### Windows Powershell

```unix
> $env:FLASK_APP = "application.py"
> $env:DATABASE_URL = "postgres://miwfafoighpxaf:0812642b1f8362b1fa91d70c6054443ac20ef250e40d29eff90b1424aa0aca68@ec2-174-129-29-101.compute-1.amazonaws.com:5432/d4gha1nsrvq385"
```

___
Alternatively, you can do `source init.sh` in a UNIX command line (Mac/Linux) or `call init.bat` in Windows to set up these environment variables automatically.

To run the flask application, enter `flask run` into the command line while in the root project directory.  
You can then visit `http://localhost:5000` on a browser tab.

**Note:**
`FLASK_DEBUG` has been enabled (`FLASK_DEBUG=1`) for easier reporting of errors.

## Setup

`sql/init.sql` has been made to reset all tables in the database.  
This can be run on the database to wipe out all data and empty all tables.

`import.py` has also been made to import all default movies from `movies.csv` (250 movies) into the `movies` table.  
This can be run via:

```unix
python import.py
```

## Routes

### Home
`.../`

This is the home page of the website.

### Login and Sign up
`.../login`, `.../signup`

The login and sign up routes can only be accessed if the user is not already logged in.  
Error messages will be displayed to the user if their login/signup is unsuccessful (e.g. account already created).

### Search
`.../search/<search query>`

All searches (even from other routes e.g. `.../`) will redirect here.  
Top 20 results will be shown (if any) - database queries will only be for year, IMDb ID and movie title.

### Logout
`.../logout`

Logs the user out. This page can only be accessed if the user is already logged in.

### My Account
`.../myaccount`

Shows the user the list of reviews and movies that he has left previously.

### Movie
`.../movie/<IMDb id>`

Show the background information of the movie (including title, genre, plot, rating etc.) and any reviews left by others users.  
Users can also submit their own review here, consisting of a score from 1 to 10 and a text review.

### API
`.../api/<IMDb id>`

The application also provides an API that can be fetched from this route.<br>
This returns a JSON response that provides the following information - the title, year, id, director, actors, IMDb rating, number of reviews and average score on Rotten Potatoes.

**Format:**

```json
{
    "title": "...",
    "year": int,
    "imdb_id": "...",
    "director": "...",
    "actors": "...",
    "imdb_rating": float,
    "review_count": int,
    "average_score": float
}
```

## Dependencies

See [requirements.txt](requirements.txt) for the full list of dependencies.

## Future Work

- [ ] Show recommendations and latest movies on homepage
- [ ] Show more results from query
- [ ] More specific options for query (e.g. director, actors, etc.)
- [ ] Delete reviews
