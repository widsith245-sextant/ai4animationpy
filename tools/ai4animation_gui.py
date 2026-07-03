"""Tk launcher for the local SOMA and UE verification workflows."""

from __future__ import annotations

import subprocess
import threading
import tkinter as tk
from pathlib import Path
from tkinter import scrolledtext


REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "scripts"
DEFAULT_PROJECT = r"D:\PCG_ANIM_RL\NNE_T"

COMMANDS = [
    ("Export SOMA GLB", "export_soma_test_animation_glb.bat", False),
    ("Import SOMA To NNE_T", "import_soma_test_animation_into_nne_t.bat", True),
    ("Retarget SOMA To Manny", "retarget_soma_to_manny_in_nne_t.bat", True),
    ("Validate SOMA -> Manny", "test_soma_to_nne_t.bat", True),
    ("Run SOMA Motion Editor", "run_soma_motion_editor.bat", False),
    ("Run Cranberry Motion Editor", "run_cranberry_motion_editor.bat", False),
]


class Launcher(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("AI4AnimationPy Validation Launcher")
        self.geometry("960x640")

        header = tk.Label(
            self,
            text="AI4AnimationPy / UE Validation Launcher",
            font=("Microsoft YaHei UI", 16, "bold"),
            anchor="w",
        )
        header.pack(fill="x", padx=16, pady=(16, 8))

        subheader = tk.Label(
            self,
            text=(
                "Run the SOMA export, UE import, retarget, and local motion editor "
                "verification workflows from one place."
            ),
            anchor="w",
            justify="left",
        )
        subheader.pack(fill="x", padx=16, pady=(0, 12))

        project_row = tk.Frame(self)
        project_row.pack(fill="x", padx=16, pady=(0, 12))

        project_label = tk.Label(project_row, text="UE Project", width=12, anchor="w")
        project_label.pack(side="left")

        self.project_var = tk.StringVar(value=DEFAULT_PROJECT)
        project_entry = tk.Entry(project_row, textvariable=self.project_var)
        project_entry.pack(side="left", fill="x", expand=True)

        button_frame = tk.Frame(self)
        button_frame.pack(fill="x", padx=16)

        for index, (label, script_name, needs_project) in enumerate(COMMANDS):
            button = tk.Button(
                button_frame,
                text=label,
                width=28,
                command=lambda value=script_name, project_arg=needs_project: self.run_script(
                    value,
                    include_project_arg=project_arg,
                ),
            )
            button.grid(row=index // 2, column=index % 2, padx=6, pady=6, sticky="ew")

        for column in range(2):
            button_frame.grid_columnconfigure(column, weight=1)

        self.log = scrolledtext.ScrolledText(self, wrap="word", font=("Consolas", 10))
        self.log.pack(fill="both", expand=True, padx=16, pady=16)
        self._append(f"Repo root: {REPO_ROOT}")
        self._append(f"Target UE project: {self.project_var.get()}")

    def _append(self, text: str) -> None:
        self.log.insert("end", text + "\n")
        self.log.see("end")

    def run_script(self, script_name: str, *, include_project_arg: bool) -> None:
        script_path = SCRIPTS_DIR / script_name
        if not script_path.exists():
            self._append(f"[missing] {script_path}")
            return

        args = ["cmd.exe", "/c", str(script_path)]
        if include_project_arg:
            args.append(self.project_var.get().strip() or DEFAULT_PROJECT)

        self._append(f"[run] {' '.join(args[2:])}")
        thread = threading.Thread(target=self._run_worker, args=(args,), daemon=True)
        thread.start()

    def _run_worker(self, args: list[str]) -> None:
        process = subprocess.Popen(
            args,
            cwd=REPO_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        assert process.stdout is not None
        for line in process.stdout:
            self.after(0, self._append, line.rstrip())

        return_code = process.wait()
        command_name = Path(args[2]).name
        self.after(0, self._append, f"[exit] {command_name} -> {return_code}")


if __name__ == "__main__":
    Launcher().mainloop()
