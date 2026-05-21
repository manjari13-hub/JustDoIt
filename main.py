# =============================================================================
# FILE: main.py
# OWNER: Teammate 2
# PURPOSE: This is the main entry point for the Student Study Planner app.
#          It builds the entire Tkinter GUI — the 3-panel layout (sidebar,
#          task list, detail panel), handles all button clicks, and connects
#          the UI to the database functions in database.py and the helper
#          functions in features.py.
#          Run this file to start the app: python main.py
# =============================================================================

import tkinter as tk
from tkinter import ttk, messagebox
import platform          # Used to detect the operating system for font selection
import database          # Our database file (Teammate 1's work)
import features          # Our features/helper file (Teammate 3's work)
import random            # Used to assign random colors to subject dots
import datetime

# =============================================================================
# FONT SETUP — detect OS and pick the best font
# =============================================================================
os_name = platform.system()

if os_name == "Windows":
    APP_FONT = "Segoe UI"
elif os_name == "Darwin":       # Darwin = macOS
    APP_FONT = "Helvetica Neue"
else:                           # Linux and everything else
    APP_FONT = "DejaVu Sans"

# =============================================================================
# COLOR PALETTE — all colors used throughout the app
# =============================================================================
COLOR_BG          = "#F0F4EF"   # Main window background (soft sage)
COLOR_PANEL       = "#FFFFFF"   # Panel/card background (white)
COLOR_ACCENT      = "#E8C547"   # Accent color for buttons (warm yellow)
COLOR_SIDEBAR_ACT = "#EAF0E9"   # Active sidebar item background
COLOR_TEXT_PRI    = "#1A1A1A"   # Primary text (near-black)
COLOR_TEXT_SEC    = "#888888"   # Secondary text (medium grey)
COLOR_BORDER      = "#E5E5E5"   # Border/divider color
COLOR_HIGH        = "#E05C5C"   # High priority dot (soft red)
COLOR_MED         = "#E8A84A"   # Medium priority dot (warm orange)
COLOR_LOW         = "#5BBF7A"   # Low priority dot (calm green)

# Sticky note background colors — cycle through these for new notes
STICKY_COLORS = ["#FFF3A3", "#C8E6FA", "#FFD6D6", "#FFE0B2"]

# Keeps track of which color to use next for sticky notes
sticky_color_index = 0

# Dictionary to store randomly assigned dot colors per subject
subject_dot_colors = {}


# =============================================================================
# MAIN APPLICATION CLASS
# =============================================================================
class StudyPlannerApp:

    def __init__(self, root):
        # Store the root window
        self.root = root
        self.root.title("Just Do It")
        self.root.geometry("1100x680")
        self.root.resizable(False, False)
        self.root.configure(bg=COLOR_BG)
        icon = tk.PhotoImage(file='logo.png')
        self.root.iconphoto(True,icon)

        # These variables keep track of the current state of the app
        self.current_view    = "tasks"       # Which nav item is active
        self.selected_task   = None          # The task shown in the detail panel
        self.add_form_open   = False         # Whether the inline add-task form is open
        self.filter_subject  = "All"         # Current subject filter
        self.filter_status   = "All"         # Current status filter
        self.filter_priority = None          # Active priority tag filter (or None)
        self.search_query    = ""            # Current search text

        # Make sure the database and tables exist before we try to use them
        database.create_database()

        # Build the three main panels
        self.build_sidebar()
        self.build_center_panel()
        self.build_right_panel()

        # Load tasks and populate the UI for the first time
        self.refresh_tasks()

    # =========================================================================
    # SIDEBAR — LEFT PANEL
    # =========================================================================
    def build_sidebar(self):
        # Outer sidebar frame
        self.sidebar = tk.Frame(self.root, bg=COLOR_PANEL, width=220)
        self.sidebar.pack(side="left", fill="y")
        self.sidebar.pack_propagate(False)   # Keep the sidebar at a fixed width

        # --- Top: Menu title and hamburger icon ---
        top_bar = tk.Frame(self.sidebar, bg=COLOR_PANEL, pady=16, padx=16)
        top_bar.pack(fill="x")

        tk.Label(top_bar, text="Menu", font=(APP_FONT, 14, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_PRI).pack(side="left")
        tk.Label(top_bar, text="≡", font=(APP_FONT, 18),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).pack(side="right")

        # Thin divider line below the top bar
        tk.Frame(self.sidebar, bg=COLOR_BORDER, height=1).pack(fill="x")

        # --- Search bar ---
        search_frame = tk.Frame(self.sidebar, bg=COLOR_PANEL, padx=12, pady=10)
        search_frame.pack(fill="x")

        search_inner = tk.Frame(search_frame, bg=COLOR_BG, bd=0)
        search_inner.pack(fill="x")

        tk.Label(search_inner, text="🔍", bg=COLOR_BG, font=(APP_FONT, 10)).pack(side="left", padx=(6, 2))

        self.search_var = tk.StringVar()
        self.search_var.trace("w", self.on_search_changed)   # Call on every keystroke

        search_entry = tk.Entry(search_inner, textvariable=self.search_var,
                                font=(APP_FONT, 10), bg=COLOR_BG, fg=COLOR_TEXT_PRI,
                                relief="flat", bd=0, insertbackground=COLOR_TEXT_PRI)
        search_entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 6))
        search_entry.insert(0, "Search...")
        search_entry.bind("<FocusIn>",  self.on_search_focus_in)
        search_entry.bind("<FocusOut>", self.on_search_focus_out)
        self.search_entry_widget = search_entry

        # --- Section label: TASKS ---
        tk.Label(self.sidebar, text="TASKS", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, anchor="w",
                 padx=16, pady=4).pack(fill="x")

        # --- Navigation buttons ---
        # Each button has a text label and an optional count badge
        self.nav_buttons = {}   # We'll store references so we can style the active one

        self.btn_tasks  = self.make_nav_button("tasks",  "☰  Tasks",        self.show_tasks)
        self.btn_sticky = self.make_nav_button("sticky", "📋  Sticky Wall",  self.show_sticky_wall)

        # --- Section label: LISTS ---
        tk.Label(self.sidebar, text="LISTS", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, anchor="w",
                 padx=16, pady=4).pack(fill="x")

        # Scrollable area for subject list
        self.lists_frame = tk.Frame(self.sidebar, bg=COLOR_PANEL)
        self.lists_frame.pack(fill="x")

        # Add New List button
        add_list_btn = tk.Button(self.sidebar, text="+ Add New List",
                                 font=(APP_FONT, 9), bg=COLOR_PANEL, fg=COLOR_ACCENT,
                                 relief="flat", cursor="hand2", anchor="w",
                                 padx=16, pady=4,
                                 command=self.open_add_list_popup)
        add_list_btn.pack(fill="x")

        # --- Section label: TAGS ---
        tk.Label(self.sidebar, text="TAGS", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, anchor="w",
                 padx=16, pady=4).pack(fill="x")

        # Priority tag pills
        tags_frame = tk.Frame(self.sidebar, bg=COLOR_PANEL, padx=12, pady=4)
        tags_frame.pack(fill="x")

        self.make_tag_pill(tags_frame, "High",   COLOR_HIGH)
        self.make_tag_pill(tags_frame, "Medium", COLOR_MED)
        self.make_tag_pill(tags_frame, "Low",    COLOR_LOW)

        # Divider before bottom buttons
        tk.Frame(self.sidebar, bg=COLOR_BORDER, height=1).pack(fill="x", pady=8)

        # --- Bottom: Settings and Sign Out ---
        tk.Button(self.sidebar, text="⚙  Settings",
                  font=(APP_FONT, 9), bg=COLOR_PANEL, fg=COLOR_TEXT_SEC,
                  relief="flat", cursor="hand2", anchor="w", padx=16, pady=4,
                  command=self.show_settings).pack(fill="x")

        tk.Button(self.sidebar, text="↪  Sign Out",
                  font=(APP_FONT, 9), bg=COLOR_PANEL, fg=COLOR_TEXT_SEC,
                  relief="flat", cursor="hand2", anchor="w", padx=16, pady=4,
                  command=self.show_signout).pack(fill="x")

    # -------------------------------------------------------------------------
    # HELPER: make_nav_button
    # Creates a styled navigation button in the sidebar
    # -------------------------------------------------------------------------
    def make_nav_button(self, name, text, command):
        btn = tk.Button(self.sidebar, text=text,
                        font=(APP_FONT, 10), bg=COLOR_PANEL, fg=COLOR_TEXT_PRI,
                        relief="flat", cursor="hand2", anchor="w",
                        padx=16, pady=8, bd=0,
                        command=command)
        btn.pack(fill="x")
        self.nav_buttons[name] = btn
        return btn

    # -------------------------------------------------------------------------
    # HELPER: make_tag_pill
    # Creates a small colored priority tag pill button
    # -------------------------------------------------------------------------
    def make_tag_pill(self, parent, priority_text, color):
        btn = tk.Button(parent, text=priority_text,
                        font=(APP_FONT, 8), bg=color, fg=COLOR_PANEL,
                        relief="flat", cursor="hand2",
                        padx=10, pady=2,
                        command=lambda p=priority_text: self.filter_by_priority(p))
        btn.pack(side="left", padx=3)

    # -------------------------------------------------------------------------
    # HELPER: set_active_nav
    # Highlights the currently active sidebar nav button
    # -------------------------------------------------------------------------
    def set_active_nav(self, active_name):
        for name, btn in self.nav_buttons.items():
            if name == active_name:
                btn.configure(bg=COLOR_SIDEBAR_ACT, font=(APP_FONT, 10, "bold"))
            else:
                btn.configure(bg=COLOR_PANEL, font=(APP_FONT, 10))

    # =========================================================================
    # CENTER PANEL — Task List View
    # =========================================================================
    def build_center_panel(self):
        # Main center container
        self.center = tk.Frame(self.root, bg=COLOR_BG)
        self.center.pack(side="left", fill="both", expand=True, padx=12, pady=12)

        # --- Top heading row ---
        heading_frame = tk.Frame(self.center, bg=COLOR_BG)
        heading_frame.pack(fill="x", pady=(0, 8))

        self.heading_label = tk.Label(heading_frame, text="Tasks",
                                      font=(APP_FONT, 16, "bold"),
                                      bg=COLOR_BG, fg=COLOR_TEXT_PRI)
        self.heading_label.pack(side="left")

        # Count badge circle (Canvas drawing trick)
        self.badge_canvas = tk.Canvas(heading_frame, width=26, height=26,
                                      bg=COLOR_BG, highlightthickness=0)
        self.badge_canvas.pack(side="left", padx=8)

        self.badge_canvas.create_oval(2, 2, 24, 24, fill=COLOR_ACCENT, outline="")
        self.badge_text_id = self.badge_canvas.create_text(13, 13, text="0",
                                                            font=(APP_FONT, 9, "bold"),
                                                            fill=COLOR_TEXT_PRI)

        # --- Filter bar ---
        filter_frame = tk.Frame(self.center, bg=COLOR_BG, pady=4)
        filter_frame.pack(fill="x")

        tk.Label(filter_frame, text="Subject:", font=(APP_FONT, 9),
                 bg=COLOR_BG, fg=COLOR_TEXT_SEC).pack(side="left")

        self.subject_combo = ttk.Combobox(filter_frame, state="readonly", width=14,
                                          font=(APP_FONT, 9))
        self.subject_combo.set("All")
        self.subject_combo.pack(side="left", padx=(4, 10))

        tk.Label(filter_frame, text="Status:", font=(APP_FONT, 9),
                 bg=COLOR_BG, fg=COLOR_TEXT_SEC).pack(side="left")

        self.status_combo = ttk.Combobox(filter_frame, values=["All", "Pending", "Done"],
                                         state="readonly", width=10, font=(APP_FONT, 9))
        self.status_combo.set("All")
        self.status_combo.pack(side="left", padx=(4, 10))

        apply_btn = tk.Button(filter_frame, text="Apply Filter",
                              font=(APP_FONT, 9, "bold"), bg=COLOR_ACCENT,
                              fg=COLOR_TEXT_PRI, relief="flat", cursor="hand2",
                              padx=12, pady=4,
                              command=self.apply_filter)
        apply_btn.pack(side="left")

        # --- Add New Task bar ---
        add_bar = tk.Frame(self.center, bg=COLOR_PANEL, pady=8, padx=12)
        add_bar.pack(fill="x", pady=4)

        tk.Button(add_bar, text="+ Add New Task",
                  font=(APP_FONT, 10), bg=COLOR_PANEL, fg=COLOR_ACCENT,
                  relief="flat", cursor="hand2",
                  command=self.toggle_add_form).pack(anchor="w")

        # --- Inline add task form (hidden by default) ---
        self.add_form_frame = tk.Frame(self.center, bg=COLOR_PANEL, padx=12, pady=8)
        # This frame is NOT packed yet — it will appear when the button is clicked

        # Subject entry (now row 0 — appears first)
        tk.Label(self.add_form_frame, text="Subject:", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).grid(row=0, column=0, sticky="w", pady=2)
        self.new_subject = tk.Entry(self.add_form_frame, font=(APP_FONT, 10),
                                    bg=COLOR_BG, relief="flat", bd=1)
        self.new_subject.grid(row=0, column=1, sticky="ew", padx=8, pady=2)

        # Task name entry (now row 1 — appears second)
        tk.Label(self.add_form_frame, text="Task Name:", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).grid(row=1, column=0, sticky="w", pady=2)
        self.new_task_name = tk.Entry(self.add_form_frame, font=(APP_FONT, 10),
                                      bg=COLOR_BG, relief="flat", bd=1)
        self.new_task_name.grid(row=1, column=1, sticky="ew", padx=8, pady=2)

        # Deadline entry
        tk.Label(self.add_form_frame, text="Deadline:", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).grid(row=2, column=0, sticky="w", pady=2)
        self.new_deadline = tk.Entry(self.add_form_frame, font=(APP_FONT, 10),
                                     bg=COLOR_BG, relief="flat", bd=1)
        self.new_deadline.insert(0, "DD-MM-YY")
        self.new_deadline.grid(row=2, column=1, sticky="ew", padx=8, pady=2)

        # Priority dropdown
        tk.Label(self.add_form_frame, text="Priority:", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).grid(row=3, column=0, sticky="w", pady=2)
        self.new_priority = ttk.Combobox(self.add_form_frame,
                                         values=["High", "Medium", "Low"],
                                         state="readonly", width=10, font=(APP_FONT, 9))
        self.new_priority.set("Medium")
        self.new_priority.grid(row=3, column=1, sticky="w", padx=8, pady=2)

        # Column weight so the entry fields expand
        self.add_form_frame.columnconfigure(1, weight=1)

        # Confirm and cancel buttons row
        btn_row = tk.Frame(self.add_form_frame, bg=COLOR_PANEL)
        btn_row.grid(row=4, column=0, columnspan=2, sticky="w", pady=6)

        tk.Button(btn_row, text="Add Task",
                  font=(APP_FONT, 9, "bold"), bg=COLOR_ACCENT,
                  fg=COLOR_TEXT_PRI, relief="flat", cursor="hand2",
                  padx=14, pady=4,
                  command=self.submit_new_task).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="Cancel",
                  font=(APP_FONT, 9), bg=COLOR_BORDER,
                  fg=COLOR_TEXT_SEC, relief="flat", cursor="hand2",
                  padx=14, pady=4,
                  command=self.toggle_add_form).pack(side="left")

        # --- Task list scroll area ---
        # Stored as self.list_container so toggle_add_form can pack before it
        self.list_container = tk.Frame(self.center, bg=COLOR_BG)
        self.list_container.pack(fill="both", expand=True, pady=4)
        list_container = self.list_container

        # Canvas + scrollbar combo for scrollable task list
        self.task_canvas = tk.Canvas(list_container, bg=COLOR_BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(list_container, orient="vertical",
                                  command=self.task_canvas.yview)
        self.task_canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.task_canvas.pack(side="left", fill="both", expand=True)

        # The actual frame that holds task cards, placed inside the canvas
        self.task_list_frame = tk.Frame(self.task_canvas, bg=COLOR_BG)
        self.task_canvas_window = self.task_canvas.create_window(
            (0, 0), window=self.task_list_frame, anchor="nw"
        )

        # Update scroll region whenever the inner frame changes size
        self.task_list_frame.bind("<Configure>", self.on_task_frame_configure)
        self.task_canvas.bind("<Configure>", self.on_canvas_configure)

        # Bind mouse wheel scrolling
        self.task_canvas.bind("<MouseWheel>", self.on_mousewheel)

        # --- Stats bar at the bottom ---
        self.stats_bar = tk.Label(self.center, text="0 done · 0 pending · 0 total",
                                   font=(APP_FONT, 9), bg=COLOR_BORDER,
                                   fg=COLOR_TEXT_SEC, pady=4)
        self.stats_bar.pack(fill="x")

        # --- Sticky Wall view frame (hidden by default) ---
        self.sticky_wall_frame = tk.Frame(self.center, bg=COLOR_BG)
        # Not packed here — shown when user clicks Sticky Wall in sidebar

    # -------------------------------------------------------------------------
    # TASK CARD: draw a single task row in the task list
    # -------------------------------------------------------------------------
    def draw_task_card(self, parent, task):
        # Unpack task tuple
        task_id      = task[0]
        subject      = task[1]
        task_name    = task[2]
        deadline     = task[3]
        priority     = task[4]
        is_done      = task[5]

        # Card frame with white background and bottom border
        card = tk.Frame(parent, bg=COLOR_PANEL, pady=8, padx=10)
        card.pack(fill="x", pady=2)

        tk.Frame(card, bg=COLOR_BORDER, height=1).pack(fill="x", side="bottom")

        # Inner row of widgets
        row = tk.Frame(card, bg=COLOR_PANEL)
        row.pack(fill="x")

        # Checkbox — checked if the task is done
        done_var = tk.IntVar(value=is_done)
        checkbox = tk.Checkbutton(row, variable=done_var, bg=COLOR_PANEL,
                                  activebackground=COLOR_PANEL,
                                  command=lambda tid=task_id, var=done_var: self.toggle_done(tid, var))
        checkbox.pack(side="left")

        # Priority dot (colored circle using Canvas)
        dot_color = features.get_priority_color(priority)
        dot_canvas = tk.Canvas(row, width=12, height=12, bg=COLOR_PANEL,
                               highlightthickness=0)
        dot_canvas.create_oval(1, 1, 11, 11, fill=dot_color, outline="")
        dot_canvas.pack(side="left", padx=(4, 8))

        # Task name and subject in the middle (expand to fill space)
        text_frame = tk.Frame(row, bg=COLOR_PANEL)
        text_frame.pack(side="left", fill="x", expand=True)

        # Strikethrough effect for done tasks: use overstrike font option
        if is_done == 1:
            name_font  = (APP_FONT, 10, "overstrike")
            name_color = COLOR_TEXT_SEC
        else:
            name_font  = (APP_FONT, 10, "bold")
            name_color = COLOR_TEXT_PRI

        tk.Label(text_frame, text=task_name, font=name_font,
                 bg=COLOR_PANEL, fg=name_color, anchor="w").pack(fill="x")
        tk.Label(text_frame, text=subject, font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, anchor="w").pack(fill="x")

        # Right side: deadline, optional overdue icon, expand arrow
        right_frame = tk.Frame(row, bg=COLOR_PANEL)
        right_frame.pack(side="right")

        # Show overdue warning if task is not done and deadline passed
        if is_done == 0 and features.is_overdue(deadline):
            tk.Label(right_frame, text="⚠", font=(APP_FONT, 10),
                     bg=COLOR_PANEL, fg=COLOR_MED).pack(side="left", padx=2)

        # Deadline date with calendar icon
        deadline_display = "📅 " + deadline if deadline else ""
        tk.Label(right_frame, text=deadline_display, font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).pack(side="left", padx=8)

        # Expand arrow to open the detail panel
        expand_btn = tk.Button(right_frame, text=">",
                               font=(APP_FONT, 10), bg=COLOR_PANEL,
                               fg=COLOR_TEXT_SEC, relief="flat", cursor="hand2",
                               command=lambda t=task: self.open_detail_panel(t))
        expand_btn.pack(side="left")

    # =========================================================================
    # RIGHT PANEL — Task Detail Panel
    # =========================================================================
    def build_right_panel(self):
        # The right panel is hidden until a task is expanded
        self.right_panel = tk.Frame(self.root, bg=COLOR_PANEL, width=320)
        # We pack it only when needed

        # Header row: "Task:" label on the left, ✕ close button on the right
        header_row = tk.Frame(self.right_panel, bg=COLOR_PANEL)
        header_row.pack(fill="x", padx=16, pady=(10, 6))

        tk.Label(header_row, text="Task:", font=(APP_FONT, 12, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).pack(side="left")

        # Close/retract button — hides the right panel when clicked
        tk.Button(header_row, text="✕",
                  font=(APP_FONT, 11), bg=COLOR_PANEL, fg=COLOR_TEXT_SEC,
                  relief="flat", cursor="hand2", bd=0,
                  activebackground=COLOR_BG,
                  command=self.close_right_panel).pack(side="right")

        tk.Frame(self.right_panel, bg=COLOR_BORDER, height=1).pack(fill="x")

        content = tk.Frame(self.right_panel, bg=COLOR_PANEL, padx=16, pady=8)
        content.pack(fill="both", expand=True)

        # Task name entry (editable)
        tk.Label(content, text="Task Name", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).pack(anchor="w", pady=(4, 0))
        self.detail_task_name = tk.Entry(content, font=(APP_FONT, 11, "bold"),
                                         bg=COLOR_BG, relief="flat", bd=1,
                                         fg=COLOR_TEXT_PRI)
        self.detail_task_name.pack(fill="x", pady=4)

        # Description text area
        tk.Label(content, text="Description", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC).pack(anchor="w", pady=(4, 0))
        self.detail_description = tk.Text(content, font=(APP_FONT, 10),
                                          bg=COLOR_BG, relief="flat", bd=1,
                                          height=4, fg=COLOR_TEXT_PRI,
                                          wrap="word")
        self.detail_description.pack(fill="x", pady=4)

        # Metadata fields (List/Subject, Due Date, Priority)
        meta_frame = tk.Frame(content, bg=COLOR_PANEL)
        meta_frame.pack(fill="x", pady=4)

        tk.Label(meta_frame, text="List", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, width=8,
                 anchor="w").grid(row=0, column=0, pady=3)
        self.detail_subject_var = tk.StringVar()
        self.detail_subject_combo = ttk.Combobox(meta_frame,
                                                  textvariable=self.detail_subject_var,
                                                  font=(APP_FONT, 9), width=18)
        self.detail_subject_combo.grid(row=0, column=1, pady=3, sticky="w")

        tk.Label(meta_frame, text="Due Date", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, width=8,
                 anchor="w").grid(row=1, column=0, pady=3)
        self.detail_deadline = tk.Entry(meta_frame, font=(APP_FONT, 9),
                                        bg=COLOR_BG, relief="flat", bd=1, width=20)
        self.detail_deadline.grid(row=1, column=1, pady=3, sticky="w")

        tk.Label(meta_frame, text="Priority", font=(APP_FONT, 9),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, width=8,
                 anchor="w").grid(row=2, column=0, pady=3)
        self.detail_priority = ttk.Combobox(meta_frame,
                                            values=["High", "Medium", "Low"],
                                            state="readonly", font=(APP_FONT, 9), width=18)
        self.detail_priority.grid(row=2, column=1, pady=3, sticky="w")

        tk.Frame(content, bg=COLOR_BORDER, height=1).pack(fill="x", pady=6)

        # Subtasks section
        tk.Label(content, text="Subtasks:", font=(APP_FONT, 9, "bold"),
                 bg=COLOR_PANEL, fg=COLOR_TEXT_PRI).pack(anchor="w")

        self.subtasks_frame = tk.Frame(content, bg=COLOR_PANEL)
        self.subtasks_frame.pack(fill="x", pady=4)

        tk.Button(content, text="+ Add New Subtask",
                  font=(APP_FONT, 9), bg=COLOR_PANEL, fg=COLOR_ACCENT,
                  relief="flat", cursor="hand2",
                  command=self.add_subtask_from_panel).pack(anchor="w", pady=2)

        tk.Frame(content, bg=COLOR_BORDER, height=1).pack(fill="x", pady=6)

        # Bottom action buttons
        btn_row = tk.Frame(content, bg=COLOR_PANEL)
        btn_row.pack(fill="x", pady=4)

        tk.Button(btn_row, text="Delete Task",
                  font=(APP_FONT, 9), bg=COLOR_PANEL, fg=COLOR_TEXT_PRI,
                  relief="flat", cursor="hand2", bd=1,
                  padx=12, pady=4,
                  command=self.delete_selected_task).pack(side="left", padx=(0, 8))

        tk.Button(btn_row, text="Save Changes",
                  font=(APP_FONT, 9, "bold"), bg=COLOR_ACCENT,
                  fg=COLOR_TEXT_PRI, relief="flat", cursor="hand2",
                  padx=12, pady=4,
                  command=self.save_task_changes).pack(side="left")

    # =========================================================================
    # STICKY WALL VIEW
    # =========================================================================
    def show_sticky_wall(self):
        # Switch to sticky wall view and update sidebar
        self.current_view = "sticky"
        self.set_active_nav("sticky")
        self.heading_label.configure(text="Sticky Wall")

        # Hide the normal task list widgets and show the sticky wall
        self.task_canvas.pack_forget()
        self.stats_bar.pack_forget()
        self.add_form_frame.pack_forget()
        self.add_form_open = False

        self.sticky_wall_frame.pack(fill="both", expand=True)
        self.render_sticky_wall()

    def render_sticky_wall(self):
        # Clear any existing sticky notes shown
        for widget in self.sticky_wall_frame.winfo_children():
            widget.destroy()

        # Scrollable canvas so many notes don't get clipped
        canvas = tk.Canvas(self.sticky_wall_frame, bg=COLOR_BG, highlightthickness=0)
        vsb = ttk.Scrollbar(self.sticky_wall_frame, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        # Inner frame placed inside the canvas
        inner = tk.Frame(canvas, bg=COLOR_BG)
        canvas_window = canvas.create_window((0, 0), window=inner, anchor="nw")

        def on_inner_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def on_canvas_resize(event):
            canvas.itemconfigure(canvas_window, width=event.width)

        inner.bind("<Configure>", on_inner_configure)
        canvas.bind("<Configure>", on_canvas_resize)
        canvas.bind("<MouseWheel>", lambda e: canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

        notes = database.get_all_sticky_notes()

        # --- 3-column grid layout ---
        COLS = 3
        for index, note in enumerate(notes):
            note_id      = note[0]
            note_title   = note[1]
            note_content = note[2]
            note_color   = note[3]

            grid_row = index // COLS
            grid_col = index % COLS

            # Outer card frame — auto-sizes to its content, min width via padx
            card = tk.Frame(inner, bg=note_color, padx=18, pady=16)
            card.grid(row=grid_row, column=grid_col, padx=14, pady=14, sticky="nsew")

            # Top row: bold title on left, delete ✕ button on right
            top_row = tk.Frame(card, bg=note_color)
            top_row.pack(fill="x")

            tk.Label(top_row, text=note_title,
                     font=(APP_FONT, 11, "bold"),
                     bg=note_color, fg=COLOR_TEXT_PRI,
                     anchor="w", wraplength=180,
                     justify="left").pack(side="left", fill="x", expand=True)

            tk.Button(top_row, text="✕",
                      font=(APP_FONT, 9), bg=note_color, fg=COLOR_TEXT_SEC,
                      relief="flat", cursor="hand2", bd=0,
                      activebackground=note_color,
                      command=lambda nid=note_id: self.delete_note(nid)).pack(side="right", anchor="n")

            # Spacer between title and content
            tk.Frame(card, bg=note_color, height=8).pack()

            # Content text — wraps naturally, no fixed height
            tk.Label(card, text=note_content,
                     font=(APP_FONT, 10),
                     bg=note_color, fg="#555555",
                     anchor="nw", wraplength=200,
                     justify="left").pack(fill="x", anchor="w")

        # Give each column equal weight so cards stretch evenly
        for c in range(COLS):
            inner.columnconfigure(c, weight=1, minsize=200)

        # --- "+ New Note" card in the next available cell ---
        add_row = len(notes) // COLS
        add_col = len(notes) % COLS

        new_card = tk.Frame(inner, bg="#EFEFEF", padx=18, pady=16)
        new_card.grid(row=add_row, column=add_col, padx=14, pady=14, sticky="nsew")

        # Big "+" button centred in the grey card
        tk.Button(new_card, text="+",
                  font=(APP_FONT, 32), bg="#EFEFEF", fg="#AAAAAA",
                  relief="flat", cursor="hand2", bd=0,
                  activebackground="#E5E5E5",
                  command=self.open_new_note_popup).pack(expand=True, pady=30)

    def open_new_note_popup(self):
        # Small popup window to create a new sticky note
        popup = tk.Toplevel(self.root)
        popup.title("New Sticky Note")
        popup.geometry("300x220")
        popup.resizable(False, False)
        popup.configure(bg=COLOR_BG)
        popup.grab_set()   # Block the main window while popup is open

        tk.Label(popup, text="Note Title:", font=(APP_FONT, 9),
                 bg=COLOR_BG, fg=COLOR_TEXT_SEC).pack(anchor="w", padx=16, pady=(12, 0))
        title_entry = tk.Entry(popup, font=(APP_FONT, 10), bg=COLOR_PANEL,
                               relief="flat", bd=1)
        title_entry.pack(fill="x", padx=16, pady=4)

        tk.Label(popup, text="Content:", font=(APP_FONT, 9),
                 bg=COLOR_BG, fg=COLOR_TEXT_SEC).pack(anchor="w", padx=16)
        content_text = tk.Text(popup, font=(APP_FONT, 10), bg=COLOR_PANEL,
                               relief="flat", height=5)
        content_text.pack(fill="x", padx=16, pady=4)

        def save_note():
            global sticky_color_index
            title   = title_entry.get().strip()
            content = content_text.get("1.0", "end-1c").strip()
            if not title:
                messagebox.showwarning("Missing Info", "Please enter a note title.")
                return
            # Cycle through the sticky note colors
            color = STICKY_COLORS[sticky_color_index % len(STICKY_COLORS)]
            sticky_color_index += 1
            database.add_sticky_note(title, content, color)
            popup.destroy()
            self.render_sticky_wall()

        tk.Button(popup, text="Save Note",
                  font=(APP_FONT, 9, "bold"), bg=COLOR_ACCENT,
                  fg=COLOR_TEXT_PRI, relief="flat", cursor="hand2",
                  command=save_note).pack(pady=6)

    def delete_note(self, note_id):
        # Delete a sticky note after confirmation
        confirmed = messagebox.askyesno("Delete Note", "Are you sure you want to delete this note?")
        if confirmed:
            database.delete_sticky_note(note_id)
            self.render_sticky_wall()

    # =========================================================================
    # NAVIGATION ACTIONS
    # =========================================================================

    def show_tasks(self):
        # Switch to the main Tasks view — shows all tasks sorted by deadline
        self.current_view = "tasks"
        self.set_active_nav("tasks")
        self.heading_label.configure(text="Tasks")
        self.show_task_list_view()
        self.refresh_tasks()

    def show_subject(self, subject):
        # Filter the task list to show only tasks belonging to a specific subject
        self.current_view = "tasks"
        self.set_active_nav("tasks")
        self.filter_subject = subject
        self.filter_priority = None
        self.heading_label.configure(text=subject)
        self.show_task_list_view()
        self.refresh_tasks()

    def show_task_list_view(self):
        # Hide sticky wall and show the task list
        self.sticky_wall_frame.pack_forget()
        self.task_canvas.pack(side="left", fill="both", expand=True)
        self.stats_bar.pack(fill="x")

    # =========================================================================
    # TASK LIST REFRESH — redraws all task cards
    # =========================================================================
    def refresh_tasks(self):
        # Load tasks from the database (apply subject + status filters if active)
        all_tasks = database.get_tasks_by_filter(self.filter_subject, self.filter_status)

        # Apply priority tag filter if one is set
        if self.filter_priority:
            filtered = []
            for task in all_tasks:
                if task[4] == self.filter_priority:
                    filtered.append(task)
            all_tasks = filtered

        # Apply search query if one is set
        if self.search_query:
            all_tasks = features.search_tasks(all_tasks, self.search_query)

        # Sort tasks by deadline (earliest first).
        # Tasks with no deadline ("") are moved to the end.
        def sort_key(task):
            deadline = task[3]
            if deadline and deadline.strip():
                try:
                    parsed = datetime.datetime.strptime(deadline.strip(), "%d-%m-%y").date()
                    return (0, parsed)
                except ValueError:
                    return (1, datetime.date.max)
            return (1, datetime.date.max)

        all_tasks.sort(key=sort_key)

        # Clear the old task cards
        for widget in self.task_list_frame.winfo_children():
            widget.destroy()

        # Draw a card for each task
        for task in all_tasks:
            self.draw_task_card(self.task_list_frame, task)

        # Update the badge count and stats bar
        count = len(all_tasks)
        self.badge_canvas.itemconfigure(self.badge_text_id, text=str(count))

        stats = features.get_stats(all_tasks)
        stats_text = "{} done · {} pending · {} total".format(
            stats["done"], stats["pending"], stats["total"]
        )
        self.stats_bar.configure(text=stats_text)

        # Update subject filter dropdown with current subjects
        subjects = features.get_unique_subjects(database.get_all_tasks())
        self.subject_combo.configure(values=subjects)

        # Update the subject dropdown in the detail panel too
        self.detail_subject_combo.configure(values=subjects)

        # Refresh the sidebar subject list
        self.refresh_sidebar_lists()

    def refresh_sidebar_lists(self):
        # Clear old subject list items
        for widget in self.lists_frame.winfo_children():
            widget.destroy()

        all_tasks = database.get_all_tasks()

        # Collect subjects from tasks
        task_subjects = features.get_unique_subjects(all_tasks)
        if "All" in task_subjects:
            task_subjects.remove("All")

        # Also collect subjects saved in the lists table (user-created lists)
        saved_lists = database.get_all_lists()

        # Merge both sets and remove duplicates, then sort
        combined = list(set(task_subjects + saved_lists))
        combined.sort()

        for subject in combined:
            # Assign a random dot color to new subjects
            if subject not in subject_dot_colors:
                subject_dot_colors[subject] = "#{:06x}".format(random.randint(0x888888, 0xDDDDDD))

            dot_color = subject_dot_colors[subject]

            # Count tasks for this subject
            subject_count = sum(1 for t in all_tasks if t[1] == subject)

            # Use a Frame as the row but bind clicks on every child to show_subject
            row = tk.Frame(self.lists_frame, bg=COLOR_PANEL, padx=12, pady=3,
                           cursor="hand2")
            row.pack(fill="x")

            # Colored dot canvas
            dot = tk.Canvas(row, width=10, height=10, bg=COLOR_PANEL,
                            highlightthickness=0, cursor="hand2")
            dot.create_oval(1, 1, 9, 9, fill=dot_color, outline="")
            dot.pack(side="left")

            # Subject name label
            name_lbl = tk.Label(row, text=subject, font=(APP_FONT, 9),
                                bg=COLOR_PANEL, fg=COLOR_TEXT_PRI, cursor="hand2")
            name_lbl.pack(side="left", padx=4)

            # Task count badge label
            count_lbl = tk.Label(row, text=str(subject_count), font=(APP_FONT, 9),
                                 bg=COLOR_PANEL, fg=COLOR_TEXT_SEC, cursor="hand2")
            count_lbl.pack(side="right")

            # Bind clicks on the row frame and every child widget
            for widget in (row, dot, name_lbl, count_lbl):
                widget.bind("<Button-1>",
                            lambda e, s=subject: self.show_subject(s))

    # =========================================================================
    # ADD TASK FORM — inline toggle
    # =========================================================================
    def toggle_add_form(self):
        # Show or hide the inline add-task form
        if self.add_form_open:
            self.add_form_frame.pack_forget()
            self.add_form_open = False
        else:
            # Pack the form just above the task list container (both are children of self.center)
            self.add_form_frame.pack(fill="x", pady=4, before=self.list_container)
            self.add_form_open = True
            self.new_subject.focus_set()

    def submit_new_task(self):
        # Read values from the inline form
        task_name = self.new_task_name.get().strip()
        subject   = self.new_subject.get().strip()
        deadline  = self.new_deadline.get().strip()
        priority  = self.new_priority.get()

        # Validate: task name and subject are required
        if not task_name or not subject:
            messagebox.showwarning("Missing Info", "Please enter a task name and subject.")
            return

        # If deadline still shows the placeholder, save it as empty
        if deadline == "DD-MM-YY":
            deadline = ""

        # Save to database
        database.add_task(subject, task_name, deadline, priority)

        # Clear the form fields
        self.new_task_name.delete(0, "end")
        self.new_subject.delete(0, "end")
        self.new_deadline.delete(0, "end")
        self.new_deadline.insert(0, "DD-MM-YY")
        self.new_priority.set("Medium")

        # Hide the form and refresh the task list
        self.toggle_add_form()
        self.refresh_tasks()

    # =========================================================================
    # TASK ACTIONS
    # =========================================================================
    def toggle_done(self, task_id, var):
        # Check or uncheck a task based on checkbox value
        if var.get() == 1:
            database.mark_task_done(task_id)
        else:
            database.unmark_task_done(task_id)
        self.refresh_tasks()

    def open_detail_panel(self, task):
        # Show the right panel and fill in the task details
        self.selected_task = task

        task_id      = task[0]
        subject      = task[1]
        task_name    = task[2]
        deadline     = task[3]
        priority     = task[4]
        description  = task[6] if len(task) > 6 else ""

        # Attach the right panel to the window
        self.right_panel.pack(side="right", fill="y")
        self.right_panel.pack_propagate(False)

        # Fill in the fields
        self.detail_task_name.delete(0, "end")
        self.detail_task_name.insert(0, task_name)

        self.detail_description.delete("1.0", "end")
        self.detail_description.insert("1.0", description)

        self.detail_subject_var.set(subject)
        self.detail_deadline.delete(0, "end")
        self.detail_deadline.insert(0, deadline)
        self.detail_priority.set(priority)

        # Load and display subtasks
        self.refresh_subtasks(task_id)

    def refresh_subtasks(self, task_id):
        # Clear old subtask widgets
        for widget in self.subtasks_frame.winfo_children():
            widget.destroy()

        subtasks = database.get_subtasks(task_id)

        for subtask in subtasks:
            sub_id   = subtask[0]
            sub_name = subtask[2]
            sub_done = subtask[3]

            var = tk.IntVar(value=sub_done)
            cb = tk.Checkbutton(self.subtasks_frame, text=sub_name,
                                variable=var, bg=COLOR_PANEL,
                                font=(APP_FONT, 9), fg=COLOR_TEXT_PRI,
                                activebackground=COLOR_PANEL,
                                command=lambda sid=sub_id: database.mark_subtask_done(sid))
            cb.pack(anchor="w", pady=1)

    def add_subtask_from_panel(self):
        # Ask the user to type a subtask name in a simple dialog
        if not self.selected_task:
            return

        popup = tk.Toplevel(self.root)
        popup.title("Add Subtask")
        popup.geometry("260x100")
        popup.resizable(False, False)
        popup.configure(bg=COLOR_BG)
        popup.grab_set()

        tk.Label(popup, text="Subtask name:", font=(APP_FONT, 9),
                 bg=COLOR_BG).pack(padx=12, pady=(10, 2), anchor="w")
        entry = tk.Entry(popup, font=(APP_FONT, 10), bg=COLOR_PANEL, relief="flat")
        entry.pack(fill="x", padx=12, pady=2)
        entry.focus_set()

        def save_subtask():
            name = entry.get().strip()
            if name:
                database.add_subtask(self.selected_task[0], name)
                popup.destroy()
                self.refresh_subtasks(self.selected_task[0])

        tk.Button(popup, text="Add", font=(APP_FONT, 9, "bold"),
                  bg=COLOR_ACCENT, fg=COLOR_TEXT_PRI, relief="flat", cursor="hand2",
                  command=save_subtask).pack(pady=6)

    def save_task_changes(self):
        # Read values from the detail panel and save to database
        if not self.selected_task:
            return

        task_id     = self.selected_task[0]
        task_name   = self.detail_task_name.get().strip()
        subject     = self.detail_subject_var.get().strip()
        deadline    = self.detail_deadline.get().strip()
        priority    = self.detail_priority.get()
        description = self.detail_description.get("1.0", "end-1c").strip()

        if not task_name:
            messagebox.showwarning("Missing Info", "Task name cannot be empty.")
            return

        database.update_task(task_id, subject, task_name, deadline, priority, description)
        self.refresh_tasks()
        messagebox.showinfo("Saved", "Task updated successfully!")

    def close_right_panel(self):
        # Hide the right detail panel and clear the selected task
        self.right_panel.pack_forget()
        self.selected_task = None

    def delete_selected_task(self):
        # Confirm and delete the currently selected task
        if not self.selected_task:
            return

        confirmed = messagebox.askyesno("Delete Task",
                                        "Are you sure you want to delete this task?")
        if confirmed:
            database.delete_task(self.selected_task[0])
            self.selected_task = None
            self.right_panel.pack_forget()   # Hide the right panel
            self.refresh_tasks()

    # =========================================================================
    # FILTER ACTIONS
    # =========================================================================
    def apply_filter(self):
        # Read filter values and refresh the list
        self.filter_subject  = self.subject_combo.get()
        self.filter_status   = self.status_combo.get()
        self.filter_priority = None   # Clear tag filter when applying dropdowns
        self.refresh_tasks()

    def filter_by_priority(self, priority):
        # Filter tasks by the clicked tag pill
        self.filter_priority = priority
        self.filter_subject  = "All"
        self.filter_status   = "All"
        self.refresh_tasks()

    # =========================================================================
    # SEARCH
    # =========================================================================
    def on_search_changed(self, *args):
        # Called every time the search box text changes
        query = self.search_var.get()
        if query == "Search...":
            query = ""
        self.search_query = query
        self.refresh_tasks()

    def on_search_focus_in(self, event):
        # Clear the placeholder text when the user clicks the search box
        if self.search_entry_widget.get() == "Search...":
            self.search_entry_widget.delete(0, "end")
            self.search_entry_widget.configure(fg=COLOR_TEXT_PRI)

    def on_search_focus_out(self, event):
        # Restore placeholder if the search box is left empty
        if self.search_entry_widget.get() == "":
            self.search_entry_widget.insert(0, "Search...")
            self.search_entry_widget.configure(fg=COLOR_TEXT_SEC)

    # =========================================================================
    # ADD NEW LIST POPUP
    # =========================================================================
    def open_add_list_popup(self):
        # Small popup to add a new subject/list name
        popup = tk.Toplevel(self.root)
        popup.title("New List")
        popup.geometry("260x110")
        popup.resizable(False, False)
        popup.configure(bg=COLOR_BG)
        popup.grab_set()

        tk.Label(popup, text="List name:", font=(APP_FONT, 9),
                 bg=COLOR_BG, fg=COLOR_TEXT_SEC).pack(anchor="w", padx=16, pady=(14, 2))

        entry = tk.Entry(popup, font=(APP_FONT, 10), bg=COLOR_PANEL,
                         relief="flat", bd=1)
        entry.pack(fill="x", padx=16, ipady=4)
        entry.focus_set()

        def confirm(event=None):
            name = entry.get().strip()
            if not name:
                messagebox.showwarning("Missing Name", "Please type a list name.", parent=popup)
                return
            # Save the new list name to the database so it persists
            database.add_list(name)
            popup.destroy()
            # Refresh the sidebar so the new list appears immediately
            self.refresh_sidebar_lists()

        entry.bind("<Return>", confirm)
        tk.Button(popup, text="Add List",
                  font=(APP_FONT, 9, "bold"), bg=COLOR_ACCENT,
                  fg=COLOR_TEXT_PRI, relief="flat", cursor="hand2",
                  command=confirm).pack(pady=8)

    # =========================================================================
    # BOTTOM SIDEBAR BUTTONS
    # =========================================================================
    def show_settings(self):
        messagebox.showinfo("Settings", "⚙ Settings panel coming soon!")

    def show_signout(self):
        messagebox.showinfo("Sign Out", "↪ You have been signed out.\n(This is a desktop app — no login required.)")

    # =========================================================================
    # SCROLLING HELPERS
    # =========================================================================
    def on_task_frame_configure(self, event):
        # Update the canvas scroll region to match the inner frame
        self.task_canvas.configure(scrollregion=self.task_canvas.bbox("all"))

    def on_canvas_configure(self, event):
        # Stretch the inner frame to fit the canvas width
        self.task_canvas.itemconfigure(self.task_canvas_window, width=event.width)

    def on_mousewheel(self, event):
        # Scroll the canvas with the mouse wheel
        self.task_canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


# =============================================================================
# ENTRY POINT — runs when you execute: python main.py
# =============================================================================
if __name__ == "__main__":
    root = tk.Tk()
    app = StudyPlannerApp(root)

    # Set the default active nav item to "tasks"
    app.set_active_nav("tasks")

    # Start the Tkinter event loop (keeps the window open)
    root.mainloop()
