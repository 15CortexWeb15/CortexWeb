"""Entry point for the CORTEX system with GUI support."""

import os
import random
import shutil
import sys
import webbrowser
from datetime import datetime
from pathlib import Path
from tkinter import (
    BOTH,
    DISABLED,
    END,
    LEFT,
    NORMAL,
    RIGHT,
    Scale,
    StringVar,
    TOP,
    Scrollbar,
    Text,
    Tk,
    Toplevel,
    PhotoImage,
    Button,
    Canvas,
    Entry,
    Frame,
    Label,
    X,
    Y,
    filedialog,
    simpledialog,
)
from tkinter import ttk
import tkinter.font as tkfont
from urllib.parse import quote_plus

from core.brain import CortexBrain


def repl(brain: CortexBrain) -> None:
    print("CORTEX REPL mode. Type STOP to exit.")
    while True:
        try:
            command = input("CORTEX> ").strip()
        except EOFError:
            print()
            break
        if not command:
            continue
        if command.lower() in ("stop", "exit", "quit"):
            print("CORTEX shutting down.")
            break
        print(brain.execute_command(command))


class CortexGUI:
    def __init__(self, brain: CortexBrain) -> None:
        self.brain = brain
        self.root = Tk()
        self.root.title("CORTEX Assistant")
        self.root.geometry("860x600")
        self.root.minsize(760, 520)
        self.root.configure(bg="#050505")

        self.style = ttk.Style(self.root)
        try:
            self.style.theme_use("vista")
        except Exception:
            try:
                self.style.theme_use("clam")
            except Exception:
                pass
        self.style.configure(
            "TLabel",
            background="#0f1720",
            foreground="#e5e7eb",
            font=("Segoe UI Variable", 10),
        )
        self.root.option_add("*Font", ("Segoe UI Variable", 11))
        self.root.bind("<Control-Return>", self.on_submit)
        self.root.bind("<Control-s>", lambda event: self.open_feature_panel("Settings"))
        self.root.bind("<Alt-b>", lambda event: self._open_browser_window())

        self.feature_panel = None
        self.panel_width = 0
        self.panel_target_width = 0
        self.font_size = 12
        self.current_theme = "Dark"
        self.base_font_family = "Segoe UI Variable"
        self.nav_title_font = tkfont.Font(family="Segoe UI Black", size=18, weight="bold")
        self.nav_subtitle_font = tkfont.Font(family="Segoe UI", size=9)
        self.main_title_font = tkfont.Font(family="Segoe UI Black", size=26, weight="bold")
        self.main_subtitle_font = tkfont.Font(family="Segoe UI", size=10)
        self.input_label_font = tkfont.Font(family="Segoe UI Variable", size=9)
        self.send_button_font = tkfont.Font(family="Segoe UI Variable", size=10, weight="bold")
        self.user_name = self.brain.memory.get_user_name() or ""
        self.root.withdraw()
        self._build_widgets()
        self._show_splash_screen()
        self._ensure_user_name()
        self.append_text(
            "Welcome to CORTEX Assistant — your modern AI companion.\n"
            "Ask anything or request a simulation, and I’ll respond naturally."
        )
        self._update_clock()

    def _build_widgets(self) -> None:
        main_frame = Frame(self.root, bg="#070707")
        main_frame.pack(fill=BOTH, expand=True, padx=14, pady=14)

        nav_frame = Frame(main_frame, bg="#0f172a", width=220)
        nav_frame.pack(side=LEFT, fill=Y, padx=(0, 10), pady=0)
        nav_frame.pack_propagate(False)

        nav_title = Label(
            nav_frame,
            text="CORTEX Hub",
            fg="#a5b4fc",
            bg="#0f172a",
            font=self.nav_title_font,
        )
        nav_title.pack(anchor="nw", padx=16, pady=(16, 8))

        nav_subtitle = Label(
            nav_frame,
            text="Your assistant control center",
            fg="#cbd5e1",
            bg="#0f172a",
            font=self.nav_subtitle_font,
            wraplength=200,
            justify=LEFT,
        )
        nav_subtitle.pack(anchor="nw", padx=16)

        for label, cmd in [
            ("Browser", "browse example.com"),
            ("Chat Logs", "chatlogs"),
            ("Settings", "settings"),
            ("Clear", "clear"),
        ]:
            self._create_nav_button(nav_frame, label, cmd)

        feature_hint = Label(
            nav_frame,
            text="Alt+B browser · Ctrl+S settings · Ctrl+Enter send",
            fg="#94a3b8",
            bg="#0f172a",
            font=("Segoe UI", 9),
            wraplength=200,
            justify=LEFT,
        )
        feature_hint.pack(anchor="nw", padx=16, pady=(10, 0))

        self.content_frame = Frame(main_frame, bg="#070707")
        self.content_frame.pack(side=LEFT, fill=BOTH, expand=True)

        title_frame = Frame(self.content_frame, bg="#070707")
        title_frame.pack(fill=X, pady=(0, 10))
        title = Label(
            title_frame,
            text="CORTEX Assistant",
            fg="#ffffff",
            bg="#070707",
            font=self.main_title_font,
        )
        title.pack(side=LEFT, anchor="w")

        subtitle = Label(
            title_frame,
            text="A clean, minimal assistant interface for everyday use.",
            fg="#9ca3af",
            bg="#070707",
            font=self.main_subtitle_font,
        )
        subtitle.pack(side=LEFT, padx=(14, 0), anchor="s")

        content_inner = Frame(self.content_frame, bg="#0b1120", bd=0)
        content_inner.pack(fill=BOTH, expand=True)

        self.star_canvas = Canvas(content_inner, bg="#0b1120", highlightthickness=0)
        self.star_canvas.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.star_canvas.bind("<Configure>", self._on_canvas_resize)
        self.star_ids: list[tuple[int, int]] = []

        panel_overlay = Frame(content_inner, bg="#0a1120", bd=0)
        panel_overlay.place(relx=0.03, rely=0.03, relwidth=0.94, relheight=0.94)

        self.output = Text(
            panel_overlay,
            wrap="word",
            state=DISABLED,
            padx=18,
            pady=18,
            bg="#08101f",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
            bd=0,
            highlightthickness=0,
            font=(self.base_font_family, self.font_size),
        )
        scrollbar = Scrollbar(
            content_inner,
            command=self.output.yview,
            troughcolor="#0f172a",
            activebackground="#60a5fa",
            bg="#0f172a",
        )
        self.output.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=RIGHT, fill=Y, padx=(0, 4), pady=12)
        self.output.pack(side=LEFT, fill=BOTH, expand=True, pady=12, padx=(12, 0))

        self._build_quick_tools(content_inner)

        input_frame = Frame(self.content_frame, bg="#0c1320", bd=0, relief="flat", highlightthickness=0)
        input_frame.pack(fill=X, pady=(0, 10), padx=(0, 4), ipady=8)

        input_label = Label(
            input_frame,
            text="Type your command or question here:",
            fg="#cbd5e1",
            bg="#0c1320",
            font=self.input_label_font,
        )
        input_label.pack(anchor="w", padx=16, pady=(10, 2))

        self.input_area = Text(
            input_frame,
            height=4,
            wrap="word",
            bg="#111827",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
            font=("Segoe UI Variable", 11),
            highlightthickness=0,
            bd=0,
            padx=14,
            pady=12,
        )
        self.input_area.pack(fill=X, expand=True, padx=14, pady=(0, 10))
        self.input_area.bind("<Return>", self.on_submit)
        self.input_area.bind("<Shift-Return>", lambda event: self.input_area.insert("insert", "\n"))
        self.input_area.bind("<Control-Return>", self.on_submit)

        send_button = Button(
            input_frame,
            text="Send",
            command=self.on_submit,
            bg="#6366f1",
            fg="#ffffff",
            activebackground="#4f46e5",
            activeforeground="#ffffff",
            relief="flat",
            padx=20,
            pady=12,
            font=self.send_button_font,
        )
        send_button.pack(side=RIGHT, padx=(0, 16), pady=(0, 10))

        self.input_area.focus_set()

        self.status_label = Label(
            self.content_frame,
            text="Ctrl+Enter send · Alt+B browser · Ctrl+S settings",
            fg="#94a3b8",
            bg="#070707",
            font=("Segoe UI Variable", 10),
        )
        self.status_label.pack(side=TOP, fill=X, pady=(0, 0))

        self.root.after(100, self._pulse_status_label)
        self.root.after(100, self._animate_panel)
        self.root.after(1200, self._twinkle_stars)

    def append_text(self, text: str) -> None:
        self.output.configure(state=NORMAL)
        self.output.insert(END, text + "\n\n")
        self.output.see(END)
        self.output.configure(state=DISABLED)

    def _build_quick_tools(self, parent: Frame) -> None:
        card_bg = "#0f172a"
        card = Frame(parent, bg=card_bg, bd=0, highlightthickness=0, relief="flat")
        card.place(relx=0.50, rely=0.01, relwidth=0.47, relheight=0.14)

        card_title = Label(
            card,
            text="Quick Actions",
            fg="#7dd3fc",
            bg=card_bg,
            font=(self.base_font_family, 11, "bold"),
        )
        card_title.pack(anchor="nw", padx=14, pady=(12, 6))

        button_frame = Frame(card, bg=card_bg)
        button_frame.pack(fill=X, padx=12, pady=(0, 10))

        for label, cmd in [
            ("Chat Logs", "chatlogs"),
            ("Open Browser", "browse example.com"),
        ]:
            if cmd.startswith("browse"):
                handler = lambda text=cmd.replace("browse", "", 1).strip(): self._open_browser_window(text)
            else:
                handler = lambda c=cmd: self.run_command(c)
            btn = Button(
                button_frame,
                text=label,
                command=handler,
                bg="#1e293b",
                fg="#e2e8f0",
                activebackground="#2563eb",
                relief="flat",
                padx=10,
                pady=8,
                font=(self.base_font_family, 9, "bold"),
            )
            btn.pack(side=LEFT, expand=True, fill=X, padx=4)

    def _build_settings_panel(self) -> None:
        settings_title = Label(
            self.feature_panel,
            text="CORTEX Settings",
            fg="#7dd3fc",
            bg="#071014",
            font=(self.base_font_family, 14, "bold"),
        )
        settings_title.pack(anchor="nw", padx=16, pady=(4, 6))

        theme_label = Label(
            self.feature_panel,
            text="Theme:",
            fg="#cbd5e1",
            bg="#071014",
            font=(self.base_font_family, 10),
        )
        theme_label.pack(anchor="nw", padx=16, pady=(8, 4))

        theme_var = StringVar(value=self.current_theme)
        theme_selector = Frame(self.feature_panel, bg="#071014")
        theme_selector.pack(fill=X, padx=16)

        for theme in ["Dark", "Apex", "Neon"]:
            button = Button(
                theme_selector,
                text=theme,
                command=lambda t=theme: self._set_theme(t),
                bg="#1f2937" if self.current_theme != theme else "#2563eb",
                fg="#e2e8f0",
                activebackground="#2563eb",
                relief="flat",
                padx=10,
                pady=8,
                font=(self.base_font_family, 10),
            )
            button.pack(side=LEFT, expand=True, fill=X, padx=4)

        font_label = Label(
            self.feature_panel,
            text="Font size:",
            fg="#cbd5e1",
            bg="#071014",
            font=(self.base_font_family, 10),
        )
        font_label.pack(anchor="nw", padx=16, pady=(12, 4))

        font_slider = Scale(
            self.feature_panel,
            from_=10,
            to=18,
            orient="horizontal",
            bg="#071014",
            fg="#e2e8f0",
            troughcolor="#0f172a",
            activebackground="#2563eb",
            command=self._update_font_size,
            length=320,
        )
        font_slider.set(self.font_size)
        font_slider.pack(fill=X, padx=16, pady=(0, 10))

        logo_label = Label(
            self.feature_panel,
            text="Startup logo:",
            fg="#cbd5e1",
            bg="#071014",
            font=(self.base_font_family, 10),
        )
        logo_label.pack(anchor="nw", padx=16, pady=(12, 4))

        logo_button = Button(
            self.feature_panel,
            text="Select logo file",
            command=self._choose_splash_logo,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            relief="flat",
            padx=12,
            pady=10,
            font=(self.base_font_family, 10, "bold"),
        )
        logo_button.pack(anchor="nw", padx=16, pady=(0, 8))

        self.logo_status = Label(
            self.feature_panel,
            text=f"Logo file: {self._get_logo_path().name if self._get_logo_path() else 'default text'}",
            fg="#94a3b8",
            bg="#071014",
            font=(self.base_font_family, 10),
            wraplength=360,
            justify=LEFT,
        )
        self.logo_status.pack(anchor="nw", padx=16, pady=(0, 12))

        self.settings_status = Label(
            self.feature_panel,
            text=f"Current theme: {self.current_theme}  |  Font size: {self.font_size}pt",
            fg="#94a3b8",
            bg="#071014",
            font=(self.base_font_family, 10),
            wraplength=360,
            justify=LEFT,
        )
        self.settings_status.pack(anchor="nw", padx=16, pady=(8, 12))

    def _set_theme(self, theme: str) -> None:
        self.current_theme = theme
        if theme == "Dark":
            self.star_canvas.configure(bg="#0b1120")
            self.content_frame.configure(bg="#070707")
        elif theme == "Apex":
            self.star_canvas.configure(bg="#08101f")
            self.content_frame.configure(bg="#0a0f1b")
        elif theme == "Neon":
            self.star_canvas.configure(bg="#040818")
            self.content_frame.configure(bg="#07101f")
        self._apply_font_settings()
        if hasattr(self, "settings_status"):
            self.settings_status.configure(
                text=f"Current theme: {self.current_theme}  |  Font size: {self.font_size}pt"
            )

    def _choose_splash_logo(self) -> None:
        dialog_path = filedialog.askopenfilename(
            title="Select Cortex logo image",
            filetypes=[("Image files", "*.png;*.gif")],
        )
        if not dialog_path:
            return
        source_path = Path(dialog_path)
        if source_path.suffix.lower() not in {".png", ".gif"}:
            self.logo_status.configure(text="Unsupported file type. Select a PNG or GIF.")
            return

        logo_dir = Path(__file__).resolve().parent / "data"
        logo_dir.mkdir(parents=True, exist_ok=True)
        target_path = logo_dir / f"cortex_logo{source_path.suffix.lower()}"
        try:
            # Remove any existing logo of the alternative extension.
            for alt_ext in {".png", ".gif"} - {source_path.suffix.lower()}:
                alt_path = logo_dir / f"cortex_logo{alt_ext}"
                if alt_path.exists():
                    alt_path.unlink()
            shutil.copy2(source_path, target_path)
            self.logo_file = target_path
            self.logo_status.configure(text=f"Logo file: {target_path.name}")
        except Exception as exc:
            self.logo_status.configure(text=f"Logo selection failed: {exc}")

    def _get_logo_path(self) -> Path | None:
        logo_dir = Path(__file__).resolve().parent / "data"
        for suffix in [".png", ".gif"]:
            candidate = logo_dir / f"cortex_logo{suffix}"
            if candidate.exists():
                return candidate
        return None

    def _load_splash_logo(self) -> PhotoImage | None:
        logo_path = self._get_logo_path()
        if not logo_path:
            return None
        try:
            return PhotoImage(file=str(logo_path))
        except Exception:
            return None

    def _show_splash_screen(self) -> None:
        splash = Toplevel(self.root)
        splash.overrideredirect(True)
        splash.configure(bg="#050505")

        width, height = 520, 340
        screen_width = splash.winfo_screenwidth()
        screen_height = splash.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f"{width}x{height}+{x}+{y}")

        logo_image = self._load_splash_logo()
        if logo_image:
            logo_label = Label(splash, image=logo_image, bg="#050505")
            logo_label.image = logo_image
        else:
            logo_label = Label(
                splash,
                text="CORTEX",
                fg="#e5e7eb",
                bg="#050505",
                font=(self.base_font_family, 42, "bold"),
            )
        logo_label.pack(expand=True, pady=(40, 10))

        status_label = Label(
            splash,
            text="Loading your personal assistant...",
            fg="#94a3b8",
            bg="#050505",
            font=(self.base_font_family, 10),
        )
        status_label.pack(pady=(0, 16))

        splash.attributes("-alpha", 0.0)
        self.root.after(0, lambda: self._fade_splash(splash, 0.0, 1.0, 40, 0.05, hold=5000))
        self.root.wait_window(splash)
        self.root.deiconify()

    def _fade_splash(self, splash: Toplevel, alpha: float, target: float, step_ms: int, increment: float, hold: int = 0) -> None:
        if alpha < target and increment > 0:
            alpha = min(target, alpha + increment)
            splash.attributes("-alpha", alpha)
            splash.after(step_ms, lambda: self._fade_splash(splash, alpha, target, step_ms, increment, hold))
            return

        if hold > 0 and increment > 0:
            splash.after(hold, lambda: self._fade_splash(splash, alpha, 0.0, step_ms, -increment, 0))
            return

        if alpha > 0.0 and increment < 0:
            alpha = max(0.0, alpha + increment)
            splash.attributes("-alpha", alpha)
            splash.after(step_ms, lambda: self._fade_splash(splash, alpha, target, step_ms, increment, hold))
            return

        splash.destroy()

    def _update_font_size(self, value: str) -> None:
        self.font_size = int(float(value))
        self._apply_font_settings()

    def _apply_font_settings(self) -> None:
        text_font = (self.base_font_family, self.font_size)
        self.output.configure(font=text_font)
        self.input_area.configure(font=(self.base_font_family, self.font_size + 1))
        self.status_label.configure(font=(self.base_font_family, max(8, self.font_size - 2)))
        if hasattr(self, "settings_status"):
            self.settings_status.configure(font=(self.base_font_family, self.font_size))
        self._draw_starfield(self.star_canvas.winfo_width(), self.star_canvas.winfo_height())

    def run_command(self, command: str) -> None:
        result = self.brain.execute_command(command)
        if result == "__CORTEX_CLEAR_SCREEN__":
            self.output.configure(state=NORMAL)
            self.output.delete("1.0", END)
            self.output.configure(state=DISABLED)
            return
        self.append_text(result)

    def on_submit(self, event=None) -> None:
        if event and event.keysym == "Return" and event.state & 0x0001:
            return
        command = self.input_area.get("1.0", END).strip()
        if not command:
            return
        self.input_area.delete("1.0", END)
        self.run_command(command)

    def _create_nav_button(self, parent: Frame, label: str, command_text: str) -> None:
        button = Button(
            parent,
            text=label,
            command=lambda c=command_text: self._nav_command(c),
            bg="#1f2937",
            fg="#e2e8f0",
            activebackground="#2563eb",
            activeforeground="#ffffff",
            relief="flat",
            padx=16,
            pady=12,
            font=("Segoe UI Variable", 10, "bold"),
            bd=0,
            highlightthickness=0,
        )
        button.pack(fill=X, padx=16, pady=6)
        button.bind("<Enter>", lambda event, btn=button: self._on_button_hover(btn))
        button.bind("<Leave>", lambda event, btn=button: self._on_button_leave(btn))

    def _nav_command(self, command_text: str) -> None:
        if command_text.startswith("browse"):
            self._open_browser_window(command_text.replace("browse", "", 1).strip())
            return
        if command_text == "chatlogs":
            self.open_feature_panel("Chat Logs", "")
            return
        if command_text == "settings":
            self.open_feature_panel("Settings", "")
            return
        self.run_command(command_text)

    def _on_button_hover(self, button: Button) -> None:
        button.configure(bg="#2563eb")

    def _on_button_leave(self, button: Button) -> None:
        button.configure(bg="#1f2937")

    def _pulse_status_label(self) -> None:
        current = self.status_label.cget("fg")
        next_color = "#38bdf8" if current == "#94a3b8" else "#94a3b8"
        self.status_label.configure(fg=next_color)
        self.root.after(800, self._pulse_status_label)

    def _draw_starfield(self, width: int, height: int) -> None:
        self.star_canvas.delete("all")
        star_count = max(60, (width // 18) + (height // 18))
        for _ in range(star_count):
            x = random.randint(0, width)
            y = random.randint(0, height)
            size = random.randint(1, 2)
            color = random.choice(["#f8fafc", "#e2e8f0", "#cbd5e1", "#fde68a"])
            self.star_canvas.create_oval(x, y, x + size, y + size, fill=color, outline="")

    def _on_canvas_resize(self, event) -> None:
        self._draw_starfield(event.width, event.height)

    def _twinkle_stars(self) -> None:
        if self.star_canvas.winfo_exists():
            self._draw_starfield(self.star_canvas.winfo_width(), self.star_canvas.winfo_height())
            self.root.after(3200, self._twinkle_stars)

    def open_feature_panel(self, feature_name: str, initial_text: str = "") -> None:
        self.feature_name = feature_name
        self.feature_initial_text = initial_text
        self.panel_target_width = 400
        self.panel_width = 0
        if self.feature_panel is None or not self.feature_panel.winfo_exists():
            self.feature_panel = Frame(self.content_frame, bg="#071014", bd=0, relief="flat")
            self.feature_panel.place(relx=1.0, rely=0, anchor="ne", width=0, height=self.content_frame.winfo_height())

        for child in self.feature_panel.winfo_children():
            child.destroy()

        header = Label(
            self.feature_panel,
            text=f"{feature_name} Panel",
            fg="#7dd3fc",
            bg="#071014",
            font=("Segoe UI Black", 16, "bold"),
        )
        header.pack(anchor="nw", padx=16, pady=(16, 8))

        description = Label(
            self.feature_panel,
            text=f"Manage {feature_name.lower()} features from this side panel.",
            fg="#cbd5e1",
            bg="#071014",
            font=("Segoe UI", 10),
            wraplength=368,
            justify=LEFT,
        )
        description.pack(anchor="nw", padx=16)

        button_row = Frame(self.feature_panel, bg="#071014")
        button_row.pack(fill=X, padx=16, pady=(10, 10))

        close_button = Button(
            button_row,
            text="Close",
            command=self.close_feature_panel,
            bg="#334155",
            fg="#e2e8f0",
            activebackground="#475569",
            relief="flat",
            padx=12,
            pady=8,
            font=("Segoe UI Variable", 9, "bold"),
        )
        close_button.pack(side=RIGHT)

        separator = Frame(self.feature_panel, bg="#0f172a", height=2)
        separator.pack(fill=X, padx=16, pady=(0, 10))

        if feature_name == "Browser":
            self._open_browser_window(initial_text)
            self.close_feature_panel()
            return
        elif feature_name == "Chat Logs":
            self._build_chat_logs_panel()
        elif feature_name == "Settings":
            self._build_settings_panel()

    def _open_browser_window(self, initial_text: str = "") -> None:
        browser_window = Toplevel(self.root)
        browser_window.title("CORTEX Browser")
        browser_window.geometry("620x220")
        browser_window.configure(bg="#0f1720")
        browser_window.transient(self.root)

        Label(
            browser_window,
            text="Enter a URL or search query:",
            fg="#e5e7eb",
            bg="#0f1720",
            font=(self.base_font_family, 11, "bold"),
        ).pack(anchor="w", padx=16, pady=(16, 6))

        url_var = StringVar(value=initial_text or "https://example.com")
        url_entry = Entry(
            browser_window,
            textvariable=url_var,
            bg="#121826",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            relief="flat",
            bd=0,
            font=(self.base_font_family, 11),
        )
        url_entry.pack(fill=X, padx=16, pady=(0, 12))
        url_entry.focus_set()

        button_frame = Frame(browser_window, bg="#0f1720")
        button_frame.pack(fill=X, padx=16, pady=(0, 16))

        open_button = Button(
            button_frame,
            text="Open in browser",
            command=lambda: self._browse_url(url_var.get()),
            bg="#22c55e",
            fg="#ffffff",
            activebackground="#16a34a",
            relief="flat",
            padx=14,
            pady=10,
            font=(self.base_font_family, 10, "bold"),
        )
        open_button.pack(side=LEFT, expand=True, fill=X, padx=(0, 8))

        close_button = Button(
            button_frame,
            text="Close",
            command=browser_window.destroy,
            bg="#334155",
            fg="#e2e8eb",
            activebackground="#475569",
            relief="flat",
            padx=14,
            pady=10,
            font=(self.base_font_family, 10, "bold"),
        )
        close_button.pack(side=LEFT, expand=True, fill=X)

        help_label = Label(
            browser_window,
            text="This opens a lightweight browser window and launches the page in your system browser.",
            fg="#94a3b8",
            bg="#0f1720",
            font=(self.base_font_family, 10),
            wraplength=580,
            justify=LEFT,
        )
        help_label.pack(anchor="w", padx=16)

    def _browse_url(self, query: str) -> None:
        target = query.strip()
        if not target:
            self.append_text("Please enter an address or search term.")
            return
        if not target.startswith("http://") and not target.startswith("https://"):
            target = f"https://www.google.com/search?q={quote_plus(target)}"
        try:
            webbrowser.open_new(target)
            self.append_text(f"Opened browser for: {target}")
        except Exception as exc:
            self.append_text(f"Unable to open browser: {exc}")

    def _forget_key(self, key: str) -> None:
        if not key:
            return
        self.brain.memory.forget(key)
        self.open_feature_panel("Chat Logs")


    def _build_chat_logs_panel(self) -> None:
        info_label = Label(
            self.feature_panel,
            text="Chat Log Manager",
            fg="#7dd3fc",
            bg="#071014",
            font=("Segoe UI Black", 14, "bold"),
        )
        info_label.pack(anchor="nw", padx=16, pady=(4, 6))

        instructions = Label(
            self.feature_panel,
            text=(
                "Create, open, and save named chat sessions. "
                "The session data is persisted locally in data/chat_logs.json."
            ),
            fg="#cbd5e1",
            bg="#071014",
            font=("Segoe UI Variable", 10),
            wraplength=360,
            justify=LEFT,
        )
        instructions.pack(anchor="nw", padx=16, pady=(0, 10))

        session_label = Label(
            self.feature_panel,
            text="Session name:",
            fg="#cbd5e1",
            bg="#071014",
            font=("Segoe UI Variable", 10),
        )
        session_label.pack(anchor="nw", padx=16, pady=(0, 4))

        self.chat_session_name_var = StringVar()
        session_entry = Entry(
            self.feature_panel,
            textvariable=self.chat_session_name_var,
            bg="#0f172a",
            fg="#e2e8f0",
            insertbackground="#e2e8f0",
            relief="flat",
            bd=0,
            font=("Segoe UI Variable", 10),
        )
        session_entry.pack(fill=X, padx=16, pady=(0, 10))

        button_row = Frame(self.feature_panel, bg="#071014")
        button_row.pack(fill=X, padx=16, pady=(0, 10))

        create_button = Button(
            button_row,
            text="New Session",
            command=self._create_chat_session,
            bg="#22c55e",
            fg="#ffffff",
            activebackground="#16a34a",
            relief="flat",
            padx=12,
            pady=10,
            font=("Segoe UI Variable", 10, "bold"),
        )
        create_button.pack(side=LEFT, expand=True, fill=X, padx=4)

        open_button = Button(
            button_row,
            text="Open Session",
            command=self._open_chat_session,
            bg="#2563eb",
            fg="#ffffff",
            activebackground="#1d4ed8",
            relief="flat",
            padx=12,
            pady=10,
            font=("Segoe UI Variable", 10, "bold"),
        )
        open_button.pack(side=LEFT, expand=True, fill=X, padx=4)

        save_button = Button(
            button_row,
            text="Save Session",
            command=self._save_chat_session,
            bg="#f97316",
            fg="#ffffff",
            activebackground="#ea580c",
            relief="flat",
            padx=12,
            pady=10,
            font=("Segoe UI Variable", 10, "bold"),
        )
        save_button.pack(side=LEFT, expand=True, fill=X, padx=4)

        self.chat_logs_status = Label(
            self.feature_panel,
            text="No active session.",
            fg="#94a3b8",
            bg="#071014",
            font=("Segoe UI Variable", 10),
            wraplength=360,
            justify=LEFT,
        )
        self.chat_logs_status.pack(anchor="nw", padx=16, pady=(0, 10))

        sessions_label = Label(
            self.feature_panel,
            text="Saved sessions:",
            fg="#cbd5e1",
            bg="#071014",
            font=("Segoe UI Variable", 10),
        )
        sessions_label.pack(anchor="nw", padx=16, pady=(0, 4))

        self.chat_logs_list = Text(
            self.feature_panel,
            wrap="word",
            state=DISABLED,
            height=6,
            bg="#020617",
            fg="#e2e8f0",
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=14,
            font=("Segoe UI Variable", 10),
        )
        self.chat_logs_list.pack(fill=X, padx=16, pady=(0, 10))

        self.chat_logs_output = Text(
            self.feature_panel,
            wrap="word",
            state=DISABLED,
            height=8,
            bg="#020617",
            fg="#e2e8f0",
            relief="flat",
            bd=0,
            highlightthickness=0,
            padx=14,
            pady=14,
            font=("Segoe UI Variable", 10),
        )
        self.chat_logs_output.pack(fill=BOTH, expand=True, padx=16, pady=(0, 16))
        self._refresh_chat_logs_panel()

    def _refresh_chat_logs_panel(self) -> None:
        sessions = self.brain.chat_logs.list_sessions()
        self.chat_logs_list.configure(state=NORMAL)
        self.chat_logs_list.delete("1.0", END)
        self.chat_logs_list.insert(END, "\n".join(sessions) if sessions else "No chat sessions yet.")
        self.chat_logs_list.configure(state=DISABLED)
        active = self.brain.active_chat_session or "None"
        self.chat_logs_status.configure(text=f"Active session: {active}")
        if active != "None":
            self._refresh_chat_logs_history(active)

    def _refresh_chat_logs_history(self, session_name: str) -> None:
        messages = self.brain.chat_logs.get_session_messages(session_name)
        self.chat_logs_output.configure(state=NORMAL)
        self.chat_logs_output.delete("1.0", END)
        if not messages:
            self.chat_logs_output.insert(END, "No messages yet in this session.")
        else:
            for msg in messages:
                self.chat_logs_output.insert(
                    END,
                    f"[{msg['timestamp']}] {msg['sender']}: {msg['text']}\n"
                )
        self.chat_logs_output.configure(state=DISABLED)

    def _create_chat_session(self) -> None:
        name = self.chat_session_name_var.get().strip() or f"Chat Session {len(self.brain.chat_logs.sessions) + 1}"
        result = self.brain.execute_command(f"chatlogs new {name}")
        self._set_chat_logs_output(result)
        self._refresh_chat_logs_panel()

    def _open_chat_session(self) -> None:
        name = self.chat_session_name_var.get().strip()
        if not name:
            self._set_chat_logs_output("Enter a session name to open.")
            return
        result = self.brain.execute_command(f"chatlogs open {name}")
        self._set_chat_logs_output(result)
        self._refresh_chat_logs_panel()

    def _save_chat_session(self) -> None:
        name = self.chat_session_name_var.get().strip() or self.brain.active_chat_session
        if not name:
            self._set_chat_logs_output("No active chat session to save.")
            return
        path = filedialog.asksaveasfilename(
            title="Save chat session",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt")],
            initialfile=f"{name}.txt",
        )
        if not path:
            return
        self.brain.chat_logs.save_session_to_file(name, path)
        self._set_chat_logs_output(f"Saved session '{name}' to {path}")

    def _set_chat_logs_output(self, text: str) -> None:
        self.chat_logs_output.configure(state=NORMAL)
        self.chat_logs_output.delete("1.0", END)
        self.chat_logs_output.insert(END, text)
        self.chat_logs_output.configure(state=DISABLED)

    def _set_panel_text(self, widget: Text, text: str) -> None:
        widget.configure(state=NORMAL)
        widget.delete("1.0", END)
        widget.insert(END, text)
        widget.configure(state=DISABLED)

    def _ensure_user_name(self) -> None:
        if self.user_name.strip():
            return
        name = simpledialog.askstring("Welcome to CORTEX", "What is your name?", parent=self.root)
        if name and name.strip():
            self.user_name = name.strip()
            self.brain.memory.set_user_name(self.user_name)
            self.append_text(f"Hello, {self.user_name}! Nice to meet you.")
        else:
            self.user_name = "User"
            self.brain.memory.set_user_name(self.user_name)
            self.append_text("Hello! I will call you User.")

    def _update_clock(self) -> None:
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if hasattr(self, "status_label"):
            self.status_label.configure(
                text=f"{now}  |  Modern interface active — welcome to the improved CORTEX experience."
            )
        self.root.after(1000, self._update_clock)

    def _animate_panel(self) -> None:
        if self.feature_panel and self.panel_target_width > 0:
            if self.panel_width < self.panel_target_width:
                self.panel_width = min(self.panel_width + 20, self.panel_target_width)
                self.feature_panel.place_configure(width=self.panel_width, height=self.content_frame.winfo_height())
                self.feature_panel.lift()
        elif self.feature_panel and self.panel_target_width == 0:
            if self.panel_width > 0:
                self.panel_width = max(self.panel_width - 20, 0)
                self.feature_panel.place_configure(width=self.panel_width, height=self.content_frame.winfo_height())
                if self.panel_width == 0:
                    self.feature_panel.place_forget()
        self.root.after(15, self._animate_panel)

    def close_feature_panel(self) -> None:
        self.panel_target_width = 0

    def run(self) -> None:
        self.root.mainloop()


def main() -> None:
    brain = CortexBrain()
    brain.start()

    if len(sys.argv) > 1:
        if sys.argv[1].lower() in ("repl", "cli"):
            repl(brain)
            return
        command = " ".join(arg.strip() for arg in sys.argv[1:] if arg.strip())
        result = brain.execute_command(command)
        if result == "__CORTEX_CLEAR_SCREEN__":
            os.system("cls" if os.name == "nt" else "clear")
            return
        print(result)
        return

    gui = CortexGUI(brain)
    gui.run()


if __name__ == "__main__":
    main()
