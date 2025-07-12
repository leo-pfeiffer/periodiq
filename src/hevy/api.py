from datetime import datetime
import requests
from requests import Response

from src.config import CONFIG


class HevyAPI:
    BASE_URL = "https://api.hevyapp.com/v1"
    API_KEY = CONFIG["HEVY_API_KEY"]
    _PAGE_SIZE = 10

    @classmethod
    def _paginate(cls, path: str, data_key: str, extra_params: dict[str, any] | None = None) -> list[dict]:
        items: list[dict] = []
        current_page = 1

        params = {"page": current_page, "pageSize": cls._PAGE_SIZE}
        if extra_params:
            params.update(extra_params)

        def _get_page(page: int) -> Response:
            params["page"] = page
            response = requests.get(
                f"{cls.BASE_URL}/{path}",
                headers={"api-key": cls.API_KEY},
                params=params
            )
            response.raise_for_status()
            return response

        # fetch first page to get page_count
        first_resp = _get_page(current_page)
        data = first_resp.json()
        page_count = data.get("page_count", 0)
        items.extend(data.get(data_key, []) or [])

        # fetch remaining pages
        while current_page < page_count:
            current_page += 1
            resp = _get_page(current_page)
            items.extend(resp.json().get(data_key, []) or [])

        return items

    @classmethod
    def get_workouts_count(cls) -> Response:
        return requests.get(
            f"{cls.BASE_URL}/workouts/count",
            headers={"api-key": cls.API_KEY},
        )

    @classmethod
    def get_workouts(cls) -> list[dict]:
        return cls._paginate("workouts", "workouts")

    @classmethod
    def get_workouts_events(cls, since: datetime) -> list[dict]:
        since_iso = since.isoformat(timespec='seconds')
        return cls._paginate(
            "workouts/events",
            "events",
            extra_params={"since": since_iso}
        )

    @classmethod
    def get_exercise_templates(cls) -> list[dict]:
        return cls._paginate("exercise_templates", "exercise_templates")

    @classmethod
    def get_routines(cls) -> list[dict]:
        return cls._paginate("routines", "routines")
