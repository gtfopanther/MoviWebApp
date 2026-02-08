import os
from typing import Tuple, Optional

import requests
from flask import Flask, flash, redirect, render_template, request, url_for
from dotenv import load_dotenv

from data_manager import DataManager
from models import db


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-key")

BASE_DIR = os.path.dirname(__file__)
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DATABASE_URL = "sqlite:///" + os.path.join(BASE_DIR, "data", "movies.db")

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
manager = DataManager(db)

with app.app_context():
    os.makedirs(os.path.join(BASE_DIR, "data"), exist_ok=True)
    db.create_all()


def fetch_movie_from_omdb(title: str) -> Tuple[Optional[dict], Optional[str]]:
    api_key = os.getenv("OMDB_API_KEY")
    if not api_key:
        return None, "OMDb API key missing. Set OMDB_API_KEY in your environment."

    try:
        response = requests.get(
            "https://www.omdbapi.com/",
            params={"t": title, "apikey": api_key},
            timeout=8,
        )
        response.raise_for_status()
        payload = response.json()
    except requests.RequestException:
        return None, "OMDb request failed. Try again in a moment."

    if payload.get("Response") == "False":
        return None, payload.get("Error", "Movie not found.")

    poster = payload.get("Poster", "")
    if poster == "N/A":
        poster = ""

    return {
        "name": payload.get("Title", title).strip(),
        "year": payload.get("Year", ""),
        "director": payload.get("Director", ""),
        "poster_url": poster,
    }, None


@app.get("/")
def index():
    return render_template("index.html", users=manager.get_users())


@app.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter a user name.")
        else:
            manager.create_user(name)
            flash("User created.")
            return redirect(url_for("index"))

    return render_template("index.html", users=manager.get_users())


@app.get("/users/<int:user_id>/movies")
def user_movies(user_id: int):
    user = manager.get_user(user_id)
    if not user:
        flash("User not found.")
        return redirect(url_for("users"))

    return render_template("movies.html", user=user, movies=manager.get_movies(user_id))


@app.post("/users/<int:user_id>/movies")
def add_movie(user_id: int):
    title = request.form.get("title", "").strip()
    if not title:
        flash("Please enter a movie title.")
        return redirect(url_for("user_movies", user_id=user_id))

    movie_data, error = fetch_movie_from_omdb(title)
    if error:
        flash(error)
        return redirect(url_for("user_movies", user_id=user_id))

    if not manager.add_movie(user_id, movie_data):
        flash("User not found.")
        return redirect(url_for("users"))

    flash("Movie added.")
    return redirect(url_for("user_movies", user_id=user_id))


@app.get("/users/<int:user_id>/movies/<int:movie_id>/edit")
def edit_movie(user_id: int, movie_id: int):
    user = manager.get_user(user_id)
    if not user:
        flash("User not found.")
        return redirect(url_for("users"))

    movie = next((item for item in user.movies if item.id == movie_id), None)
    if not movie:
        flash("Movie not found.")
        return redirect(url_for("user_movies", user_id=user_id))

    return render_template("edit_movie.html", user=user, movie=movie)


@app.post("/users/<int:user_id>/movies/<int:movie_id>/update")
def update_movie(user_id: int, movie_id: int):
    title = request.form.get("title", "").strip()
    if not title:
        flash("Title cannot be empty.")
        return redirect(url_for("edit_movie", user_id=user_id, movie_id=movie_id))

    updates = {
        "name": title,
        "year": request.form.get("year", ""),
        "director": request.form.get("director", ""),
        "poster_url": request.form.get("poster", ""),
    }

    if manager.update_movie(user_id, movie_id, updates):
        flash("Movie updated.")
    else:
        flash("Movie update failed.")

    return redirect(url_for("user_movies", user_id=user_id))


@app.post("/users/<int:user_id>/movies/<int:movie_id>/delete")
def delete_movie(user_id: int, movie_id: int):
    if manager.delete_movie(user_id, movie_id):
        flash("Movie deleted.")
    else:
        flash("Movie delete failed.")

    return redirect(url_for("user_movies", user_id=user_id))


if __name__ == "__main__":
    app.run(debug=True)
