import csv
import os

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import scoped_session, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

def main():

    # table_names = inspect(engine).get_table_names()

    if not engine.dialect.has_table(engine, 'movies'):

        db.execute("""
            CREATE TABLE movies (
                id varchar(9) NOT NULL UNIQUE PRIMARY KEY,
                title varchar NOT NULL,
                year int NOT NULL,
                runtime int NOT NULL,
                imdbRating float NOT NULL,
                rpRating float
            );
        """)
        db.commit()

    with open('movies.csv', newline='') as f:

        reader = csv.reader(f, delimiter=';')
        next(reader, None)

        max_prog = sum(1 for row in reader)
        
        f.seek(0)
        next(reader, None)

        i = 1

        # TODO: check if row already exists

        # id written as 'ID' since id() is a built-in Python function
        for row in reader:
            
            # Title;Year;Runtime;imdbID;imdbRating
            title, year, runtime, ID, imdbRating = row

            db.execute("INSERT INTO movies (id, title, year, runtime, imdbRating) VALUES (:id, :title, :year, :runtime, :imdbRating)",
                        {"id": ID, "title": title, "year": int(year), "runtime": int(runtime), "imdbRating": float(imdbRating)})
            db.commit()

            print(f"{i/max_prog*100}%: Added {title}, {year}, {runtime}, {ID}, {imdbRating}")
            i += 1

if __name__ == "__main__":
    main()