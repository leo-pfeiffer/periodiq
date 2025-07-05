from datetime import datetime, date, timedelta

import pandas as pd
from sqlalchemy import select, func
from sqlalchemy.orm import selectinload

from src.db.connection import SessionLocal
from src.db.models import Workout, WorkoutExercise, WorkoutSet
from src.db.utils import orm_to_dict

UNCATEGORIZED = "UNCATEGORIZED"
KG_TO_LBS = 2.20462


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
            .order_by(Workout.start_time)
            .options(
                selectinload(Workout.exercises)
                .selectinload(WorkoutExercise.sets)
            )
        )
        workouts = session.execute(stmt).scalars().all()
        return [orm_to_dict(w) for w in workouts]


def get_workout_uuids__in_time_range(start_date: date, end_date: date) -> list[str]:
    with SessionLocal() as session:
        stmt = (
            select(Workout.uuid)
            .where(
                Workout.start_time >= start_date,
                Workout.start_time <= end_date
            )
            .order_by(Workout.start_time)
        )
        return [x for x in session.execute(stmt).scalars().all()]


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


def exercises_of_workouts(workouts):
    exercises = []
    for w in workouts:
        exercises.extend(w['exercises'])
    sorted_exercises = sorted(exercises, key=lambda e: e["index"])
    return list(dict.fromkeys([e["title"] for e in sorted_exercises]))


def exercises_of_group(grouped):
    return {
        group: exercises_of_workouts(workouts)
        for group, workouts in grouped.items()
    }


def _get_exercise_from_workout(exercise, workout):
    for gex in workout['exercises']:
        if exercise == gex['title']:
            return gex
    return None


def _pretty_timestamp(iso_string: str):
    dt_object = datetime.fromisoformat(iso_string)
    return dt_object.strftime("%Y-%m-%d %H:%M")


def _get_max_sets_for_workout(workout):
    return max([len(e['sets']) for e in workout['exercises']])


def get_workout_df_for_routine(exercises, workouts):
    rows = {e: [] for e in exercises}
    columns_set = set()
    columns = []

    for workout in workouts:
        start_time = _pretty_timestamp(workout['start_time'])
        max_sets = _get_max_sets_for_workout(workout)

        for ex in exercises:
            gex = _get_exercise_from_workout(ex, workout)
            set_values = []
            if gex:
                for idx, s in enumerate(gex['sets']):
                    col_name1 = (start_time, f'W {idx+1}')
                    col_name2 = (start_time, f'R {idx+1}')

                    if col_name1 not in columns_set:
                        columns_set.add(col_name1)
                        columns.append(col_name1)
                    if col_name2 not in columns_set:
                        columns_set.add(col_name2)
                        columns.append(col_name2)

                    weight_kg = s.get('weight_kg') or 0
                    reps = s.get('reps') or 0

                    set_values.append(int(weight_kg * KG_TO_LBS))
                    set_values.append(int(reps))

            n_none_sets = max_sets * 2 - len(set_values)
            set_values.extend([None] * n_none_sets)
            rows[ex].extend(set_values)

    df = pd.DataFrame.from_dict(data=rows, orient='index').astype('Int64')
    pd.set_option('display.max_rows', None)
    pd.set_option('display.max_columns', None)
    df.columns = pd.MultiIndex.from_tuples(tuples=columns)
    return df


def style_df(df):
    shaded_cols = [c for i, c in enumerate(list(dict.fromkeys([c[0] for c in df.columns]))) if i % 2 != 0]

    styler = (
        df.style.apply(lambda c: ["background-color: rgba(255, 75, 75, 0.1);"] * len(c), subset=shaded_cols)
    )

    return styler


def get_workout_df_by_exercise(workouts):
    exercises = exercises_of_workouts(workouts)
    return get_workout_df_for_routine(exercises, workouts)


def get_workouts_by_routine_dfs(uuids) -> dict:
    if not uuids:
        return {}
    workouts = get_workouts_with_details(uuids)
    grouped_workouts = group_and_sort_workouts(workouts)
    guessed_order = guess_order_of_workout_days(grouped_workouts)
    group_exercises = exercises_of_group(grouped_workouts)

    return {
        g: style_df(get_workout_df_for_routine(group_exercises[g], grouped_workouts[g]))
        for g in guessed_order
    }


def get_workouts_by_exercise_df(uuids):
    if not uuids:
        return None
    workouts = get_workouts_with_details(uuids)
    return get_workout_df_by_exercise(workouts)


def exercise_name_df(uuids):
    workouts = get_workouts_with_details(uuids)
    exercises = exercises_of_workouts(workouts)
    return pd.DataFrame({"Exercise": sorted(exercises)})


def _get_one_rep_max_last(exercise: str, start_date: date, end_date: date):
    with SessionLocal() as session:
        # Epley 1RM formula
        one_rm_expr = WorkoutSet.weight_kg * (
                1 + (WorkoutSet.reps / 30)
        )

        stmt = (
            select(func.max(one_rm_expr))
            .select_from(WorkoutSet)
            .join(WorkoutExercise)
            .join(Workout)
            .where(
                WorkoutExercise.title == exercise,
                WorkoutSet.reps != None,
                WorkoutSet.reps > 0,
                WorkoutSet.weight_kg != None,
                Workout.start_time >= start_date,
                Workout.start_time <= end_date
            )
        )

        return session.execute(stmt).scalar()


def get_one_rep_max_last_three_months(exercise):
    end_date = date.today()
    start_date = end_date - timedelta(days=90)
    return _get_one_rep_max_last(exercise, start_date, end_date)


def get_one_rep_max_prev_three_months(exercise):
    end_date = date.today() - timedelta(days=90)
    start_date = end_date - timedelta(days=90)
    return _get_one_rep_max_last(exercise, start_date, end_date)


def change_in_one_rep_max(exercise) -> tuple:
    last_three_months = int(get_one_rep_max_last_three_months(exercise) * KG_TO_LBS)
    prev_three_months = int(get_one_rep_max_prev_three_months(exercise) * KG_TO_LBS)
    return last_three_months, last_three_months - prev_three_months
