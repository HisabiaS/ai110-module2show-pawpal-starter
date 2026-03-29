"""
PawPal+ logic layer.

Classes
-------
Task    - A single pet care activity.
Pet     - A pet with a list of tasks.
Owner   - An owner who manages one or more pets.
Scheduler - Retrieves, sorts, filters, and schedules tasks across all pets.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """Represents a single pet care activity."""

    description: str
    time: str                   # "HH:MM" 24-hour format
    duration_minutes: int
    priority: str               # "low" | "medium" | "high"
    frequency: str = "once"     # "once" | "daily" | "weekly"
    is_complete: bool = False
    due_date: date = field(default_factory=date.today)
    pet_name: str = ""

    def mark_complete(self) -> Optional["Task"]:
        """Mark task complete. Returns next occurrence for recurring tasks, else None."""
        self.is_complete = True
        if self.frequency == "daily":
            return Task(
                description=self.description,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(days=1),
                pet_name=self.pet_name,
            )
        if self.frequency == "weekly":
            return Task(
                description=self.description,
                time=self.time,
                duration_minutes=self.duration_minutes,
                priority=self.priority,
                frequency=self.frequency,
                due_date=self.due_date + timedelta(weeks=1),
                pet_name=self.pet_name,
            )
        return None


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

class Pet:
    """Stores pet details and a list of care tasks."""

    def __init__(self, name: str, species: str, age: int = 0) -> None:
        self.name = name
        self.species = species
        self.age = age
        self.tasks: list[Task] = []

    def add_task(self, task: Task) -> None:
        """Attach task to this pet and record the pet's name on the task."""
        task.pet_name = self.name
        self.tasks.append(task)

    def remove_task(self, description: str) -> bool:
        """Remove the first task matching description. Returns True if removed."""
        for i, t in enumerate(self.tasks):
            if t.description == description:
                self.tasks.pop(i)
                return True
        return False

    def __repr__(self) -> str:
        return f"Pet(name={self.name!r}, species={self.species!r}, tasks={len(self.tasks)})"


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Manages one or more pets."""

    def __init__(self, name: str) -> None:
        self.name = name
        self.pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Return every task across all pets."""
        tasks: list[Task] = []
        for pet in self.pets:
            tasks.extend(pet.tasks)
        return tasks

    def __repr__(self) -> str:
        return f"Owner(name={self.name!r}, pets={len(self.pets)})"


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Retrieves, organises, and manages tasks for an owner's pets."""

    def __init__(self, owner: Owner) -> None:
        self.owner = owner

    # -- retrieval ----------------------------------------------------------

    def get_all_tasks(self) -> list[Task]:
        """Return all tasks from the owner's pets."""
        return self.owner.get_all_tasks()

    # -- sorting ------------------------------------------------------------

    def sort_by_time(self, tasks: Optional[list[Task]] = None) -> list[Task]:
        """Return tasks sorted chronologically by their 'HH:MM' time field."""
        if tasks is None:
            tasks = self.get_all_tasks()
        return sorted(tasks, key=lambda t: t.time)

    # -- filtering ----------------------------------------------------------

    def filter_tasks(
        self,
        pet_name: Optional[str] = None,
        status: Optional[bool] = None,
    ) -> list[Task]:
        """Filter tasks by pet name and/or completion status.

        Parameters
        ----------
        pet_name : str, optional
            Only return tasks belonging to this pet.
        status : bool, optional
            True = completed, False = pending, None = all.
        """
        tasks = self.get_all_tasks()
        if pet_name is not None:
            tasks = [t for t in tasks if t.pet_name == pet_name]
        if status is not None:
            tasks = [t for t in tasks if t.is_complete == status]
        return tasks

    # -- conflict detection -------------------------------------------------

    def detect_conflicts(self) -> list[str]:
        """Detect tasks scheduled at the same time for the same pet.

        Returns a list of human-readable warning strings (empty if no conflicts).

        Tradeoff: only flags exact time matches, not overlapping durations.
        This keeps the logic lightweight and avoids false positives from tasks
        that happen to be scheduled close together but don't actually overlap.
        """
        seen: dict[tuple[str, str], str] = {}
        warnings: list[str] = []
        for task in self.get_all_tasks():
            key = (task.time, task.pet_name)
            if key in seen:
                warnings.append(
                    f"WARNING: '{seen[key]}' and '{task.description}' "
                    f"for {task.pet_name} are both at {task.time}"
                )
            else:
                seen[key] = task.description
        return warnings

    # -- recurrence ---------------------------------------------------------

    def mark_task_complete(self, task: Task) -> Optional[Task]:
        """Mark a task complete and register the next occurrence if recurring.

        Returns the new Task if one was created, else None.
        """
        next_task = task.mark_complete()
        if next_task:
            for pet in self.owner.pets:
                if pet.name == task.pet_name:
                    pet.add_task(next_task)
                    break
        return next_task

    # -- schedule generation ------------------------------------------------

    def generate_schedule(self, for_date: Optional[date] = None) -> list[Task]:
        """Return incomplete tasks due on for_date, sorted by time.

        Defaults to today if no date is supplied.
        Priority (high > medium > low) breaks ties within the same time slot.
        """
        if for_date is None:
            for_date = date.today()
        priority_rank = {"high": 0, "medium": 1, "low": 2}
        due = [
            t for t in self.get_all_tasks()
            if t.due_date == for_date and not t.is_complete
        ]
        return sorted(due, key=lambda t: (t.time, priority_rank.get(t.priority, 9)))
