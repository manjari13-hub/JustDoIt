# =============================================================================
# FILE: features.py
# OWNER: Teammate 3
# PURPOSE: This file contains helper functions that sit between the UI (main.py)
#          and the database (database.py). These functions handle things like
#          filtering tasks, calculating stats, checking for overdue tasks,
#          and formatting task data for display.
#          No database calls happen here — this file only works with data
#          that has already been loaded from the database.
# =============================================================================

import datetime  # Built-in Python module for working with dates


# -----------------------------------------------------------------------------
# FUNCTION: get_stats
# PURPOSE: Counts how many tasks are done, how many are pending, and the total.
# PARAMETERS:
#   tasks - a list of task tuples from the database
#           Format: (id, subject, task_name, deadline, priority, is_done, description)
# RETURNS:
#   A dictionary like: {"done": 3, "pending": 5, "total": 8}
# -----------------------------------------------------------------------------
def get_stats(tasks):
    total = len(tasks)   # Total number of tasks
    done = 0             # We'll count up how many are done

    # Go through each task and check the is_done field (index 5 in the tuple)
    for task in tasks:
        if task[5] == 1:   # is_done = 1 means completed
            done += 1

    # Calculate pending by subtracting done from total
    pending = total - done

    # Return the counts as a dictionary
    return {"done": done, "pending": pending, "total": total}


# -----------------------------------------------------------------------------
# FUNCTION: get_unique_subjects
# PURPOSE: Extracts all unique subject names from a list of tasks.
# PARAMETERS:
#   tasks - a list of task tuples from the database
# RETURNS:
#   A sorted list of subject name strings, with "All" as the very first item.
#   Example: ["All", "Maths", "Physics", "Science"]
# -----------------------------------------------------------------------------
def get_unique_subjects(tasks):
    subjects = []

    # Loop through all tasks and collect subjects we haven't seen before
    for task in tasks:
        subject = task[1]   # subject is at index 1 in the tuple
        if subject not in subjects and subject:
            subjects.append(subject)

    # Sort the list alphabetically so it looks neat in dropdowns
    subjects.sort()

    # Always put "All" at the front so users can see everything
    subjects.insert(0, "All")

    return subjects


# -----------------------------------------------------------------------------
# FUNCTION: is_overdue
# PURPOSE: Checks whether a task's deadline has already passed.
# PARAMETERS:
#   deadline_str - a date string in "YYYY-MM-DD" format (e.g. "2024-12-31")
# RETURNS:
#   True  - if the deadline was before today
#   False - if the deadline is today, in the future, or the string is invalid/empty
# -----------------------------------------------------------------------------
def is_overdue(deadline_str):
    # If the deadline is empty or None, we can't check — return False
    if not deadline_str or deadline_str.strip() == "":
        return False

    # Try to convert the string to a real date object
    try:
        deadline_date = datetime.datetime.strptime(deadline_str.strip(), "%d-%m-%y").date()
        today = datetime.date.today()

        # Return True only if the deadline was strictly before today
        return deadline_date < today

    except ValueError:
        # If the date string doesn't match the expected format, just return False
        return False


# -----------------------------------------------------------------------------
# FUNCTION: get_tasks_due_today
# PURPOSE: Filters a task list to only return tasks that are due today.
# PARAMETERS:
#   tasks - a list of task tuples from the database
# RETURNS:
#   A list of task tuples whose deadline matches today's date.
#   Returns an empty list if no tasks are due today.
# -----------------------------------------------------------------------------
def get_tasks_due_today(tasks):
    today_str = datetime.date.today().strftime("%d-%m-%y")
    tasks_today = []

    # Check each task's deadline (index 3 in the tuple)
    for task in tasks:
        deadline = task[3]
        if deadline == today_str:
            tasks_today.append(task)

    return tasks_today


# -----------------------------------------------------------------------------
# FUNCTION: format_task_display
# PURPOSE: Creates a readable text summary of a single task for display.
# PARAMETERS:
#   task - a single task tuple:
#          (id, subject, task_name, deadline, priority, is_done, description)
# RETURNS:
#   A formatted string like:
#   "[DONE] Maths — Solve Chapter 5 | Due: 2024-12-01 | Priority: High"
#   "[    ] Physics — Lab Report    | Due: 2024-11-20 | Priority: Low  ⚠ OVERDUE"
# -----------------------------------------------------------------------------
def format_task_display(task):
    # Unpack the task tuple into readable variable names
    task_id      = task[0]
    subject      = task[1]
    task_name    = task[2]
    deadline     = task[3]
    priority     = task[4]
    is_done      = task[5]

    # Show "[DONE]" if completed, or "[    ]" if still pending
    if is_done == 1:
        status_label = "[DONE]"
    else:
        status_label = "[    ]"

    # Build the main part of the display string
    display = "{} {} — {} | Due: {} | Priority: {}".format(
        status_label, subject, task_name, deadline, priority
    )

    # If the task is not done and is overdue, add a warning at the end
    if is_done == 0 and is_overdue(deadline):
        display += "  ⚠ OVERDUE"

    return display


# -----------------------------------------------------------------------------
# FUNCTION: search_tasks
# PURPOSE: Filters a list of tasks by a search query string.
#          The search checks both the task name and subject name.
# PARAMETERS:
#   tasks - a list of task tuples from the database
#   query - the search string the user typed (e.g. "math" or "report")
# RETURNS:
#   A filtered list of tasks where either task_name or subject contains the query.
#   If query is empty, returns the full unfiltered list.
# -----------------------------------------------------------------------------
def search_tasks(tasks, query):
    # If the search box is empty, just return all tasks
    if not query or query.strip() == "":
        return tasks

    # Convert the query to lowercase for case-insensitive matching
    query_lower = query.lower()
    matching_tasks = []

    # Check each task — look in task_name (index 2) and subject (index 1)
    for task in tasks:
        task_name_lower = task[2].lower()
        subject_lower   = task[1].lower()

        if query_lower in task_name_lower or query_lower in subject_lower:
            matching_tasks.append(task)

    return matching_tasks


# -----------------------------------------------------------------------------
# FUNCTION: get_priority_color
# PURPOSE: Returns the hex color code that matches a given priority level.
#          These colors are used to draw the colored priority dots in the UI.
# PARAMETERS:
#   priority - a string: "High", "Medium", or "Low"
# RETURNS:
#   A hex color string like "#E05C5C"
# -----------------------------------------------------------------------------
def get_priority_color(priority):
    if priority == "High":
        return "#E05C5C"    # Soft red for high priority

    elif priority == "Medium":
        return "#E8A84A"    # Warm orange for medium priority

    elif priority == "Low":
        return "#5BBF7A"    # Calm green for low priority

    else:
        # Return grey for any unrecognised or missing priority value
        return "#888888"
