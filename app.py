from datetime import datetime, date, timedelta

import streamlit as st

from src import data_utils
from src.data_utils import get_workouts_by_routine_dfs, get_workouts_by_exercise_df, exercise_name_df, style_df, \
    change_in_one_rep_max, get_workout_uuids__in_time_range, change_in_heaviest_weight
from src.hevy.updater import process_new_workout_events

st.set_page_config("Periodiq")
st.set_page_config(layout="wide")
st.logo('images/periodiq-logo.png', size='large')

dashboard_view, workout_view, exercise_view, settings_view = st.tabs(
    ["Dashboard", "Workouts", "Exercises", "Settings"]
)

priority_exercises = [
    "Squat (Barbell)",
    "Deadlift (Barbell)",
    "Deadlift (Trap bar)",
    "Bench Press (Barbell)",
]

with dashboard_view:
    st.write("#### One Rep Max")
    one_rm_cols = st.columns(len(priority_exercises))
    for i, col in enumerate(one_rm_cols):
        exercise = priority_exercises[i]
        one_rm, one_rm_change = change_in_one_rep_max(exercise)
        col.metric(
            f"{exercise}",
            one_rm,
            delta=one_rm_change,
            help=f"Best {exercise} 1RM in last 3 months and change to prior 3 months",
            label_visibility="visible",
            border=True,
            width="stretch"
        )

    st.write("#### Heaviest Weight")
    heaviest_weight_cols = st.columns(len(priority_exercises))
    for i, col in enumerate(heaviest_weight_cols):
        exercise = priority_exercises[i]
        heaviest_weight, heaviest_weight_change = change_in_heaviest_weight(exercise)
        col.metric(
            f"{exercise}",
            heaviest_weight,
            delta=heaviest_weight_change,
            help=f"Heaviest weight {exercise} in last 3 months and change to prior 3 months",
            label_visibility="visible",
            border=True,
            width="stretch"
        )

with workout_view:

    show_cols = ['title', 'start_time', 'end_time']

    workout_df = data_utils.workouts_to_df()

    column_configuration = {
        "title": st.column_config.TextColumn(
            "Title", max_chars=100, width="medium"
        ),
        "start_time": st.column_config.DatetimeColumn(
            "Start Time",
            width="medium",
        ),
        "end_time": st.column_config.DatetimeColumn(
            "End Time",
            width="medium",
        ),
    }

    workouts = st.dataframe(
        workout_df[show_cols],
        column_config=column_configuration,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        height=200
    )

    selected_workouts = workouts.selection.rows
    filtered_df = workout_df[["uuid"] + show_cols].iloc[selected_workouts]

    uuids = list(filtered_df.uuid.unique())

    if len(filtered_df) > 0:
        dfs = get_workouts_by_routine_dfs(uuids)
        for g, df in dfs.items():
            st.write(g)
            st.dataframe(
                df,
                column_config={
                    "_index": st.column_config.Column("Exercise", width="medium")
                },
                use_container_width=False
            )


with exercise_view:
    today = date.today()
    past_90 = today - timedelta(days=90)

    date_range = st.date_input(
        "Date range",
        (past_90, today),
        max_value=today,
        format="MM/DD/YYYY",
        label_visibility="hidden"
    )

    time_range_uuids = get_workout_uuids__in_time_range(date_range[0], date_range[1])
    exercise_name_df = exercise_name_df(time_range_uuids)

    exercises_df = st.dataframe(
        exercise_name_df,
        use_container_width=True,
        hide_index=True,
        on_select="rerun",
        selection_mode="multi-row",
        height=200
    )
    selected_exercises = exercises_df.selection.rows

    if selected_exercises:
        ex_df = get_workouts_by_exercise_df(time_range_uuids)
        ex_df_filtered = (
            ex_df.loc[list(exercise_name_df.iloc[selected_exercises]['Exercise'])]
            .dropna(axis=1, how='all')
        )
        ex_df_styled = style_df(ex_df_filtered)

        if len(ex_df_filtered) > 0:
            st.dataframe(
                ex_df_styled,
                column_config={
                    "_index": st.column_config.Column("Exercise", width="medium")
                },
                use_container_width=False,
            )


with settings_view:
    st.write("Fetch latest workout data from Hevy")
    st.button(
        label="Refresh data",
        on_click=process_new_workout_events
    )