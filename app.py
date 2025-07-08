from datetime import date, timedelta

import streamlit as st

from src import data_utils
from src.app_utils import st_horizontal
from src.data_utils import get_workouts_by_routine_dfs, get_workouts_by_exercise_df, exercise_name_df, style_df, \
    change_in_one_rep_max, get_workout_uuids__in_time_range, change_in_heaviest_weight, \
    get_weekly_sets_last_three_months, get_routines_df, create_or_update_periodiq_plan, get_periodiq_plans_df, \
    delete_periodiq_plan_by_id
from src.hevy.updater import refresh_data


st.set_page_config("Periodiq")
st.set_page_config(layout="wide")
st.logo('images/periodiq-logo.png', size='large')

dashboard_view, planner_view, workout_view, exercise_view, settings_view = st.tabs(
    ["Dashboard", "Planner", "Workouts", "Exercises", "Settings"]
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

    st.write("#### Sets per Week")
    st.bar_chart(
        get_weekly_sets_last_three_months(),
        x="week_start",
        y="set_count",
        x_label="Week",
        y_label="# Sets",
        color=(255, 75, 75, 0.6)
    )

with planner_view:
    # CREATE NEW PLAN (Modal)
    # 1. Name of the plan
    # 2. Description / Goals
    # 3. Select Hevy Routines to include in this plan
    # 4. Start Date / End Date
    #
    # SELECT / VIEW PLAN
    # 1. Select plan from list
    # -> Shows title and description
    # -> Pulls in all workouts within the time frame of the plan
    # -> All workouts whose name corresponds to plan routines, are grouped together
    # -> All other workouts are grouped as UNCATEGORIZED
    #
    # EDIT PLAN (Modal)
    # 1. Update (name, description, routines, start/end date
    # 2. Delete plan
    #
    # CALENDAR VIEW
    # 1. Shows plans in order (layout tbd)
    # 2. Click on plan should select plan (maybe)

    @st.dialog("Periodiq Plan", width='large')
    def create_plan_modal(
        plan_id=None,
        name=None,
        focus=None,
        start_date=None,
        end_date=None,
        routine_uuids=None
    ):

        plan_name = st.text_input("Name", value=name)
        plan_focus = st.text_input("Focus", value=focus)
        start_date = st.date_input("Start Date", value=start_date)
        end_date = st.date_input("End Date", value=end_date)

        st.write("Routines:")
        routines_df = get_routines_df()

        pre_selected_rows = []
        print(routine_uuids)
        if routine_uuids:
            filtered_uuids = routines_df.uuid.isin(routine_uuids)
            pre_selected_rows = list(filtered_uuids[filtered_uuids].index)

        selected_indices = st.multiselect(
            "Select rows",
            options=routines_df.index.tolist(),
            default=pre_selected_rows,
            format_func=lambda i: f"{routines_df.loc[i, 'title']} (uuid={routines_df.loc[i, 'uuid']})"
        )

        def _selected_routine_uuids():
            return list(routines_df.iloc[selected_indices].uuid.unique())

        with st_horizontal():
            if st.button("Submit"):
                create_or_update_periodiq_plan(
                    periodiq_plan_id=plan_id,
                    name=plan_name,
                    description=plan_focus,
                    start_date=start_date,
                    end_date=end_date,
                    routine_uuids=_selected_routine_uuids()
                )
                st.rerun()
            if st.button("Delete"):
                delete_periodiq_plan_by_id(periodiq_plan_id=plan_id)
                st.rerun()


    with st_horizontal():
        if st.button("Create Plan"):
            create_plan_modal()

        button_slot = st.empty()

    available_periodiq_plans = get_periodiq_plans_df()
    periodiq_plan_df_selector = st.dataframe(
        available_periodiq_plans,
        hide_index=True,
        on_select="rerun",
        selection_mode="single-row",
    )

    if len(periodiq_plan_df_selector.selection.rows) > 0:
        if button_slot.button("Edit"):
            selected_row = available_periodiq_plans.iloc[periodiq_plan_df_selector.selection.rows]
            create_plan_modal(
                plan_id=int(selected_row.id[0]),
                name=selected_row.name[0],
                focus=selected_row.description[0],
                start_date=selected_row.start_date[0],
                end_date=selected_row.end_date[0],
                routine_uuids=selected_row.routines[0]
            )
    else:
        button_slot.empty()


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
        on_click=refresh_data
    )