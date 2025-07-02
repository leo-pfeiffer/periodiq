from dateutil.parser import isoparse

from src.db.models import Workout, WorkoutExercise, WorkoutSet


def parse_workout(payload: dict) -> Workout:
    workout = Workout(
        uuid=payload["id"],
        title=payload["title"],
        description=payload.get("description"),
        start_time=isoparse(payload["start_time"]),
        end_time=isoparse(payload["end_time"]),
        updated_at=isoparse(payload["updated_at"]),
        created_at=isoparse(payload["created_at"]),
    )

    # ----- nested exercises -----
    for ex in payload.get("exercises", []):
        exercise = WorkoutExercise(
            index=ex["index"],
            title=ex["title"],
            notes=ex.get("notes"),
            exercise_template_id=ex["exercise_template_id"],
            supersets_id=ex.get("superset_id"),
        )

        # ----- nested sets -----
        for st in ex.get("sets", []):
            workout_set = WorkoutSet(
                index=st["index"],
                type=st["type"],
                weight_kg=st["weight_kg"],
                reps=st["reps"],
                distance_meters=st["distance_meters"],
                duration_seconds=st["duration_seconds"],
                rpe=st["rpe"],
                custom_metric=st["custom_metric"],
            )
            exercise.sets.append(workout_set)

        workout.exercises.append(exercise)

    return workout


def sort_workouts(workouts: list[Workout]):
    return sorted(workouts, key=lambda w: w.start_time)
