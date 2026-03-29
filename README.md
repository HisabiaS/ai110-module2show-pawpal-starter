# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Features

- **Owner & pet management** — register an owner and one or more pets (dog, cat, rabbit, etc.)
- **Task scheduling** — add care tasks with time, duration, priority (`high` / `medium` / `low`), and recurrence (`once` / `daily` / `weekly`)
- **Smarter Scheduling**
  - *Sorting by time* — the daily schedule is always displayed in chronological order; priority breaks ties within the same time slot
  - *Filtering* — view tasks by pet or completion status (pending / done / all)
  - *Conflict warnings* — the scheduler flags any two tasks for the same pet booked at the same time
  - *Daily recurrence* — completing a recurring task automatically creates the next occurrence (daily → tomorrow, weekly → next week)
- **Interactive UI** — Streamlit app with sidebar pet management, tabbed schedule view, and in-app task removal

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

## Testing PawPal+

```bash
python -m pytest
```

The test suite (`tests/test_pawpal.py`) covers 21 behaviours across 6 areas:
task completion, recurrence logic, pet task management, sorting, filtering, and conflict detection.

Confidence level: ★★★★☆ — all happy paths and core edge cases pass.

## Running the app

```bash
streamlit run app.py
```

## Project files

| File | Purpose |
|------|---------|
| `pawpal_system.py` | Logic layer — `Task`, `Pet`, `Owner`, `Scheduler` classes |
| `app.py` | Streamlit UI |
| `main.py` | CLI demo script |
| `tests/test_pawpal.py` | Automated test suite |
| `reflection.md` | Design decisions and AI collaboration notes |

---

## Suggested workflow (original)

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
