"""
============================================================
  Pomodoro Timer — Python GUI Project
  Built with : Tkinter (standard library only)
  Version    : 1.0
============================================================
"""

import tkinter as tk
from tkinter import messagebox, font
import time
import threading
import winsound  # Windows only — see play_sound() for cross-platform fallback


# ============================================================
#  CONSTANTS — Centralized config (easy to change)
# ============================================================

# Default durations in seconds (60 * minutes)
DEFAULT_WORK_MINUTES  = 25
DEFAULT_BREAK_MINUTES = 5

# Colors — Dark minimal theme
BG_COLOR         = "#1A1A2E"   # Deep navy background
CARD_COLOR       = "#16213E"   # Slightly lighter card
ACCENT_WORK      = "#E94560"   # Red-pink for work mode
ACCENT_BREAK     = "#0F9B8E"   # Teal for break mode
TEXT_COLOR       = "#EAEAEA"   # Off-white text
SUBTEXT_COLOR    = "#8892A4"   # Muted gray for labels
BTN_START_BG     = "#E94560"
BTN_PAUSE_BG     = "#F5A623"
BTN_RESET_BG     = "#4A4A6A"
BTN_TEXT         = "#FFFFFF"

# Fonts
FONT_TIMER       = ("Courier", 72, "bold")   # Big clock display
FONT_MODE        = ("Helvetica", 16, "bold")
FONT_LABEL       = ("Helvetica", 11)
FONT_BTN         = ("Helvetica", 12, "bold")
FONT_COUNT       = ("Helvetica", 13)
FONT_SETTINGS    = ("Helvetica", 10)


# ============================================================
#  POMODORO APP CLASS — Main application
# ============================================================

class PomodoroApp:
    """
    Main Pomodoro Timer application class.
    Manages all state, UI, and timer logic.
    """

    def __init__(self, root):
        self.root = root
        self._setup_window()

        # --- State Variables ---
        self.work_minutes  = tk.IntVar(value=DEFAULT_WORK_MINUTES)
        self.break_minutes = tk.IntVar(value=DEFAULT_BREAK_MINUTES)

        self.is_running    = False   # Is timer currently counting down?
        self.is_paused     = False   # Is timer paused?
        self.mode          = "work"  # Current mode: "work" or "break"
        self.sessions_done = 0       # Completed pomodoro sessions

        # Time left in current session (in seconds)
        self.time_left = DEFAULT_WORK_MINUTES * 60

        # Threading event to signal the timer thread to stop
        self._stop_event = threading.Event()

        # Build the UI
        self._build_ui()

        # Show initial time on screen
        self._update_display()

    # ----------------------------------------------------------
    #  WINDOW SETUP
    # ----------------------------------------------------------

    def _setup_window(self):
        """Configure the main application window."""
        self.root.title("🍅 Pomodoro Timer")
        self.root.geometry("480x620")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_COLOR)
        # Center window on screen
        self.root.eval("tk::PlaceWindow . center")

    # ----------------------------------------------------------
    #  UI BUILDER
    # ----------------------------------------------------------

    def _build_ui(self):
        """Build and layout all UI widgets."""

        # ── Top Title ──────────────────────────────────────────
        title_frame = tk.Frame(self.root, bg=BG_COLOR)
        title_frame.pack(pady=(30, 0))

        tk.Label(
            title_frame,
            text="🍅 POMODORO",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=("Helvetica", 22, "bold")
        ).pack()

        tk.Label(
            title_frame,
            text="Focus. Rest. Repeat.",
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
            font=FONT_SETTINGS
        ).pack()

        # ── Timer Card ─────────────────────────────────────────
        self.card = tk.Frame(
            self.root,
            bg=CARD_COLOR,
            bd=0,
            relief="flat",
            highlightthickness=2,
            highlightbackground=ACCENT_WORK
        )
        self.card.pack(pady=25, padx=40, fill="x")

        # Mode label (WORK SESSION / BREAK TIME)
        self.mode_label = tk.Label(
            self.card,
            text="WORK SESSION",
            bg=CARD_COLOR,
            fg=ACCENT_WORK,
            font=FONT_MODE
        )
        self.mode_label.pack(pady=(25, 5))

        # Big countdown timer display
        self.timer_label = tk.Label(
            self.card,
            text="25:00",
            bg=CARD_COLOR,
            fg=TEXT_COLOR,
            font=FONT_TIMER
        )
        self.timer_label.pack(pady=(5, 5))

        # Progress bar (visual strip under timer)
        self.progress_canvas = tk.Canvas(
            self.card,
            width=360,
            height=6,
            bg=CARD_COLOR,
            highlightthickness=0
        )
        self.progress_canvas.pack(pady=(0, 20))
        # Background track
        self.progress_canvas.create_rectangle(0, 0, 360, 6, fill="#2A2A4A", outline="")
        # Foreground fill — stored as an ID so we can update it
        self.progress_bar = self.progress_canvas.create_rectangle(
            0, 0, 360, 6, fill=ACCENT_WORK, outline=""
        )

        # ── Session Counter ────────────────────────────────────
        counter_frame = tk.Frame(self.root, bg=BG_COLOR)
        counter_frame.pack(pady=(0, 15))

        tk.Label(
            counter_frame,
            text="Completed Sessions:",
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
            font=FONT_LABEL
        ).pack(side="left", padx=(0, 8))

        self.session_label = tk.Label(
            counter_frame,
            text="🍅 × 0",
            bg=BG_COLOR,
            fg=TEXT_COLOR,
            font=FONT_COUNT
        )
        self.session_label.pack(side="left")

        # ── Control Buttons ────────────────────────────────────
        btn_frame = tk.Frame(self.root, bg=BG_COLOR)
        btn_frame.pack(pady=10)

        self.start_btn = self._make_button(
            btn_frame, "▶  START", BTN_START_BG, self.start_timer
        )
        self.start_btn.pack(side="left", padx=8)

        self.pause_btn = self._make_button(
            btn_frame, "⏸  PAUSE", BTN_PAUSE_BG, self.pause_timer
        )
        self.pause_btn.pack(side="left", padx=8)
        self.pause_btn.config(state="disabled")  # Disabled until timer starts

        self.reset_btn = self._make_button(
            btn_frame, "↺  RESET", BTN_RESET_BG, self.reset_timer
        )
        self.reset_btn.pack(side="left", padx=8)

        # ── Settings Panel ─────────────────────────────────────
        settings_frame = tk.LabelFrame(
            self.root,
            text="  ⚙ Settings  ",
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
            font=FONT_SETTINGS,
            bd=1,
            relief="groove",
            labelanchor="n"
        )
        settings_frame.pack(pady=20, padx=40, fill="x")

        # Work duration setting
        work_row = tk.Frame(settings_frame, bg=BG_COLOR)
        work_row.pack(pady=(12, 4), padx=15, fill="x")

        tk.Label(work_row, text="Work Duration (min):",
                 bg=BG_COLOR, fg=TEXT_COLOR, font=FONT_SETTINGS).pack(side="left")

        work_spin = tk.Spinbox(
            work_row,
            from_=1, to=60,
            textvariable=self.work_minutes,
            width=5,
            font=FONT_SETTINGS,
            bg="#2A2A4A", fg=TEXT_COLOR,
            buttonbackground="#2A2A4A",
            relief="flat",
            command=self._on_settings_change
        )
        work_spin.pack(side="right")
        work_spin.bind("<Return>", lambda e: self._on_settings_change())

        # Break duration setting
        break_row = tk.Frame(settings_frame, bg=BG_COLOR)
        break_row.pack(pady=(4, 12), padx=15, fill="x")

        tk.Label(break_row, text="Break Duration (min):",
                 bg=BG_COLOR, fg=TEXT_COLOR, font=FONT_SETTINGS).pack(side="left")

        break_spin = tk.Spinbox(
            break_row,
            from_=1, to=30,
            textvariable=self.break_minutes,
            width=5,
            font=FONT_SETTINGS,
            bg="#2A2A4A", fg=TEXT_COLOR,
            buttonbackground="#2A2A4A",
            relief="flat",
            command=self._on_settings_change
        )
        break_spin.pack(side="right")
        break_spin.bind("<Return>", lambda e: self._on_settings_change())

        # ── Footer ─────────────────────────────────────────────
        tk.Label(
            self.root,
            text="Stay focused. One session at a time. 🔥",
            bg=BG_COLOR,
            fg=SUBTEXT_COLOR,
            font=("Helvetica", 9)
        ).pack(side="bottom", pady=12)

    def _make_button(self, parent, text, bg_color, command):
        """Helper to create a styled button."""
        btn = tk.Button(
            parent,
            text=text,
            bg=bg_color,
            fg=BTN_TEXT,
            font=FONT_BTN,
            width=9,
            height=1,
            relief="flat",
            cursor="hand2",
            activebackground=bg_color,
            activeforeground=BTN_TEXT,
            command=command,
            bd=0,
            padx=10,
            pady=8
        )
        # Hover effects
        btn.bind("<Enter>", lambda e: btn.config(bg=self._lighten(bg_color)))
        btn.bind("<Leave>", lambda e: btn.config(bg=bg_color))
        return btn

    @staticmethod
    def _lighten(hex_color):
        """Make a hex color slightly lighter for hover effect."""
        hex_color = hex_color.lstrip("#")
        r, g, b = int(hex_color[0:2], 16), int(hex_color[2:4], 16), int(hex_color[4:6], 16)
        # Increase brightness by 30, clamp to 255
        r = min(r + 30, 255)
        g = min(g + 30, 255)
        b = min(b + 30, 255)
        return f"#{r:02x}{g:02x}{b:02x}"

    # ----------------------------------------------------------
    #  TIMER CONTROL FUNCTIONS
    # ----------------------------------------------------------

    def start_timer(self):
        """
        Start the countdown timer.
        Runs in a background thread so the UI doesn't freeze.
        """
        if self.is_running:
            return  # Already running, do nothing

        self.is_running = True
        self.is_paused  = False

        # Reset the stop signal for the new thread
        self._stop_event.clear()

        # Update button states
        self.start_btn.config(state="disabled")
        self.pause_btn.config(state="normal")

        # Launch countdown in a separate thread
        # daemon=True means thread dies when main window closes
        timer_thread = threading.Thread(target=self._countdown, daemon=True)
        timer_thread.start()

    def pause_timer(self):
        """Toggle between pause and resume."""
        if not self.is_running:
            return

        if self.is_paused:
            # ── Resume ──
            self.is_paused = False
            self.pause_btn.config(text="⏸  PAUSE")
            # Restart the thread with remaining time
            self._stop_event.clear()
            timer_thread = threading.Thread(target=self._countdown, daemon=True)
            timer_thread.start()
        else:
            # ── Pause ──
            self.is_paused = True
            self.pause_btn.config(text="▶  RESUME")
            # Signal the running thread to stop
            self._stop_event.set()

    def reset_timer(self):
        """
        Stop everything and reset to beginning of current mode.
        """
        # Signal thread to stop
        self._stop_event.set()

        self.is_running = False
        self.is_paused  = False
        self.mode       = "work"

        # Reset time to full work duration
        self.time_left  = self.work_minutes.get() * 60

        # Reset buttons
        self.start_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="⏸  PAUSE")

        # Refresh display
        self._update_mode_ui()
        self._update_display()

    def _countdown(self):
        """
        Core countdown logic — runs in a background thread.
        Counts down self.time_left by 1 second per tick.
        Uses after() to safely update Tkinter UI from thread.
        """
        while self.time_left > 0:
            # Check if we should stop (pause or reset triggered)
            if self._stop_event.is_set():
                return

            # Sleep 1 second
            time.sleep(1)

            # Check again after sleep (in case reset happened during sleep)
            if self._stop_event.is_set():
                return

            # Decrement time
            self.time_left -= 1

            # Safely update UI from main thread using after(0, ...)
            self.root.after(0, self._update_display)

        # Time ran out — switch mode (only if not stopped)
        if not self._stop_event.is_set():
            self.root.after(0, self._session_complete)

    # ----------------------------------------------------------
    #  SESSION SWITCHING
    # ----------------------------------------------------------

    def _session_complete(self):
        """
        Called when a countdown finishes naturally.
        Plays a sound, shows a notification, and switches mode.
        """
        self.is_running = False
        self.play_sound()

        if self.mode == "work":
            # Work session just ended
            self.sessions_done += 1
            self.session_label.config(text=f"🍅 × {self.sessions_done}")
            messagebox.showinfo(
                "🍅 Pomodoro Complete!",
                f"Great work! Session #{self.sessions_done} done.\nTime for a break! ☕"
            )
            self.switch_mode("break")
        else:
            # Break just ended
            messagebox.showinfo(
                "⏰ Break Over!",
                "Break's over! Back to work! 💪"
            )
            self.switch_mode("work")

    def switch_mode(self, new_mode):
        """
        Switch between 'work' and 'break' mode.
        Updates time_left and refreshes the UI.
        """
        self.mode = new_mode

        if new_mode == "work":
            self.time_left = self.work_minutes.get() * 60
        else:
            self.time_left = self.break_minutes.get() * 60

        # Update colors, labels, progress bar
        self._update_mode_ui()
        self._update_display()

        # Auto-start next session
        self.start_timer()

    def _update_mode_ui(self):
        """Update colors and labels to reflect current mode."""
        if self.mode == "work":
            accent = ACCENT_WORK
            label  = "WORK SESSION"
        else:
            accent = ACCENT_BREAK
            label  = "☕ BREAK TIME"

        # Update card border color
        self.card.config(highlightbackground=accent)

        # Update mode label text and color
        self.mode_label.config(text=label, fg=accent)

        # Update progress bar color
        self.progress_canvas.itemconfig(self.progress_bar, fill=accent)

    # ----------------------------------------------------------
    #  DISPLAY UPDATE
    # ----------------------------------------------------------

    def _update_display(self):
        """
        Refresh the timer label and progress bar.
        Called every second by the countdown thread via after().
        """
        # Convert seconds → MM:SS
        minutes = self.time_left // 60
        seconds = self.time_left % 60
        time_str = f"{minutes:02d}:{seconds:02d}"

        self.timer_label.config(text=time_str)

        # Calculate progress (1.0 = full, 0.0 = empty)
        total = (
            self.work_minutes.get() * 60
            if self.mode == "work"
            else self.break_minutes.get() * 60
        )
        # Avoid division by zero
        progress = self.time_left / total if total > 0 else 0
        bar_width = int(360 * progress)

        # Update progress bar fill width
        self.progress_canvas.coords(self.progress_bar, 0, 0, bar_width, 6)

        # Update window title with live countdown
        mode_name = "Work" if self.mode == "work" else "Break"
        self.root.title(f"🍅 {time_str} — {mode_name}")

    # ----------------------------------------------------------
    #  SETTINGS HANDLER
    # ----------------------------------------------------------

    def _on_settings_change(self):
        """
        Called when user changes work/break duration in spinboxes.
        Only applies if timer is not running.
        """
        if self.is_running:
            messagebox.showwarning(
                "Timer Running",
                "Stop or reset the timer before changing settings."
            )
            return

        # Update time_left to match new setting for current mode
        if self.mode == "work":
            self.time_left = self.work_minutes.get() * 60
        else:
            self.time_left = self.break_minutes.get() * 60

        self._update_display()

    # ----------------------------------------------------------
    #  SOUND ALERT
    # ----------------------------------------------------------

    def play_sound(self):
        """
        Play a simple alert sound when a session ends.
        Uses winsound on Windows (built-in).
        Falls back to terminal bell on Mac/Linux.
        """
        try:
            # Windows: play a system beep (frequency=880Hz, duration=500ms)
            winsound.Beep(880, 400)
            winsound.Beep(660, 400)
        except Exception:
            # Mac / Linux fallback — terminal bell
            print("\a", end="", flush=True)


# ============================================================
#  MAIN — Entry point
# ============================================================

def main():
    # Create the main Tkinter window
    root = tk.Tk()

    # Initialize the app
    app = PomodoroApp(root)

    # Start the Tkinter event loop (keeps window open)
    root.mainloop()


if __name__ == "__main__":
    main()
