import os
from typing import Tuple, Optional

import requests
from flask import Flask, flash, redirect, render_template, request, url_for
from dotenv import load_dotenv

from data_manager import DataManager


load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET", "dev-secret-key")

DATA_PATH = os.path.join(os.path.dirname(__file__), "data", "movies.json")
manager = DataManager(DATA_PATH)


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
        "title": payload.get("Title", title).strip(),
        "year": payload.get("Year", ""),
        "director": payload.get("Director", ""),
        "poster": poster,
    }, None


@app.get("/")
def index():
    return redirect(url_for("users"))


@app.route("/users", methods=["GET", "POST"])
def users():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        if not name:
            flash("Please enter a user name.")
        else:
            manager.add_user(name)
            flash("User created.")
            return redirect(url_for("users"))

    return render_template("users.html", users=manager.get_users())


@app.get("/users/<int:user_id>/movies")
def user_movies(user_id: int):
    user = manager.get_user(user_id)
    if not user:
        flash("User not found.")
        return redirect(url_for("users"))

    return render_template("movies.html", user=user, movies=user.get("movies", []))


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

    manager.add_movie(user_id, movie_data)
    flash("Movie added.")
    return redirect(url_for("user_movies", user_id=user_id))


@app.get("/users/<int:user_id>/movies/<int:movie_id>/edit")
def edit_movie(user_id: int, movie_id: int):
    user = manager.get_user(user_id)
    if not user:
        flash("User not found.")
        return redirect(url_for("users"))

    movie = next((item for item in user.get("movies", []) if item["id"] == movie_id), None)
    if not movie:
        flash("Movie not found.")
        return redirect(url_for("user_movies", user_id=user_id))

    return render_template("edit_movie.html", user=user, movie=movie)


@app.post("/users/<int:user_id>/movies/<int:movie_id>/edit")
def update_movie(user_id: int, movie_id: int):
    updates = {
        "title": request.form.get("title", ""),
        "year": request.form.get("year", ""),
        "director": request.form.get("director", ""),
        "poster": request.form.get("poster", ""),
    }

    if not updates["title"].strip():
        flash("Title cannot be empty.")
        return redirect(url_for("edit_movie", user_id=user_id, movie_id=movie_id))

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
