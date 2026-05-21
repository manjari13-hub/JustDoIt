# =============================================================================
# FILE: database.py
# OWNER: Teammate 1
# PURPOSE: This file handles everything related to the SQLite database.
#          It creates the database file, the tables, and provides functions
#          to add, retrieve, update, and delete tasks, sticky notes, and subtasks.
#          All other files import from this file to interact with the database.
# =============================================================================

import sqlite3  # Built-in Python module for working with SQLite databases


# The name of our database file (will be created in the same folder as the scripts)
DATABASE_FILE = "studyplanner.db"


# -----------------------------------------------------------------------------
# FUNCTION: create_database
# PURPOSE: Creates the database file and all required tables if they don't exist.
#          This is called once when the app starts up.
# -----------------------------------------------------------------------------
def create_database():
    # Connect to (or create) the database file
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Create the main tasks table
    # "IF NOT EXISTS" means it won't crash if the table already exists
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            subject     TEXT,
            task_name   TEXT,
            deadline    TEXT,
            priority    TEXT,
            is_done     INTEGER DEFAULT 0,
            description TEXT DEFAULT ''
        )
    """)

    # Create the lists table so user-defined subjects persist between sessions
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS lists (
            id   INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE
        )
    """)

    # Create the sticky_notes table for the Sticky Wall feature
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sticky_notes (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT,
            content TEXT,
            color   TEXT
        )
    """)

    # Create the subtasks table for the Task Detail Panel
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS subtasks (
            id      INTEGER PRIMARY KEY AUTOINCREMENT,
            task_id INTEGER,
            name    TEXT,
            is_done INTEGER DEFAULT 0
        )
    """)

    # Save the changes and close the connection
    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: add_task
# PURPOSE: Inserts a brand-new task into the tasks table.
# PARAMETERS:
#   subject   - the subject/list the task belongs to (e.g. "Maths")
#   task_name - the name of the task (e.g. "Solve Chapter 5")
#   deadline  - the due date as a string in "YYYY-MM-DD" format
#   priority  - how urgent the task is: "High", "Medium", or "Low"
# -----------------------------------------------------------------------------
def add_task(subject, task_name, deadline, priority):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Insert one row into the tasks table
    cursor.execute("""
        INSERT INTO tasks (subject, task_name, deadline, priority, is_done, description)
        VALUES (?, ?, ?, ?, 0, '')
    """, (subject, task_name, deadline, priority))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: get_all_tasks
# PURPOSE: Retrieves every task from the database and returns them as a list.
#          Each task in the list is a tuple:
#          (id, subject, task_name, deadline, priority, is_done, description)
# -----------------------------------------------------------------------------
def get_all_tasks():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Select all rows from the tasks table, newest first
    cursor.execute("SELECT id, subject, task_name, deadline, priority, is_done, description FROM tasks ORDER BY id DESC")

    # fetchall() returns a list of tuples
    tasks = cursor.fetchall()

    connection.close()
    return tasks


# -----------------------------------------------------------------------------
# FUNCTION: mark_task_done
# PURPOSE: Updates a task's is_done column to 1 (meaning "completed").
# PARAMETERS:
#   task_id - the unique ID number of the task to mark as done
# -----------------------------------------------------------------------------
def mark_task_done(task_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Update only the is_done column for the matching task
    cursor.execute("UPDATE tasks SET is_done = 1 WHERE id = ?", (task_id,))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: unmark_task_done
# PURPOSE: Updates a task's is_done column back to 0 (meaning "not done").
#          Useful if a user accidentally checks off a task.
# PARAMETERS:
#   task_id - the unique ID number of the task to unmark
# -----------------------------------------------------------------------------
def unmark_task_done(task_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("UPDATE tasks SET is_done = 0 WHERE id = ?", (task_id,))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: delete_task
# PURPOSE: Permanently removes a task from the database by its ID.
# PARAMETERS:
#   task_id - the unique ID number of the task to delete
# -----------------------------------------------------------------------------
def delete_task(task_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Delete the task row
    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    # Also delete any subtasks that belong to this task
    cursor.execute("DELETE FROM subtasks WHERE task_id = ?", (task_id,))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: update_task
# PURPOSE: Updates the details of an existing task (used by Task Detail Panel).
# PARAMETERS:
#   task_id     - the ID of the task to update
#   subject     - new subject name
#   task_name   - new task name
#   deadline    - new deadline string
#   priority    - new priority value
#   description - new description text
# -----------------------------------------------------------------------------
def update_task(task_id, subject, task_name, deadline, priority, description):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        UPDATE tasks
        SET subject = ?, task_name = ?, deadline = ?, priority = ?, description = ?
        WHERE id = ?
    """, (subject, task_name, deadline, priority, description, task_id))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: get_tasks_by_filter
# PURPOSE: Returns a filtered list of tasks based on subject and completion status.
# PARAMETERS:
#   subject_filter - a subject name string, or "All" to include every subject
#   status_filter  - "All", "Pending" (not done), or "Done" (completed)
# -----------------------------------------------------------------------------
def get_tasks_by_filter(subject_filter, status_filter):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # Start with a base query that selects everything
    query = "SELECT id, subject, task_name, deadline, priority, is_done, description FROM tasks"
    conditions = []
    parameters = []

    # Add subject filter if a specific subject was chosen
    if subject_filter != "All":
        conditions.append("subject = ?")
        parameters.append(subject_filter)

    # Add status filter if "Pending" or "Done" was chosen
    if status_filter == "Pending":
        conditions.append("is_done = 0")
    elif status_filter == "Done":
        conditions.append("is_done = 1")

    # If there are conditions, attach them to the query
    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    query += " ORDER BY id DESC"

    cursor.execute(query, parameters)
    tasks = cursor.fetchall()

    connection.close()
    return tasks



# =============================================================================
# LISTS FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
# FUNCTION: add_list
# PURPOSE: Saves a new user-defined subject/list name to the lists table.
#          Uses INSERT OR IGNORE so duplicate names are silently skipped.
# PARAMETERS:
#   name - the subject name string to save (e.g. "Chemistry")
# -----------------------------------------------------------------------------
def add_list(name):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    # INSERT OR IGNORE means no error if the name already exists
    cursor.execute("INSERT OR IGNORE INTO lists (name) VALUES (?)", (name,))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: get_all_lists
# PURPOSE: Returns every saved list name as a list of strings.
# RETURNS:
#   A list of name strings sorted alphabetically, e.g. ["Chemistry", "Maths"]
# -----------------------------------------------------------------------------
def get_all_lists():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT name FROM lists ORDER BY name ASC")
    rows = cursor.fetchall()

    connection.close()

    # rows is a list of 1-tuples like [("Chemistry",), ("Maths",)]
    # We extract just the name string from each tuple
    names = []
    for row in rows:
        names.append(row[0])
    return names


# -----------------------------------------------------------------------------
# FUNCTION: add_sticky_note
# PURPOSE: Saves a new sticky note to the sticky_notes table.
# PARAMETERS:
#   title   - short heading for the note
#   content - the main body text of the note
#   color   - a hex color string for the note background (e.g. "#FFF3A3")
# -----------------------------------------------------------------------------
def add_sticky_note(title, content, color):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO sticky_notes (title, content, color)
        VALUES (?, ?, ?)
    """, (title, content, color))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: get_all_sticky_notes
# PURPOSE: Returns all sticky notes from the database as a list of tuples.
#          Each tuple: (id, title, content, color)
# -----------------------------------------------------------------------------
def get_all_sticky_notes():
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT id, title, content, color FROM sticky_notes ORDER BY id DESC")
    notes = cursor.fetchall()

    connection.close()
    return notes


# -----------------------------------------------------------------------------
# FUNCTION: delete_sticky_note
# PURPOSE: Removes a sticky note from the database by its ID.
# PARAMETERS:
#   note_id - the unique ID of the sticky note to delete
# -----------------------------------------------------------------------------
def delete_sticky_note(note_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("DELETE FROM sticky_notes WHERE id = ?", (note_id,))

    connection.commit()
    connection.close()


# =============================================================================
# SUBTASKS FUNCTIONS
# =============================================================================

# -----------------------------------------------------------------------------
# FUNCTION: add_subtask
# PURPOSE: Adds a subtask linked to a specific parent task.
# PARAMETERS:
#   task_id - the ID of the parent task this subtask belongs to
#   name    - the name/description of the subtask
# -----------------------------------------------------------------------------
def add_subtask(task_id, name):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO subtasks (task_id, name, is_done)
        VALUES (?, ?, 0)
    """, (task_id, name))

    connection.commit()
    connection.close()


# -----------------------------------------------------------------------------
# FUNCTION: get_subtasks
# PURPOSE: Returns all subtasks that belong to a given parent task.
#          Each subtask is a tuple: (id, task_id, name, is_done)
# PARAMETERS:
#   task_id - the ID of the parent task
# -----------------------------------------------------------------------------
def get_subtasks(task_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("SELECT id, task_id, name, is_done FROM subtasks WHERE task_id = ?", (task_id,))
    subtasks = cursor.fetchall()

    connection.close()
    return subtasks


# -----------------------------------------------------------------------------
# FUNCTION: mark_subtask_done
# PURPOSE: Marks a specific subtask as completed (is_done = 1).
# PARAMETERS:
#   subtask_id - the unique ID of the subtask to mark as done
# -----------------------------------------------------------------------------
def mark_subtask_done(subtask_id):
    connection = sqlite3.connect(DATABASE_FILE)
    cursor = connection.cursor()

    cursor.execute("UPDATE subtasks SET is_done = 1 WHERE id = ?", (subtask_id,))

    connection.commit()
    connection.close()
