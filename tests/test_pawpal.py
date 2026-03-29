"""
Automated test suite for PawPal+ (tests/test_pawpal.py).

Run with:  python -m pytest
"""

import pytest
from datetime import date, timedelta
from pawpal_system import Task, Pet, Owner, Scheduler


# ── Fixtures ───────────────────────────────────────────────────────────────

@pytest.fixture
def today():
    return date.today()


@pytest.fixture
def owner_with_pets(today):
    """Owner with two pets and a handful of tasks, returned as (owner, dog, cat)."""
    owner = Owner("Jordan")
    dog = Pet("Mochi", "dog", age=3)
    cat = Pet("Luna",  "cat", age=5)

    dog.add_task(Task("Morning walk",    "07:30", 20, "high",   "daily",  due_date=today))
    dog.add_task(Task("Afternoon walk",  "14:00", 30, "medium", "once",   due_date=today))
    dog.add_task(Task("Evening feeding", "18:00", 10, "high",   "daily",  due_date=today))

    cat.add_task(Task("Morning feeding", "07:00", 5,  "high",  "daily",  due_date=today))
    cat.add_task(Task("Litter box",      "09:00", 5,  "medium","daily",  due_date=today))

    owner.add_pet(dog)
    owner.add_pet(cat)
    return owner, dog, cat


# ── Task: mark_complete ────────────────────────────────────────────────────

class TestTaskCompletion:
    def test_mark_complete_changes_status(self):
        """Calling mark_complete() must flip is_complete to True."""
        task = Task("Feeding", "08:00", 5, "high")
        assert not task.is_complete
        task.mark_complete()
        assert task.is_complete

    def test_one_time_task_returns_no_next(self):
        """A frequency='once' task should return None from mark_complete."""
        task = Task("Vet visit", "10:00", 60, "high", frequency="once")
        next_task = task.mark_complete()
        assert next_task is None

    def test_daily_task_returns_next_day(self, today):
        """A daily task should generate a successor due the following day."""
        task = Task("Morning walk", "07:30", 20, "high", frequency="daily", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(days=1)
        assert next_task.description == "Morning walk"
        assert not next_task.is_complete

    def test_weekly_task_returns_next_week(self, today):
        """A weekly task should generate a successor due seven days later."""
        task = Task("Flea treatment", "09:00", 5, "low", frequency="weekly", due_date=today)
        next_task = task.mark_complete()
        assert next_task is not None
        assert next_task.due_date == today + timedelta(weeks=1)


# ── Pet: task management ───────────────────────────────────────────────────

class TestPetTaskManagement:
    def test_add_task_increases_count(self):
        """Adding a task to a Pet should increase its task list by one."""
        pet = Pet("Mochi", "dog")
        initial = len(pet.tasks)
        pet.add_task(Task("Walk", "08:00", 20, "high"))
        assert len(pet.tasks) == initial + 1

    def test_add_task_sets_pet_name(self):
        """add_task should stamp the pet's name onto the task."""
        pet = Pet("Luna", "cat")
        task = Task("Feeding", "07:00", 5, "high")
        pet.add_task(task)
        assert task.pet_name == "Luna"

    def test_remove_task_decreases_count(self):
        """remove_task should drop the task from the pet's list."""
        pet = Pet("Mochi", "dog")
        pet.add_task(Task("Walk", "08:00", 20, "high"))
        assert pet.remove_task("Walk") is True
        assert len(pet.tasks) == 0

    def test_remove_nonexistent_task_returns_false(self):
        """remove_task on a missing description should return False."""
        pet = Pet("Mochi", "dog")
        assert pet.remove_task("Ghost task") is False


# ── Scheduler: sorting ─────────────────────────────────────────────────────

class TestSchedulerSorting:
    def test_sort_by_time_orders_correctly(self, owner_with_pets, today):
        """Tasks must come back in chronological HH:MM order."""
        owner, dog, cat = owner_with_pets
        sched = Scheduler(owner)
        sorted_tasks = sched.sort_by_time()
        times = [t.time for t in sorted_tasks]
        assert times == sorted(times)

    def test_sort_with_out_of_order_input(self):
        """sort_by_time must reorder tasks regardless of insertion order."""
        owner = Owner("Alex")
        pet = Pet("Rex", "dog")
        pet.add_task(Task("Afternoon walk", "14:00", 30, "medium"))
        pet.add_task(Task("Morning walk",   "07:00", 20, "high"))
        pet.add_task(Task("Midday nap",     "12:00", 60, "low"))
        owner.add_pet(pet)

        sched = Scheduler(owner)
        sorted_tasks = sched.sort_by_time()
        assert [t.time for t in sorted_tasks] == ["07:00", "12:00", "14:00"]


# ── Scheduler: filtering ───────────────────────────────────────────────────

class TestSchedulerFiltering:
    def test_filter_by_pet_name(self, owner_with_pets):
        """filter_tasks(pet_name=...) should return only that pet's tasks."""
        owner, dog, cat = owner_with_pets
        sched = Scheduler(owner)
        mochi_tasks = sched.filter_tasks(pet_name="Mochi")
        assert all(t.pet_name == "Mochi" for t in mochi_tasks)
        assert len(mochi_tasks) == len(dog.tasks)

    def test_filter_by_completion_status(self, owner_with_pets):
        """filter_tasks(status=False) should return only incomplete tasks."""
        owner, dog, cat = owner_with_pets
        sched = Scheduler(owner)
        pending = sched.filter_tasks(status=False)
        assert all(not t.is_complete for t in pending)

    def test_filter_completed_tasks(self, owner_with_pets):
        """After marking a task complete, filter_tasks(status=True) finds it."""
        owner, dog, cat = owner_with_pets
        sched = Scheduler(owner)
        dog.tasks[0].is_complete = True
        completed = sched.filter_tasks(status=True)
        assert len(completed) == 1


# ── Scheduler: conflict detection ─────────────────────────────────────────

class TestConflictDetection:
    def test_no_conflicts_by_default(self, owner_with_pets):
        """The fixture tasks have no time collisions within the same pet."""
        owner, dog, cat = owner_with_pets
        sched = Scheduler(owner)
        assert sched.detect_conflicts() == []

    def test_detects_same_time_same_pet(self, today):
        """Two tasks for the same pet at the same time triggers a warning."""
        owner = Owner("Sam")
        pet = Pet("Buddy", "dog")
        pet.add_task(Task("Walk",    "08:00", 20, "high",   due_date=today))
        pet.add_task(Task("Feeding", "08:00", 10, "medium", due_date=today))
        owner.add_pet(pet)

        sched = Scheduler(owner)
        warnings = sched.detect_conflicts()
        assert len(warnings) == 1
        assert "Buddy" in warnings[0]
        assert "08:00" in warnings[0]

    def test_same_time_different_pets_no_conflict(self, today):
        """Two different pets at the same time should NOT trigger a conflict."""
        owner = Owner("Sam")
        dog = Pet("Buddy", "dog")
        cat = Pet("Whiskers", "cat")
        dog.add_task(Task("Walk",    "08:00", 20, "high", due_date=today))
        cat.add_task(Task("Feeding", "08:00", 5,  "high", due_date=today))
        owner.add_pet(dog)
        owner.add_pet(cat)

        sched = Scheduler(owner)
        assert sched.detect_conflicts() == []


# ── Scheduler: recurrence via mark_task_complete ───────────────────────────

class TestRecurrence:
    def test_mark_task_complete_adds_to_pet(self, today):
        """Completing a daily task via Scheduler should add tomorrow's task to pet."""
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        task = Task("Morning walk", "07:30", 20, "high", "daily", due_date=today)
        pet.add_task(task)
        owner.add_pet(pet)

        sched = Scheduler(owner)
        sched.mark_task_complete(task)

        assert len(pet.tasks) == 2
        next_task = pet.tasks[1]
        assert next_task.due_date == today + timedelta(days=1)
        assert not next_task.is_complete

    def test_once_task_complete_no_new_task(self, today):
        """Completing a 'once' task should NOT add any new task to the pet."""
        owner = Owner("Jordan")
        pet = Pet("Mochi", "dog")
        task = Task("Vet visit", "10:00", 60, "high", "once", due_date=today)
        pet.add_task(task)
        owner.add_pet(pet)

        sched = Scheduler(owner)
        sched.mark_task_complete(task)

        assert len(pet.tasks) == 1  # no successor added


# ── Scheduler: generate_schedule ──────────────────────────────────────────

class TestGenerateSchedule:
    def test_returns_only_today_tasks(self, today):
        """generate_schedule should exclude tasks due on other dates."""
        owner = Owner("Jordan")
        pet = Pet("Rex", "dog")
        pet.add_task(Task("Today's walk",    "08:00", 20, "high", due_date=today))
        pet.add_task(Task("Tomorrow's walk", "08:00", 20, "high", due_date=today + timedelta(days=1)))
        owner.add_pet(pet)

        sched = Scheduler(owner)
        schedule = sched.generate_schedule(for_date=today)
        assert len(schedule) == 1
        assert schedule[0].description == "Today's walk"

    def test_excludes_completed_tasks(self, today):
        """generate_schedule should not include tasks already marked complete."""
        owner = Owner("Jordan")
        pet = Pet("Rex", "dog")
        task = Task("Walk", "08:00", 20, "high", due_date=today)
        task.is_complete = True
        pet.add_task(task)
        owner.add_pet(pet)

        sched = Scheduler(owner)
        assert sched.generate_schedule(for_date=today) == []

    def test_empty_pet_returns_empty_schedule(self, today):
        """A pet with no tasks should produce an empty schedule."""
        owner = Owner("Jordan")
        owner.add_pet(Pet("Ghost", "cat"))
        sched = Scheduler(owner)
        assert sched.generate_schedule(for_date=today) == []
