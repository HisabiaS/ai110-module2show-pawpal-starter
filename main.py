"""
main.py — CLI demo script for PawPal+.

Run with:  python main.py
"""

from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

# ── Build sample data ──────────────────────────────────────────────────────

owner = Owner("Jordan")

mochi = Pet("Mochi", "dog", age=3)
luna  = Pet("Luna",  "cat", age=5)

owner.add_pet(mochi)
owner.add_pet(luna)

today = date.today()

# Mochi's tasks (intentionally out of chronological order to test sorting)
mochi.add_task(Task("Afternoon walk",  "14:00", 30, "medium", "daily",  due_date=today))
mochi.add_task(Task("Morning walk",    "07:30", 20, "high",   "daily",  due_date=today))
mochi.add_task(Task("Evening feeding", "18:00", 10, "high",   "daily",  due_date=today))
mochi.add_task(Task("Flea treatment",  "09:00", 5,  "low",    "weekly", due_date=today))

# Luna's tasks
luna.add_task(Task("Morning feeding", "07:00", 5,  "high",  "daily", due_date=today))
luna.add_task(Task("Litter box",      "09:00", 5,  "medium","daily", due_date=today))
luna.add_task(Task("Playtime",        "18:30", 15, "low",   "daily", due_date=today))

# ── Demonstrate scheduling ─────────────────────────────────────────────────

sched = Scheduler(owner)

print("=" * 55)
print(f"  PawPal+ — Today's Schedule for {owner.name}")
print(f"  Date: {today}")
print("=" * 55)

schedule = sched.generate_schedule()
if schedule:
    for t in schedule:
        status = "X" if t.is_complete else "o"
        print(
            f"  [{status}] {t.time}  {t.pet_name:<8}  "
            f"{t.description:<22}  {t.duration_minutes:>3} min  "
            f"[{t.priority}]"
        )
else:
    print("  No tasks due today.")

# ── Conflict detection ─────────────────────────────────────────────────────

print("\n-- Conflict check --")
# Add a duplicate time intentionally to trigger detection
mochi.add_task(Task("Vet appointment", "07:30", 60, "high", due_date=today))
conflicts = sched.detect_conflicts()
if conflicts:
    for w in conflicts:
        print(" ", w)
else:
    print("  No conflicts detected.")

# Remove the intentional duplicate before continuing
mochi.remove_task("Vet appointment")

# ── Filtering ─────────────────────────────────────────────────────────────

print("\n-- Mochi's pending tasks (filtered) --")
for t in sched.sort_by_time(sched.filter_tasks(pet_name="Mochi", status=False)):
    print(f"  {t.time}  {t.description}")

# ── Recurring task demo ────────────────────────────────────────────────────

print("\n-- Completing 'Morning walk' (daily) -> generates next occurrence --")
morning_walk = next(t for t in mochi.tasks if t.description == "Morning walk")
next_task = sched.mark_task_complete(morning_walk)
if next_task:
    print(f"  Next '{next_task.description}' scheduled for {next_task.due_date}")

print("\n-- Updated Mochi task count:", len(mochi.tasks))
print("=" * 55)
