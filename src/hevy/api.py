from datetime import datetime

import requests
from requests import Response

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

    @classmethod
    def get_workouts(cls):
        workouts = []
        current_page = 1
        page_size = 30

        def _get_page(page: int):
            return requests.get(
                f"{HevyAPI.BASE_URL}/workouts",
                headers={"api-key": cls.API_KEY},
                params={"page": page, "pageSize": page_size}
            )

        def _process_response(resp: Response):
            _workouts = resp.json().get("workouts")
            if _workouts:
                workouts.extend(_workouts)

        first_page = _get_page(current_page)
        page_count = first_page.json().get("page_count", 0)

        _process_response(first_page)

        while current_page < page_count:
            current_page += 1
            next_page = _get_page(current_page)
            _process_response(next_page)

        return workouts

    @classmethod
    def get_workouts_events(cls, since: datetime):
        since_iso = since.isoformat(timespec='seconds')
        workout_events = []
        current_page = 1
        page_size = 30

        def _get_page(page: int):
            return requests.get(
                f"{HevyAPI.BASE_URL}/workouts/events",
                headers={"api-key": cls.API_KEY},
                params={
                    "page": page,
                    "pageSize": page_size,
                    "since": since_iso
                }
            )

        def _process_response(resp: Response):
            _workouts = resp.json().get("events")
            if _workouts:
                workout_events.extend(_workouts)

        first_page = _get_page(current_page)
        page_count = first_page.json().get("page_count", 0)

        _process_response(first_page)

        while current_page < page_count:
            current_page += 1
            next_page = _get_page(current_page)
            _process_response(next_page)

        return workout_events

    @classmethod
    def get_exercise_templates(cls):
        exercise_templates = []
        current_page = 1
        page_size = 30

        def _get_page(page: int):
            return requests.get(
                f"{HevyAPI.BASE_URL}/exercise_templates",
                headers={"api-key": cls.API_KEY},
                params={
                    "page": page,
                    "pageSize": page_size,
                }
            )

        def _process_response(resp: Response):
            _exercise_templates = resp.json().get("exercise_templates")
            if _exercise_templates:
                exercise_templates.extend(_exercise_templates)

        first_page = _get_page(current_page)
        page_count = first_page.json().get("page_count", 0)

        _process_response(first_page)

        while current_page < page_count:
            current_page += 1
            next_page = _get_page(current_page)
            _process_response(next_page)

        return exercise_templates
