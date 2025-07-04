import logging
from datetime import timedelta

from sqlalchemy import select, func, delete

from src.db.connection import SessionLocal
from src.db.models import Workout
from src.hevy.api import HevyAPI
from src.hevy.utils import parse_workout, sort_workouts


def insert_workouts(workouts: list[dict]) -> None:
    with SessionLocal() as session:
        workouts = [parse_workout(w) for w in workouts]
        session.add_all(sort_workouts(workouts))
        session.commit()


def get_most_recent_update():
    with SessionLocal() as session:
        stmt = select(func.max(Workout.updated_at))
        return session.execute(stmt).scalar_one()


def process_new_workout_events():
    last_update = get_most_recent_update()

    if not last_update:
        logging.info("Could not find last update time, likely because there are no workouts yet.")
        return

    workout_events = HevyAPI.get_workouts_events(since=last_update + timedelta(seconds=1))
    if not workout_events:
        logging.info("No new updates.")
        return

    grouped_events = {"updated": [], "deleted": []}

    for event in workout_events:
        event_type = event["type"]
        workout = event["workout"]
        if event_type in grouped_events.keys():
            grouped_events[event_type].append(workout)

    # Delete all workouts that have been updated or deleted.
    # For updates, re-insert the updated version
    with SessionLocal() as session, session.begin():
        # delete all workouts that had events
        event_ids_to_delete = {w["id"] for w in grouped_events["deleted"] + grouped_events["updated"]}
        delete_stmt = delete(Workout).where(Workout.uuid.in_(event_ids_to_delete))
        session.execute(delete_stmt)

        # re-insert updated events
        workouts = [parse_workout(w) for w in grouped_events["updated"]]
        session.add_all(sort_workouts(workouts))
