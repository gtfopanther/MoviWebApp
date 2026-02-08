import json
import os

from models import Movie, User, db


def migrate(json_path: str) -> None:
    if not os.path.exists(json_path):
        print(f"No JSON file found at {json_path}. Nothing to migrate.")
        return

    with open(json_path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)

    users = payload.get("users", [])
    if not users:
        print("JSON file has no users. Nothing to migrate.")
        return

    for user in users:
        name = (user.get("name") or "").strip()
        if not name:
            continue

        existing_user = User.query.filter_by(name=name).first()
        if existing_user:
            target_user = existing_user
        else:
            target_user = User(name=name)
            db.session.add(target_user)
            db.session.flush()

        for movie in user.get("movies", []):
            title = (movie.get("title") or movie.get("name") or "").strip()
            if not title:
                continue

            already_exists = Movie.query.filter_by(user_id=target_user.id, name=title).first()
            if already_exists:
                continue

            db.session.add(
                Movie(
                    name=title,
                    year=movie.get("year", ""),
                    director=movie.get("director", ""),
                    poster_url=movie.get("poster") or movie.get("poster_url") or "",
                    user=target_user,
                )
            )

    db.session.commit()
    print("Migration complete.")


if __name__ == "__main__":
    from app import app  # ensures app + db config is loaded

    base_dir = os.path.dirname(__file__)
    json_path = os.path.join(base_dir, "data", "movies.json")

    with app.app_context():
        migrate(json_path)
