#! /usr/bin/env python


def init_db(db):
    script = create_script()
    db = db.executescript(script)
    db.commit()

def create_script():
    from itertools import product
    from string import lowercase
    result = (table_sql(c1+c2) for c1, c2 in product(lowercase, lowercase))
    return '\n'.join(result)

def table_sql(suffix):
    return '''CREATE TABLE word_%s (
        word VARCHAR PRIMARY KEY,
        sound VARCHAR,
        mean VARCHAR);''' % suffix

if __name__ == '__main__':
    import sys
    import sqlite3

    db_path = sys.argv[1]
    db = sqlite3.connect(db_path)
    init_db(db)
