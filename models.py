from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
"""SQLAlchemy database instance used across the app."""


class User(db.Model):
    """User model storing profile data and related movies."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)

    movies = db.relationship("Movie", backref="user", lazy=True, cascade="all, delete-orphan")


class Movie(db.Model):
    """Movie model storing OMDb metadata for a user's favorite."""
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    director = db.Column(db.String(200), nullable=True)
    year = db.Column(db.String(10), nullable=True)
    poster_url = db.Column(db.String(500), nullable=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
