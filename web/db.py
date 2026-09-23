from flask import g

from database.connection import SessionLocal


def get_db():
    if "db" not in g:
        g.db = SessionLocal()
    return g.db


def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        try:
            # Desfaz apenas trabalho pendente; commits continuam nos Controllers.
            db.rollback()
        finally:
            db.close()
