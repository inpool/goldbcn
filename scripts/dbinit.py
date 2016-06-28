#! /usr/bin/env python2


def init_db(db):
    script = create_script()
    db.executescript(script)
    db.commit()

def create_script():
    from itertools import product
    from string import lowercase
    result = (table_sql(c1+c2) for c1, c2 in product(lowercase, lowercase))
    return '\n'.join(result)

def table_sql(suffix):
    return '''CREATE TABLE word_%s (
        word VARCHAR PRIMARY KEY,
        keyword VARCHAR,
        sound VARCHAR,
        mean VARCHAR);''' % suffix

if __name__ == '__main__':
    import sys, os
    import sqlite3

    if len(sys.argv) < 2:
        db_path = '~/.goldendict/dbcn/dict.db'
    else:
        db_path = sys.argv[1]
    db_path = os.path.expanduser(db_path)
    db_dir = os.path.dirname(db_path)
    if not os.path.exists(db_dir):
        os.makedirs(db_dir)
    elif not os.path.isdir(db_dir):
        print >> sys.stderr, "The database file's directory name is a file"
        sys.exit(1)
    db = sqlite3.connect(db_path)
    init_db(db)
