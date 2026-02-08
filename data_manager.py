import json
import os
from typing import Dict, List, Optional


class DataManager:
    def __init__(self, data_path: str) -> None:
        self.data_path = data_path
        self._ensure_data_file()

    def _ensure_data_file(self) -> None:
        directory = os.path.dirname(self.data_path)
        if directory and not os.path.exists(directory):
            os.makedirs(directory, exist_ok=True)
        if not os.path.exists(self.data_path):
            with open(self.data_path, "w", encoding="utf-8") as handle:
                json.dump({"users": []}, handle, indent=2)

    def _load(self) -> Dict:
        with open(self.data_path, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def _save(self, data: Dict) -> None:
        with open(self.data_path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2)

    def get_users(self) -> List[Dict]:
        data = self._load()
        return data.get("users", [])

    def add_user(self, name: str) -> Dict:
        data = self._load()
        users = data.setdefault("users", [])
        next_id = max([user["id"] for user in users], default=0) + 1
        user = {"id": next_id, "name": name.strip(), "movies": []}
        users.append(user)
        self._save(data)
        return user

    def get_user(self, user_id: int) -> Optional[Dict]:
        return next((user for user in self.get_users() if user["id"] == user_id), None)

    def get_movies(self, user_id: int) -> List[Dict]:
        user = self.get_user(user_id)
        if not user:
            return []
        return user.get("movies", [])

    def add_movie(self, user_id: int, movie: Dict) -> Optional[Dict]:
        data = self._load()
        for user in data.get("users", []):
            if user["id"] == user_id:
                movies = user.setdefault("movies", [])
                next_id = max([item["id"] for item in movies], default=0) + 1
                movie_record = {
                    "id": next_id,
                    "title": movie.get("title", "").strip(),
                    "year": movie.get("year", ""),
                    "director": movie.get("director", ""),
                    "poster": movie.get("poster", ""),
                }
                movies.append(movie_record)
                self._save(data)
                return movie_record
        return None

    def update_movie(self, user_id: int, movie_id: int, updates: Dict) -> bool:
        data = self._load()
        for user in data.get("users", []):
            if user["id"] == user_id:
                for movie in user.get("movies", []):
                    if movie["id"] == movie_id:
                        for key in ["title", "year", "director", "poster"]:
                            if key in updates:
                                value = updates[key]
                                if isinstance(value, str):
                                    value = value.strip()
                                movie[key] = value
                        self._save(data)
                        return True
        return False

    def delete_movie(self, user_id: int, movie_id: int) -> bool:
        data = self._load()
        for user in data.get("users", []):
            if user["id"] == user_id:
                movies = user.get("movies", [])
                before = len(movies)
                user["movies"] = [movie for movie in movies if movie["id"] != movie_id]
                if len(user["movies"]) != before:
                    self._save(data)
                    return True
        return False
