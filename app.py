"""
app.py — PawPal+ Streamlit UI.

Connects the Owner / Pet / Task / Scheduler logic layer to an interactive UI.
Run with:  streamlit run app.py
"""

import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="wide")
st.title("🐾 PawPal+")
st.caption("Your smart pet care planning assistant")

# ── Session state bootstrap ─────────────────────────────────────────────────
# st.session_state acts as persistent memory across reruns within a browser session.

if "owner" not in st.session_state:
    st.session_state.owner = None      # set during owner setup
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None

# ── Sidebar: Owner + Pet management ─────────────────────────────────────────

with st.sidebar:
    st.header("Owner Setup")

    owner_name = st.text_input("Your name", value="Jordan")
    if st.button("Set / update owner"):
        if st.session_state.owner is None:
            st.session_state.owner = Owner(owner_name)
        else:
            st.session_state.owner.name = owner_name
        st.session_state.scheduler = Scheduler(st.session_state.owner)
        st.success(f"Owner set to {owner_name}")

    if st.session_state.owner:
        st.divider()
        st.subheader("Add a Pet")
        with st.form("add_pet_form", clear_on_submit=True):
            pet_name    = st.text_input("Pet name",  value="Mochi")
            pet_species = st.selectbox("Species", ["dog", "cat", "rabbit", "bird", "other"])
            pet_age     = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
            submitted   = st.form_submit_button("Add pet")
        if submitted:
            # Prevent duplicate pet names
            existing = [p.name for p in st.session_state.owner.pets]
            if pet_name in existing:
                st.warning(f"A pet named '{pet_name}' already exists.")
            else:
                new_pet = Pet(pet_name, pet_species, pet_age)
                st.session_state.owner.add_pet(new_pet)
                st.success(f"Added {pet_name} the {pet_species}!")

        # Registered pets
        if st.session_state.owner.pets:
            st.divider()
            st.subheader("Your Pets")
            for p in st.session_state.owner.pets:
                st.write(f"**{p.name}** ({p.species}, {p.age} yr) — {len(p.tasks)} task(s)")

# ── Main area ────────────────────────────────────────────────────────────────

if st.session_state.owner is None:
    st.info("Use the sidebar to set your name and register your first pet to get started.")
    st.stop()

owner     = st.session_state.owner
scheduler = st.session_state.scheduler

# Guard: need at least one pet
if not owner.pets:
    st.warning("Add at least one pet in the sidebar before scheduling tasks.")
    st.stop()

# ── Tabs ─────────────────────────────────────────────────────────────────────

tab_add, tab_schedule, tab_manage = st.tabs(["Add Task", "Today's Schedule", "Manage Tasks"])

# ── Tab 1: Add a task ─────────────────────────────────────────────────────────

with tab_add:
    st.subheader("Schedule a New Task")
    pet_names = [p.name for p in owner.pets]

    with st.form("add_task_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            selected_pet  = st.selectbox("Pet", pet_names)
            task_desc     = st.text_input("Task description", value="Morning walk")
            task_time     = st.text_input("Time (HH:MM)", value="07:30")
        with col2:
            task_duration = st.number_input("Duration (min)", min_value=1, max_value=480, value=20)
            task_priority = st.selectbox("Priority", ["high", "medium", "low"])
            task_freq     = st.selectbox("Frequency", ["once", "daily", "weekly"])
        task_date = st.date_input("Due date", value=date.today())
        add_submitted = st.form_submit_button("Add task")

    if add_submitted:
        # Basic time format validation
        parts = task_time.split(":")
        valid_time = (
            len(parts) == 2
            and all(p.isdigit() for p in parts)
            and 0 <= int(parts[0]) <= 23
            and 0 <= int(parts[1]) <= 59
        )
        if not valid_time:
            st.error("Please enter time in HH:MM format (e.g. 08:30).")
        else:
            new_task = Task(
                description=task_desc,
                time=task_time,
                duration_minutes=int(task_duration),
                priority=task_priority,
                frequency=task_freq,
                due_date=task_date,
            )
            pet_obj = next(p for p in owner.pets if p.name == selected_pet)
            pet_obj.add_task(new_task)
            st.success(f"Added '{task_desc}' for {selected_pet} at {task_time}.")

            # Surface any newly created conflicts
            conflicts = scheduler.detect_conflicts()
            if conflicts:
                for w in conflicts:
                    st.warning(w)

# ── Tab 2: Today's Schedule ───────────────────────────────────────────────────

with tab_schedule:
    st.subheader(f"Schedule for {date.today().strftime('%A, %B %d %Y')}")

    # Optional pet filter
    filter_pet = st.selectbox(
        "Show tasks for",
        ["All pets"] + [p.name for p in owner.pets],
        key="filter_pet_schedule",
    )

    all_today = scheduler.generate_schedule(for_date=date.today())
    if filter_pet != "All pets":
        all_today = [t for t in all_today if t.pet_name == filter_pet]

    # Conflict banner
    conflicts = scheduler.detect_conflicts()
    if conflicts:
        with st.expander("Scheduling conflicts detected", expanded=True):
            for w in conflicts:
                st.warning(w)

    if not all_today:
        st.info("No pending tasks scheduled for today.")
    else:
        priority_color = {"high": "🔴", "medium": "🟡", "low": "🟢"}

        for i, t in enumerate(all_today):
            col_check, col_info, col_badge = st.columns([1, 6, 2])
            with col_check:
                done = st.checkbox("", key=f"task_{i}_{t.description}_{t.pet_name}_{t.time}")
                if done:
                    next_t = scheduler.mark_task_complete(t)
                    if next_t:
                        st.caption(f"Next: {next_t.due_date}")
            with col_info:
                st.markdown(
                    f"**{t.time}** &nbsp; {t.pet_name} &nbsp;|&nbsp; "
                    f"{t.description} &nbsp; ({t.duration_minutes} min)"
                )
            with col_badge:
                st.markdown(f"{priority_color.get(t.priority, '')} {t.priority}")

        # Summary table
        st.divider()
        st.subheader("Full Summary")
        table_data = [
            {
                "Time": t.time,
                "Pet": t.pet_name,
                "Task": t.description,
                "Duration (min)": t.duration_minutes,
                "Priority": t.priority,
                "Frequency": t.frequency,
            }
            for t in all_today
        ]
        st.table(table_data)

# ── Tab 3: Manage Tasks ────────────────────────────────────────────────────────

with tab_manage:
    st.subheader("All Tasks")

    manage_pet = st.selectbox(
        "Filter by pet",
        ["All pets"] + [p.name for p in owner.pets],
        key="manage_pet_filter",
    )
    manage_status = st.radio("Status", ["Pending", "Completed", "All"], horizontal=True)

    status_map = {"Pending": False, "Completed": True, "All": None}
    pet_filter  = None if manage_pet == "All pets" else manage_pet
    tasks_shown = scheduler.filter_tasks(pet_name=pet_filter, status=status_map[manage_status])
    tasks_shown = scheduler.sort_by_time(tasks_shown)

    if not tasks_shown:
        st.info("No tasks match the current filter.")
    else:
        for t in tasks_shown:
            status_label = "Done" if t.is_complete else "Pending"
            with st.expander(f"{t.time}  {t.pet_name}  —  {t.description}  [{status_label}]"):
                st.write(f"Duration: {t.duration_minutes} min")
                st.write(f"Priority: {t.priority}")
                st.write(f"Frequency: {t.frequency}")
                st.write(f"Due date: {t.due_date}")
                if st.button("Remove task", key=f"remove_{t.pet_name}_{t.description}_{t.time}"):
                    pet_obj = next((p for p in owner.pets if p.name == t.pet_name), None)
                    if pet_obj and pet_obj.remove_task(t.description):
                        st.success(f"Removed '{t.description}'.")
                        st.rerun()
