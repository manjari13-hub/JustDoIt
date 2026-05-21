# JustDoIt
A simple python to do list app.
<br>
A desktop app built with Python and Tkinter that helps students organise their study tasks, track deadlines, and manage their workload across different subjects. It stores all data locally using SQLite, so no internet connection is required.

---

## Team

| Teammate | File | Responsibility |
|---|---|---|
| Teammate 1 | `database.py` | Database & backend logic |
| Teammate 2 | `main.py` | UI & Tkinter interface |
| Teammate 3 | `features.py` | Features, filters & stats |

---

## How to Run

1. Make sure Python is installed on your computer (version **3.8 or above**)
   - Check your version: `python --version`
2. **No extra libraries needed** — the app only uses built-in Python modules (`tkinter`, `sqlite3`, `datetime`, `platform`)
3. Place all four files in the **same folder**:
   - `main.py`
   - `database.py`
   - `features.py`
   - `README.md`
4. Open a terminal (or Command Prompt on Windows) inside that folder
5. Run the app with:
   ```
   python main.py
   ```
6. A database file called `studyplanner.db` will be created automatically in the same folder on first run

---

## Features

- **Task Management** — Add, view, edit, and delete study tasks with a subject, deadline, and priority level
- **Priority Levels** — Tag every task as High, Medium, or Low priority, shown with colour-coded dots (red / orange / green)
- **Today View** — Instantly see only the tasks that are due today, with a live count badge
- **Upcoming View** — See all pending tasks across every subject in one place
- **Overdue Warnings** — Tasks past their deadline display an ⚠ warning icon so nothing slips through
- **Task Detail Panel** — Click the `>` arrow on any task to open a right-side panel with an editable description, subtasks checklist, and the ability to save changes
- **Sticky Wall** — A colourful sticky note board (yellow, blue, pink, orange) where you can jot down freeform notes, separate from the task list
- **Search & Filter** — Search tasks in real time by name or subject, and filter by subject and completion status using the top filter bar or sidebar tag pills

---

## UI Design Reference

The interface is inspired by modern task manager apps such as Todoist and TickTick, with a clean 3-panel layout:

- **Left panel** — Sidebar navigation with subject lists, priority tag pills, and search
- **Center panel** — Main task list view (or Sticky Wall when selected), with an inline add-task form and a stats bar at the bottom
- **Right panel** — Collapsible task detail panel that slides in when a task is expanded, showing editable fields, a description area, and a subtasks checklist

The colour palette uses a soft sage background (`#F0F4EF`), white cards, a warm yellow accent (`#E8C547`), and priority colours matched to common traffic-light conventions.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **Python 3** | Programming language |
| **Tkinter** | GUI framework (built into Python) |
| **SQLite** | Local database (built into Python via `sqlite3`) |
