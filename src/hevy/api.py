import requests

from src.config import CONFIG


class HevyAPI:
    BASE_URL = "https://api.hevyapp.com/v1"
    API_KEY = CONFIG["HEVY_API_KEY"]

    @classmethod
    def get_workouts_count(cls):
        return requests.get(
            f"{HevyAPI.BASE_URL}/workouts/count",
            headers={"api-key": cls.API_KEY},
        )


if __name__ == "__main__":
    print(HevyAPI.get_workouts_count().json())
