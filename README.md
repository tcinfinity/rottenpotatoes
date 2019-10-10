# Summative 3

Movie Review Website using Flask

## Running

Mac/Linux: `export FLASK_APP=application.py`<br>
Windows: `set FLASK_APP=application.py`

Mac/Linux: `export DATABASE_URL=postgres://miwfafoighpxaf:0812642b1f8362b1fa91d70c6054443ac20ef250e40d29eff90b1424aa0aca68@ec2-174-129-29-101.compute-1.amazonaws.com:5432/d4gha1nsrvq385`<br>
Windows: `set DATABASE_URL=postgres://miwfafoighpxaf:0812642b1f8362b1fa91d70c6054443ac20ef250e40d29eff90b1424aa0aca68@ec2-174-129-29-101.compute-1.amazonaws.com:5432/d4gha1nsrvq385`

___
Alternatively, you can do `source init.sh` in a UNIX command line (Mac/Linux) or `call init.bat` in Windows for set up these environment variables automatically.

`FLASK_DEBUG` has been enabled (`FLASK_DEBUG=1`) for easier reporting of errors.

To run the flask application, enter `flask run` into the command line while in the root project directory.

## Setup

`sql/init.sql` has been made to reset all tables in the database.
This can be run on the database to wipe out all data and empty all tables.

`import.py` has also been made to import all default movies from `movies.csv` (250 movies) int the `movies` table.
This can be run via:
```unix
python import.py
```