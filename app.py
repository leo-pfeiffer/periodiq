import streamlit as st

from src import data_utils
from src.data_utils import get_all_dfs
from src.hevy.updater import process_new_workout_events

st.set_page_config(layout="wide")

select, compare = st.tabs(["Select members", "Compare selected"])

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

    st.dataframe(
        filtered_df,
        column_config=column_configuration,
        use_container_width=True,
    )

with compare:

    uuids = list(filtered_df.uuid.unique())
    dfs = get_all_dfs(uuids)
    for g, df in dfs.items():
        st.write(g)
        st.dataframe(
            df,
            column_config={
                "_index": st.column_config.Column("Exercise", width="medium")
            },
            use_container_width=False
        )
