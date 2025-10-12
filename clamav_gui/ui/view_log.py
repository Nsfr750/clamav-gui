"""
Log viewer dialog to browse and view application log files.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import List

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QPushButton,
    QTextEdit,
    QFileDialog,
    QMessageBox,
    QWidget,
    QLabel,
)

from clamav_gui.utils.logger import get_log_files


class LogViewerDialog(QDialog):
    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self.setWindowTitle("Log Viewer")
        self.resize(800, 600)
        self._setup_ui()
        self._populate_logs()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        top = QHBoxLayout()
        self.refresh_btn = QPushButton("Refresh")
        self.open_dir_btn = QPushButton("Open Logs Folder")
        self.export_btn = QPushButton("Export Selected")
        top.addWidget(self.refresh_btn)
        top.addWidget(self.open_dir_btn)
        top.addWidget(self.export_btn)
        top.addStretch(1)

        self.refresh_btn.clicked.connect(self._populate_logs)
        self.open_dir_btn.clicked.connect(self._open_logs_folder)
        self.export_btn.clicked.connect(self._export_selected)

        layout.addLayout(top)

        middle = QHBoxLayout()
        self.log_list = QListWidget()
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_list.currentRowChanged.connect(self._load_selected)
        middle.addWidget(self.log_list, 1)
        middle.addWidget(self.log_view, 2)

        layout.addLayout(middle)

        bottom = QHBoxLayout()
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        bottom.addStretch(1)
        bottom.addWidget(self.close_btn)
        layout.addLayout(bottom)

    def _populate_logs(self) -> None:
        self.log_list.clear()
        files = get_log_files()
        for p in files:
            self.log_list.addItem(p.name)
        if files:
            self.log_list.setCurrentRow(0)
        else:
            self.log_view.setPlainText("No log files found.")

    def _load_selected(self, row: int) -> None:
        files = get_log_files()
        if 0 <= row < len(files):
            path = files[row]
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except Exception as e:
                text = f"Failed to read log file: {e}"
            self.log_view.setPlainText(text)
        else:
            self.log_view.clear()

    def _open_logs_folder(self) -> None:
        # Open the logs folder in the system file explorer
        files = get_log_files()
        target_dir = files[0].parent if files else Path.cwd()
        try:
            os.startfile(str(target_dir))  # Windows
        except Exception:
            # Cross-platform fallback: show info
            QMessageBox.information(self, "Logs", f"Logs folder: {target_dir}")

    def _export_selected(self) -> None:
        files = get_log_files()
        index = self.log_list.currentRow()
        if 0 <= index < len(files):
            src = files[index]
            target, _ = QFileDialog.getSaveFileName(self, "Export Log As", src.name, "Log Files (*.log);;All Files (*.*)")
            if target:
                try:
                    Path(target).write_text(src.read_text(encoding="utf-8", errors="replace"), encoding="utf-8")
                    QMessageBox.information(self, "Export", f"Exported to {target}")
                except Exception as e:
                    QMessageBox.critical(self, "Export Failed", str(e))
        else:
            QMessageBox.information(self, "Export", "No log selected.")
