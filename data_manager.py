from typing import List, Optional

from models import Movie, User, db


class DataManager:
    def __init__(self, database) -> None:
        self.db = database

    def create_user(self, name: str) -> User:
        user = User(name=name.strip())
        self.db.session.add(user)
        self.db.session.commit()
        return user

    def get_users(self) -> List[User]:
        return User.query.all()

    def get_user(self, user_id: int) -> Optional[User]:
        return User.query.get(user_id)

    def get_movies(self, user_id: int) -> List[Movie]:
        user = self.get_user(user_id)
        if not user:
            return []
        return list(user.movies)

    def add_movie(self, user_id: int, movie_data: dict) -> Optional[Movie]:
        user = self.get_user(user_id)
        if not user:
            return None

        movie = Movie(
            name=movie_data.get("name", "").strip(),
            year=movie_data.get("year", ""),
            director=movie_data.get("director", ""),
            poster_url=movie_data.get("poster_url", ""),
            user=user,
        )
        self.db.session.add(movie)
        self.db.session.commit()
        return movie

    def update_movie(self, user_id: int, movie_id: int, updates: dict) -> bool:
        movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first()
        if not movie:
            return False

        if "name" in updates:
            movie.name = updates["name"].strip()
        if "year" in updates:
            movie.year = updates["year"]
        if "director" in updates:
            movie.director = updates["director"]
        if "poster_url" in updates:
            movie.poster_url = updates["poster_url"]

        self.db.session.commit()
        return True

    def delete_movie(self, user_id: int, movie_id: int) -> bool:
        movie = Movie.query.filter_by(id=movie_id, user_id=user_id).first()
        if not movie:
            return False

        self.db.session.delete(movie)
        self.db.session.commit()
        return True
