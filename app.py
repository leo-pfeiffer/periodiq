import streamlit as st

from src import data_utils
from src.data_utils import get_workouts_by_routine_dfs, get_workouts_by_exercise_df, exercise_name_df, style_df
from src.hevy.updater import process_new_workout_events

st.set_page_config("Periodiq")
st.set_page_config(layout="wide")
st.logo('images/periodiq-logo.png', size='large')

select, by_routine, by_exercise = st.tabs(["Select workouts", "Workouts by routine", "Workouts by exercise"])

with select:

    st.button(
        label="Refresh data",
        on_click=process_new_workout_events
    )

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
    )

    st.header("Selected workouts")

    selected_workouts = workouts.selection.rows
    filtered_df = workout_df[["uuid"] + show_cols].iloc[selected_workouts]

    uuids = list(filtered_df.uuid.unique())

    st.dataframe(
        filtered_df,
        column_config=column_configuration,
        use_container_width=True,
    )

with by_routine:

    if len(filtered_df) == 0:
        st.write("Select workouts first.")

    else:
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


with by_exercise:

    if len(filtered_df) == 0:
        st.write("Select workouts first.")

    else:

        exercise_name_df = exercise_name_df(uuids)
        exercises_df = st.dataframe(
            exercise_name_df,
            use_container_width=True,
            hide_index=True,
            on_select="rerun",
            selection_mode="multi-row",
            height=150
        )
        selected_exercises = exercises_df.selection.rows

        ex_df = get_workouts_by_exercise_df(uuids)
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
