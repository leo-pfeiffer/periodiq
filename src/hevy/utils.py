from dateutil.parser import isoparse

from src.db.models import Workout, WorkoutExercise, WorkoutSet, ExerciseTemplate, Routine, RoutineExercise, RoutineSet


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


def parse_exercise_template(payload: dict) -> ExerciseTemplate:
    return ExerciseTemplate(
        uuid=payload["id"],
        title=payload["title"],
        type=payload["type"],
        primary_muscle_group=payload["primary_muscle_group"],
        secondary_muscle_groups=payload.get("secondary_muscle_groups"),
        is_custom=bool(payload["is_custom"])
    )


def parse_routine(payload: dict) -> Routine:
    routine = Routine(
        id=payload["id"],
        title=payload["title"],
        folder_id=payload.get("folder_id"),
        updated_at=isoparse(payload["updated_at"]),
        created_at=isoparse(payload["created_at"]),
    )

    # ----- nested exercises -----
    for ex in payload.get("exercises", []):
        exercise = RoutineExercise(
            index=ex["index"],
            title=ex["title"],
            rest_seconds=ex["rest_seconds"],
            notes=ex.get("notes"),
            exercise_template_id=ex.get("exercise_template_id"),
            supersets_id=ex.get("superset_id"),
        )

        # ----- nested sets -----
        for st in ex.get("sets", []):
            routine_set = RoutineSet(
                index=st["index"],
                type=st["type"],
                weight_kg=st.get("weight_kg"),
                reps=st.get("reps"),
                distance_meters=st.get("distance_meters"),
                duration_seconds=st.get("duration_seconds"),
                rpe=st.get("rpe"),
                custom_metric=st.get("custom_metric"),
            )
            exercise.sets.append(routine_set)

        routine.exercises.append(exercise)

    return routine


def sort_workouts(workouts: list[Workout]):
    return sorted(workouts, key=lambda w: w.start_time)
