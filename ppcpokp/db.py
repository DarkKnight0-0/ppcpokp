import sqlite3

from flask import current_app, g
from flask.cli import with_appcontext


def ensure_download_clicks_table(db):
    db.execute(
        '''
        CREATE TABLE IF NOT EXISTS download_clicks (
            filename TEXT PRIMARY KEY,
            click_count INTEGER NOT NULL DEFAULT 0
        )
        '''
    )
    db.commit()


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(
            current_app.config['DATABASE'],
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row

    return g.db


def close_db(e=None):
    db = g.pop('db', None)

    if db is not None:
        db.close()


def init_app(app):
    app.teardown_appcontext(close_db)