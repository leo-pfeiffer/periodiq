import pandas as pd
from sqlalchemy import select
from sqlalchemy.orm import selectinload

from src.db.connection import SessionLocal
from src.db.models import Workout, WorkoutExercise
from src.db.utils import orm_to_dict

UNCATEGORIZED = "UNCATEGORIZED"


def workouts_to_df() -> pd.DataFrame:
    """Return the workouts table as a pandas DataFrame."""
    with SessionLocal() as session:
        stmt = select(Workout).order_by(Workout.start_time.desc())
        workouts = session.execute(stmt).scalars().all()

        # turn each Workout into a dict of column -> value
        rows = [
            {col.name: getattr(w, col.name) for col in Workout.__table__.columns}
            for w in workouts
        ]

    return pd.DataFrame(rows)


def get_workouts_with_details(uuids: list[str]) -> list[dict]:
    with SessionLocal() as session:
        stmt = (
            select(Workout)
            .where(Workout.uuid.in_(uuids))
            .options(
                selectinload(Workout.exercises)
                .selectinload(WorkoutExercise.sets)
            )
        )
        workouts = session.execute(stmt).scalars().all()
        return [orm_to_dict(w) for w in workouts]


# uuids = [
#     "25c2ed8b-c0b8-4e2a-b99d-3215cb054b40",
#     "dde076a7-899f-4e7c-8924-3a346ba6299a",
#     "99509426-ad2d-4acb-b1bb-6bcd8f67aa07",
#     "fbaff451-1673-429e-954c-6993e86f8e9a",
#     "b5fe1899-6a32-4d61-9d4e-bd00b3db72a3",
#     "5d3de98f-c5db-4a38-afaf-4bc52e5589b8",
#     "0222e624-2af0-4402-b773-8e75136e08fa",
#     "ccbb802f-2ee7-4067-b9e6-1d29fe7df4f2",
#     "62d07456-b243-4808-b40b-1174a47326ed",
#     "d9336e41-dcdd-4e2e-8dda-ffd34c580eec",
#     "a0a0df4b-0e43-4774-b2ec-cf17e3dfe9a6",
#     "2ebdbe35-0039-42da-8d2b-edea8b3c2d9b",
#     "c6b1d36d-dfe8-4386-b6b8-9eee0dad1ccd"
# ]


def get_workout_day(w):
    title = w.get('title', '')
    try:
        title_parts = title.split('//')
        result = title_parts[1].strip()
    except IndexError:
        result = UNCATEGORIZED
    if not result:
        result = UNCATEGORIZED
    return result


def guess_order_of_workout_days(grouped):
    def _earliest_time(workout_list):
        return sorted(workout_list, key=lambda w: w['start_time'])[0]['start_time']

    order = [
        k for k, _ in
        sorted(
            [*grouped.items()],
            key=lambda item: _earliest_time(item[1])
        )
    ]

    # always put UNCATEGORIZED last
    if UNCATEGORIZED in order:
        order.remove(UNCATEGORIZED)
        order.append(UNCATEGORIZED)

    return order


def group_and_sort_workouts(workouts):
    grouped_workouts = {}
    for workout in workouts:
        workout_day = get_workout_day(workout)
        if workout_day in grouped_workouts:
            grouped_workouts[workout_day].append(workout)
        else:
            grouped_workouts[workout_day] = [workout]
    for group in grouped_workouts.keys():
        grouped_workouts[group] = sorted(grouped_workouts[group], key=lambda w: w["start_time"])
    return grouped_workouts


def exercises_of_group(grouped):
    exercises = {}
    for group, workouts in grouped.items():
        group_ex = []
        for w in workouts:
            group_ex.extend(w['exercises'])
        group_ex = sorted(group_ex, key=lambda e: e["index"])
        group_ex_names = list(dict.fromkeys([e["title"] for e in group_ex]))
        exercises[group] = group_ex_names
    return exercises


def _get_exercise_from_workout(exercise, workout):
    for gex in workout['exercises']:
        if exercise == gex['title']:
            return gex
    return None


def _get_max_sets_for_workout(workout):
    return max([len(e['sets']) for e in workout['exercises']])


def get_df(exercises, workouts):
    rows = {e: [] for e in exercises}
    columns_set = set()
    columns = []

    for workout in workouts:
        max_sets = _get_max_sets_for_workout(workout)

        for ex in exercises:
            gex = _get_exercise_from_workout(ex, workout)
            if gex:
                for s in gex['sets']:

                    idx = s['index'] + 1
                    col_name1 = (workout['start_time'], f'SET {idx}', f"Weight")
                    col_name2 = (workout['start_time'], f'SET {idx}', f"Reps")

                    if col_name1 not in columns_set:
                        columns_set.add(col_name1)
                        columns.append(col_name1)
                    if col_name2 not in columns_set:
                        columns_set.add(col_name2)
                        columns.append(col_name2)

                    weight_kg = s.get('weight_kg') or 0
                    reps = s.get('reps') or 0

                    rows[ex].append(int(weight_kg * 2.20462))
                    rows[ex].append(int(reps))

            else:
                rows[ex].extend([None] * max_sets * 2)

    df = pd.DataFrame.from_dict(data=rows, orient='index').astype('Int64')

    df.columns = pd.MultiIndex.from_tuples(tuples=columns)

    shaded_cols = [c for i, c in enumerate(list(dict.fromkeys([c[0] for c in df.columns]))) if i % 2 != 0]

    styler = (
        df.style.apply(lambda c: ["background-color: rgba(0, 123, 255, 0.1);"] * len(c), subset=shaded_cols)
    )

    return styler


def get_all_dfs(uuids) -> dict:
    workouts = get_workouts_with_details(uuids)
    grouped_workouts = group_and_sort_workouts(workouts)
    guessed_order = guess_order_of_workout_days(grouped_workouts)
    group_exercises = exercises_of_group(grouped_workouts)

    return {
        g: get_df(group_exercises[g], grouped_workouts[g])
        for g in guessed_order
    }
