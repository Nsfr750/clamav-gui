"""
A minimal, reliable main UI window that ensures the menu bar and UI are visible.
"""
from __future__ import annotations

import logging
import os
from PySide6.QtWidgets import (
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QTabWidget,
    QGroupBox,
    QFormLayout,
    QLineEdit,
    QCheckBox,
    QPushButton,
    QTextEdit,
    QProgressBar,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QAbstractItemView,
)
from PySide6.QtCore import Qt
from PySide6.QtCore import QProcess

from clamav_gui.ui.menu import ClamAVMenuBar
from clamav_gui.ui.settings import AppSettings
from clamav_gui.ui.updates_ui import check_for_updates
from clamav_gui import __version__
from clamav_gui.utils.quarantine_manager import QuarantineManager

logger = logging.getLogger(__name__)


class MainUIWindow(QMainWindow):
    def __init__(self, lang_manager=None, parent=None):
        super().__init__(parent)
        self.lang_manager = lang_manager
        self.setWindowTitle("ClamAV GUI")
        self.resize(960, 720)

        # Ensure standard window flags (menus visible)
        self.setWindowFlags(
            Qt.Window
            | Qt.WindowMinimizeButtonHint
            | Qt.WindowMaximizeButtonHint
            | Qt.WindowCloseButtonHint
        )

        # Menu bar
        self.menu_bar = ClamAVMenuBar(self)
        self.setMenuBar(self.menu_bar)
        if hasattr(self.menu_bar, "set_language_manager") and self.lang_manager is not None:
            self.menu_bar.set_language_manager(self.lang_manager)

        # Central UI (simple tabs to validate rendering)
        central = QWidget(self)
        layout = QVBoxLayout(central)
        self.tabs = QTabWidget()

        # Tab 0: Scan (UI only, stubbed handlers)
        scan_tab = self._create_scan_tab()
        self.tabs.addTab(scan_tab, "Scan")

        # Tab 1: Email Scan (UI only, stubbed handlers)
        email_tab = self._create_email_scan_tab()
        self.tabs.addTab(email_tab, "Email Scan")

        # Tab 2: Home
        home = QWidget()
        home_layout = QVBoxLayout(home)
        home_layout.addWidget(QLabel("Welcome to ClamAV GUI"))
        self.tabs.addTab(home, "Home")

        # Tab 3: Status
        status = QWidget()
        status_layout = QVBoxLayout(status)
        status_layout.addWidget(QLabel("Status: Ready"))
        self.tabs.addTab(status, "Status")

        # Tab 4: Update
        update_tab = self._create_update_tab()
        self.tabs.addTab(update_tab, "Update")

        # Tab 5: Virus DB Update
        virus_db_tab = self._create_virus_db_tab()
        self.tabs.addTab(virus_db_tab, "Virus DB")

        # Tab 6: Quarantine (UI only)
        quarantine_tab = self._create_quarantine_tab()
        self.tabs.addTab(quarantine_tab, "Quarantine")

        # Tab 7: Config Editor (UI only)
        config_tab = self._create_config_editor_tab()
        self.tabs.addTab(config_tab, "Config Editor")

        # Tab 8: Settings (ported minimally)
        settings_tab = self._create_settings_tab()
        self.tabs.addTab(settings_tab, "Settings")

        layout.addWidget(self.tabs)
        self.setCentralWidget(central)

        # Status bar at bottom
        self.status = self.statusBar()
        try:
            self.status.showMessage("Ready")
        except Exception:
            pass

        # Diagnostics
        try:
            mb = self.menuBar()
            logger.info(
                f"[MainUIWindow] menu_bar exists={mb is not None}, actions={len(mb.actions()) if mb else 0}"
            )
        except Exception as e:
            logger.warning(f"[MainUIWindow] menu diagnostics failed: {e}")
        
        # Scan process state
        self.scan_process: QProcess | None = None

        # Quarantine manager
        self.quarantine_manager = QuarantineManager()

        # Virus DB update process state
        self.db_process: QProcess | None = None

    def set_status(self, message: str, timeout_ms: int = 3000) -> None:
        try:
            self.status.showMessage(message, timeout_ms)
        except Exception:
            pass

    # --- Settings tab (ported) ---
    def _create_settings_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        self.settings = AppSettings()

        path_group = QGroupBox("ClamAV Paths")
        path_form = QFormLayout()
        self.clamd_path = QLineEdit()
        self.freshclam_path = QLineEdit()
        self.clamscan_path = QLineEdit()
        self.db_dir_path = QLineEdit()
        self.db_dir_path.setPlaceholderText(r"e.g. C:\\ProgramData\\ClamAV\\db or a writable folder")
        path_form.addRow("ClamD Path:", self.clamd_path)
        path_form.addRow("FreshClam Path:", self.freshclam_path)
        path_form.addRow("ClamScan Path:", self.clamscan_path)
        path_form.addRow("Virus DB Directory:", self.db_dir_path)
        path_group.setLayout(path_form)

        scan_group = QGroupBox("Scan Settings")
        scan_v = QVBoxLayout()
        basic = QGroupBox("Basic Options")
        basic_v = QVBoxLayout()
        self.scan_archives = QCheckBox("Scan archives (zip, rar, etc.)")
        self.scan_archives.setChecked(True)
        self.scan_heuristics = QCheckBox("Enable heuristic analysis")
        self.scan_heuristics.setChecked(True)
        self.scan_pua = QCheckBox("Scan potentially unwanted applications")
        self.scan_pua.setChecked(False)
        self.enable_quarantine = QCheckBox("Auto-quarantine infected files")
        self.enable_quarantine.setChecked(True)
        basic_v.addWidget(self.scan_archives)
        basic_v.addWidget(self.scan_heuristics)
        basic_v.addWidget(self.scan_pua)
        basic_v.addWidget(self.enable_quarantine)
        basic.setLayout(basic_v)
        scan_v.addWidget(basic)
        scan_group.setLayout(scan_v)

        save_btn = QPushButton("Save Settings")
        save_btn.clicked.connect(self._save_settings)

        v.addWidget(path_group)
        v.addWidget(scan_group)
        v.addStretch(1)
        v.addWidget(save_btn)

        # Load and apply existing settings if available
        try:
            self.current_settings = self.settings.load_settings() or {}
            self._apply_settings()
        except Exception:
            self.current_settings = {}

        return tab

    # --- Email Scan tab (UI only with stub handlers) ---
    def _create_email_scan_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        # Email file selection list
        email_group = QGroupBox("Email Files to Scan")
        eg_v = QVBoxLayout(email_group)
        self.email_files_list = QListWidget()
        self.email_files_list.setSelectionMode(QAbstractItemView.MultiSelection)
        self.email_files_list.setMaximumHeight(150)
        eg_v.addWidget(self.email_files_list)

        # Buttons for file management
        file_btns = QHBoxLayout()
        add_file_btn = QPushButton("Add Email File")
        add_file_btn.clicked.connect(self._add_email_file)
        remove_file_btn = QPushButton("Remove Selected")
        remove_file_btn.clicked.connect(self._remove_email_file)
        clear_files_btn = QPushButton("Clear All")
        clear_files_btn.clicked.connect(self._clear_email_files)
        file_btns.addWidget(add_file_btn)
        file_btns.addWidget(remove_file_btn)
        file_btns.addWidget(clear_files_btn)
        eg_v.addLayout(file_btns)

        # Options
        options_group = QGroupBox("Scan Options")
        og_v = QVBoxLayout(options_group)
        self.scan_email_attachments = QCheckBox("Scan email attachments")
        self.scan_email_attachments.setChecked(True)
        self.scan_email_content = QCheckBox("Scan email content for suspicious patterns")
        self.scan_email_content.setChecked(True)
        og_v.addWidget(self.scan_email_attachments)
        og_v.addWidget(self.scan_email_content)

        # Output
        output_group = QGroupBox("Scan Output")
        out_v = QVBoxLayout(output_group)
        self.email_output = QTextEdit()
        self.email_output.setReadOnly(True)
        out_v.addWidget(self.email_output)

        # Progress
        self.email_progress = QProgressBar()

        # Buttons
        btns = QHBoxLayout()
        self.start_email_scan_btn = QPushButton("Start Email Scan")
        self.start_email_scan_btn.clicked.connect(self._start_email_scan)
        self.stop_email_scan_btn = QPushButton("Stop")
        self.stop_email_scan_btn.setEnabled(False)
        self.stop_email_scan_btn.clicked.connect(self._stop_email_scan)
        self.save_email_report_btn = QPushButton("Save Report")
        self.save_email_report_btn.setEnabled(False)
        self.save_email_report_btn.clicked.connect(self._save_email_report)
        btns.addWidget(self.start_email_scan_btn)
        btns.addWidget(self.stop_email_scan_btn)
        btns.addWidget(self.save_email_report_btn)

        # Compose
        v.addWidget(email_group)
        v.addWidget(options_group)
        v.addWidget(output_group)
        v.addWidget(self.email_progress)
        v.addLayout(btns)

        return tab

    # Email scan handlers (stubs)
    def _add_email_file(self) -> None:
        paths, _ = QFileDialog.getOpenFileNames(self, "Add Email Files", "", "Email Files (*.eml *.msg);;All Files (*.*)")
        for p in paths:
            self.email_files_list.addItem(p)

    def _remove_email_file(self) -> None:
        for item in self.email_files_list.selectedItems():
            self.email_files_list.takeItem(self.email_files_list.row(item))

    def _clear_email_files(self) -> None:
        self.email_files_list.clear()

    def _start_email_scan(self) -> None:
        count = self.email_files_list.count()
        if count == 0:
            self.email_output.append("Please add at least one email file.")
            return
        files = [self.email_files_list.item(i).text() for i in range(count)]
        self.email_output.append(f"Starting email scan on {len(files)} files...")
        self.email_progress.setRange(0, 0)
        self.start_email_scan_btn.setEnabled(False)
        self.stop_email_scan_btn.setEnabled(True)
        self.save_email_report_btn.setEnabled(False)

    def _stop_email_scan(self) -> None:
        self.email_progress.setRange(0, 1)
        self.email_progress.setValue(0)
        self.email_output.append("Email scan stopped.")
        self.start_email_scan_btn.setEnabled(True)
        self.stop_email_scan_btn.setEnabled(False)
        self.save_email_report_btn.setEnabled(True)

    def _save_email_report(self) -> None:
        text = self.email_output.toPlainText()
        if not text:
            self.email_output.append("Nothing to save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Email Scan Report", "email_scan_report.txt", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.email_output.append(f"Report saved to: {path}")
            except Exception as e:
                self.email_output.append(f"Failed to save report: {e}")

    # --- Quarantine tab (UI only with stub handlers) ---
    def _create_quarantine_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        # Stats
        stats_group = QGroupBox("Quarantine Statistics")
        sg_v = QVBoxLayout(stats_group)
        self.quarantine_stats_text = QTextEdit()
        self.quarantine_stats_text.setReadOnly(True)
        self.quarantine_stats_text.setMaximumHeight(150)
        sg_v.addWidget(self.quarantine_stats_text)
        refresh_btn = QPushButton("Refresh Stats")
        refresh_btn.clicked.connect(self._refresh_quarantine_stats)
        sg_v.addWidget(refresh_btn)

        # Files list
        files_group = QGroupBox("Quarantined Files")
        fg_v = QVBoxLayout(files_group)
        self.quarantine_files_list = QListWidget()
        self.quarantine_files_list.setSelectionMode(QAbstractItemView.MultiSelection)
        fg_v.addWidget(self.quarantine_files_list)

        # File management buttons
        actions = QHBoxLayout()
        restore_btn = QPushButton("Restore Selected")
        delete_btn = QPushButton("Delete Selected")
        restore_btn.clicked.connect(self._restore_selected_files)
        delete_btn.clicked.connect(self._delete_selected_files)
        actions.addWidget(restore_btn)
        actions.addWidget(delete_btn)

        # Bulk operations
        bulk = QHBoxLayout()
        restore_all_btn = QPushButton("Restore All")
        delete_all_btn = QPushButton("Delete All")
        cleanup_btn = QPushButton("Cleanup (30+ days)")
        restore_all_btn.clicked.connect(self._restore_all_files)
        delete_all_btn.clicked.connect(self._delete_all_files)
        cleanup_btn.clicked.connect(self._cleanup_old_files)
        bulk.addWidget(restore_all_btn)
        bulk.addWidget(delete_all_btn)
        bulk.addWidget(cleanup_btn)

        export_btn = QPushButton("Export List")
        export_btn.clicked.connect(self._export_quarantine_list)

        # Compose
        v.addWidget(stats_group)
        v.addWidget(files_group)
        v.addLayout(actions)
        v.addLayout(bulk)
        v.addWidget(export_btn)

        # Initial fill
        self._refresh_quarantine_stats()
        self._refresh_quarantine_files()

        return tab

    # Quarantine handlers (real)
    def _refresh_quarantine_stats(self) -> None:
        try:
            stats = self.quarantine_manager.get_quarantine_stats()
            text = (
                "Quarantine Statistics:\n====================\n\n"
                f"Total quarantined files: {stats.get('total_quarantined', 0)}\n"
                f"Total size: {stats.get('total_size_mb', 0):.2f} MB\n\n"
                "Threat types found:\n"
            )
            threats = stats.get('threat_types') or []
            if threats:
                text += "\n".join(f"  • {t}" for t in threats)
            else:
                text += "  None"
            text += (
                "\n\nLast activity:\n"
                f"  Newest file: {stats.get('newest_file') or 'N/A'}\n"
                f"  Oldest file: {stats.get('oldest_file') or 'N/A'}"
            )
            self.quarantine_stats_text.setPlainText(text)
        except Exception as e:
            self.quarantine_stats_text.setPlainText(f"Error loading quarantine statistics: {e}")

    def _refresh_quarantine_files(self) -> None:
        try:
            self.quarantine_files_list.clear()
            files = self.quarantine_manager.list_quarantined_files()
            if not files:
                self.quarantine_files_list.addItem("No quarantined files")
                return
            for info in files:
                filename = info.get('original_filename', 'Unknown')
                threat = info.get('threat_name', 'Unknown')
                size = info.get('file_size', 0)
                item_text = f"{filename} - {threat} ({size} bytes)"
                item = QListWidgetItem(item_text)
                item.setData(Qt.UserRole, info)
                self.quarantine_files_list.addItem(item)
        except Exception as e:
            self.quarantine_files_list.clear()
            self.quarantine_files_list.addItem(f"Error loading quarantined files: {e}")

    def _get_selected_file_ids(self) -> list[str]:
        ids: list[str] = []
        for item in self.quarantine_files_list.selectedItems():
            info = item.data(Qt.UserRole) or {}
            # Determine file_id from metadata
            file_id = info.get('file_hash') and f"{info.get('file_hash')}_{info.get('quarantine_time','')}"
            if not file_id and 'quarantined_path' in info:
                # Extract timestamp_hash_filename format
                basename = info['quarantined_path'].split(os.sep)[-1]
                parts = basename.split('_', 2)
                if len(parts) >= 2:
                    file_id = f"{parts[1]}_{parts[0]}"
            if file_id:
                ids.append(file_id)
        return ids

    def _restore_selected_files(self) -> None:
        ids = self._get_selected_file_ids()
        if not ids:
            self._append_quarantine_msg("No files selected to restore.")
            return
        for fid in ids:
            ok, msg = self.quarantine_manager.restore_file(fid)
            self._append_quarantine_msg(msg)
        self._refresh_quarantine_files()
        self._refresh_quarantine_stats()

    def _delete_selected_files(self) -> None:
        ids = self._get_selected_file_ids()
        if not ids:
            self._append_quarantine_msg("No files selected to delete.")
            return
        for fid in ids:
            ok, msg = self.quarantine_manager.delete_quarantined_file(fid)
            self._append_quarantine_msg(msg)
        self._refresh_quarantine_files()
        self._refresh_quarantine_stats()

    def _restore_all_files(self) -> None:
        # Restore all listed files
        count = self.quarantine_files_list.count()
        restored = 0
        for i in range(count):
            item = self.quarantine_files_list.item(i)
            info = item.data(Qt.UserRole) or {}
            if not info:
                continue
            file_id = info.get('file_hash') and f"{info.get('file_hash')}_{info.get('quarantine_time','')}"
            if not file_id and 'quarantined_path' in info:
                basename = info['quarantined_path'].split(os.sep)[-1]
                parts = basename.split('_', 2)
                if len(parts) >= 2:
                    file_id = f"{parts[1]}_{parts[0]}"
            if file_id:
                ok, msg = self.quarantine_manager.restore_file(file_id)
                self._append_quarantine_msg(msg)
                if ok:
                    restored += 1
        self._append_quarantine_msg(f"Restored {restored} files.")
        self._refresh_quarantine_files()
        self._refresh_quarantine_stats()

    def _delete_all_files(self) -> None:
        count = self.quarantine_files_list.count()
        deleted = 0
        for i in range(count):
            item = self.quarantine_files_list.item(i)
            info = item.data(Qt.UserRole) or {}
            if not info:
                continue
            file_id = info.get('file_hash') and f"{info.get('file_hash')}_{info.get('quarantine_time','')}"
            if not file_id and 'quarantined_path' in info:
                basename = info['quarantined_path'].split(os.sep)[-1]
                parts = basename.split('_', 2)
                if len(parts) >= 2:
                    file_id = f"{parts[1]}_{parts[0]}"
            if file_id:
                ok, msg = self.quarantine_manager.delete_quarantined_file(file_id)
                self._append_quarantine_msg(msg)
                if ok:
                    deleted += 1
        self._append_quarantine_msg(f"Deleted {deleted} files.")
        self._refresh_quarantine_files()
        self._refresh_quarantine_stats()

    def _cleanup_old_files(self) -> None:
        try:
            count, msg = self.quarantine_manager.cleanup_old_files(days_old=30)
            self._append_quarantine_msg(msg)
        except Exception as e:
            self._append_quarantine_msg(f"Cleanup failed: {e}")
        self._refresh_quarantine_files()
        self._refresh_quarantine_stats()

    def _export_quarantine_list(self) -> None:
        path, _ = QFileDialog.getSaveFileName(self, "Export Quarantine List", "quarantine_list.json", "JSON Files (*.json);;All Files (*.*)")
        if path:
            try:
                ok = self.quarantine_manager.export_quarantine_list(path)
                if ok:
                    self._append_quarantine_msg(f"Exported list to: {path}")
                else:
                    self._append_quarantine_msg("Failed to export list.")
            except Exception as e:
                self._append_quarantine_msg(f"Failed to export list: {e}")

    def _append_quarantine_msg(self, msg: str) -> None:
        # Append into status text area to keep it simple for stubs
        self.quarantine_stats_text.append(f"\n{msg}")

    # --- Config Editor tab (UI only) ---
    def _create_config_editor_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)
        toolbar = QHBoxLayout()
        open_btn = QPushButton("Open Config...")
        save_btn = QPushButton("Save Config")
        toolbar.addWidget(open_btn)
        toolbar.addWidget(save_btn)
        toolbar.addStretch(1)
        self.config_path_edit = QLineEdit()
        self.config_path_edit.setPlaceholderText("No file selected")
        self.config_editor = QTextEdit()
        self.config_editor.setPlaceholderText("Configuration content will appear here...")

        open_btn.clicked.connect(self._open_config_file)
        save_btn.clicked.connect(self._save_config_file)

        v.addLayout(toolbar)
        v.addWidget(QLabel("Config file path:"))
        v.addWidget(self.config_path_edit)
        v.addWidget(self.config_editor)
        return tab

    def _open_config_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Open Config File", "", "Config Files (*.conf *.cfg *.ini *.yaml *.yml *.toml);;All Files (*.*)")
        if path:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    self.config_editor.setPlainText(f.read())
                self.config_path_edit.setText(path)
            except Exception as e:
                self.config_editor.setPlainText(f"Failed to open file: {e}")

    def _save_config_file(self) -> None:
        path = self.config_path_edit.text().strip()
        if not path:
            path, _ = QFileDialog.getSaveFileName(self, "Save Config File", "config.conf", "Config Files (*.conf *.cfg *.ini *.yaml *.yml *.toml);;All Files (*.*)")
            if not path:
                return
            self.config_path_edit.setText(path)
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(self.config_editor.toPlainText())
        except Exception as e:
            self.config_editor.append(f"\nFailed to save file: {e}")
    # --- Update tab ---
    def _create_update_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)
        info = QLabel("Check for updates to ClamAV GUI")
        self.update_output = QTextEdit()
        self.update_output.setReadOnly(True)
        btns = QHBoxLayout()
        check_btn = QPushButton("Check for Updates")
        check_btn.clicked.connect(self._do_check_updates)
        btns.addWidget(check_btn)
        btns.addStretch(1)
        v.addWidget(info)
        v.addLayout(btns)
        v.addWidget(self.update_output)
        return tab

    def _do_check_updates(self) -> None:
        try:
            self.update_output.append("Checking for updates...")
            # Use existing helper; it will handle dialogs/logging, but we also append a line here
            check_for_updates(parent=self, current_version=__version__, force_check=True)
            self.update_output.append("Update check completed.")
        except Exception as e:
            self.update_output.append(f"Failed to check updates: {e}")

    # --- Virus DB tab ---
    def _create_virus_db_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)
        info = QLabel("Update ClamAV virus definitions using freshclam")
        self.db_output = QTextEdit()
        self.db_output.setReadOnly(True)
        self.db_progress = QProgressBar()
        btns = QHBoxLayout()
        start_btn = QPushButton("Update Virus DB")
        stop_btn = QPushButton("Stop")
        stop_btn.setEnabled(False)
        start_btn.clicked.connect(self._start_db_update)
        stop_btn.clicked.connect(self._stop_db_update)
        self.db_start_btn = start_btn
        self.db_stop_btn = stop_btn
        btns.addWidget(start_btn)
        btns.addWidget(stop_btn)
        btns.addStretch(1)
        v.addWidget(info)
        v.addLayout(btns)
        v.addWidget(self.db_output)
        v.addWidget(self.db_progress)
        return tab

    def _start_db_update(self) -> None:
        # Resolve freshclam path from settings; fallback to 'freshclam'
        try:
            if not hasattr(self, "current_settings"):
                self.current_settings = self.settings.load_settings() or {}
        except Exception:
            self.current_settings = {}
        freshclam = self.current_settings.get("freshclam_path") or "freshclam"
        db_dir = self.current_settings.get("virus_db_dir") or r"C:\\ProgramData\\ClamAV\\db"

        # Ensure DB directory exists and is writable
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            self.db_output.append(f"Failed to create DB directory '{db_dir}': {e}")
            self.db_output.append("Tip: choose a writable path in Settings → Virus DB Directory or run with elevated privileges.")
            return

        self.db_process = QProcess(self)
        self.db_process.setProcessChannelMode(QProcess.MergedChannels)
        self.db_process.readyReadStandardOutput.connect(self._on_db_output)
        self.db_process.finished.connect(self._on_db_finished)
        self.db_process.errorOccurred.connect(self._on_db_error)

        args = [f"--datadir={db_dir}"]
        self.db_output.append(f"Running: {freshclam} {' '.join(args)}")
        self.db_progress.setRange(0, 0)
        self.db_start_btn.setEnabled(False)
        self.db_stop_btn.setEnabled(True)
        try:
            self.db_process.start(freshclam, args)
        except Exception as e:
            self.db_output.append(f"Failed to start freshclam: {e}")
            self.db_progress.setRange(0, 1)
            self.db_progress.setValue(0)
            self.db_start_btn.setEnabled(True)
            self.db_stop_btn.setEnabled(False)

    def _stop_db_update(self) -> None:
        if self.db_process is not None:
            try:
                if self.db_process.state() != QProcess.NotRunning:
                    self.db_process.terminate()
                    if not self.db_process.waitForFinished(2000):
                        self.db_process.kill()
            except Exception:
                pass
            self.db_process = None
        self.db_progress.setRange(0, 1)
        self.db_progress.setValue(0)
        self.db_output.append("Virus DB update stopped.")
        self.db_start_btn.setEnabled(True)
        self.db_stop_btn.setEnabled(False)

    def _on_db_output(self) -> None:
        try:
            data = self.db_process.readAllStandardOutput() if self.db_process else b""
            if not data:
                return
            try:
                text = bytes(data).decode("utf-8", errors="replace")
            except Exception:
                text = str(bytes(data))
            if text:
                self.db_output.append(text.rstrip())
        except Exception as e:
            self.db_output.append(f"Output error: {e}")

    def _on_db_finished(self, exit_code: int, exit_status) -> None:
        self.db_progress.setRange(0, 1)
        self.db_progress.setValue(0)
        self.db_output.append(f"Virus DB update finished with code {exit_code}.")
        self.db_start_btn.setEnabled(True)
        self.db_stop_btn.setEnabled(False)
        self.db_process = None

    def _on_db_error(self, process_error) -> None:
        self.db_output.append("Virus DB update process error occurred.")
        if self.db_process is not None:
            self.db_output.append(f"Process error: {process_error}")
        self.db_start_btn.setEnabled(True)
        self.db_stop_btn.setEnabled(False)
        self.db_progress.setRange(0, 1)
        self.db_progress.setValue(0)

    # --- Scan tab (UI only with stubbed logic) ---
    def _create_scan_tab(self) -> QWidget:
        tab = QWidget()
        v = QVBoxLayout(tab)

        # Target selection
        target_group = QGroupBox("Scan Target")
        hg = QHBoxLayout(target_group)
        self.target_input = QLineEdit()
        self.target_input.setPlaceholderText("Select a file or directory to scan...")
        browse_btn = QPushButton("Browse...")
        browse_btn.clicked.connect(self._browse_target)
        hg.addWidget(self.target_input)
        hg.addWidget(browse_btn)

        # Options
        options_group = QGroupBox("Scan Options")
        ov = QVBoxLayout(options_group)
        self.recursive_scan = QCheckBox("Scan subdirectories")
        self.recursive_scan.setChecked(True)
        self.heuristic_scan = QCheckBox("Enable heuristic scan")
        self.heuristic_scan.setChecked(True)
        self.scan_archives_opt = QCheckBox("Scan archives (zip, rar, etc.)")
        self.scan_archives_opt.setChecked(True)
        self.scan_pua_opt = QCheckBox("Scan potentially unwanted applications (PUA)")
        self.scan_pua_opt.setChecked(False)
        ov.addWidget(self.recursive_scan)
        ov.addWidget(self.heuristic_scan)
        ov.addWidget(self.scan_archives_opt)
        ov.addWidget(self.scan_pua_opt)

        # Output
        output_group = QGroupBox("Output")
        out_v = QVBoxLayout(output_group)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        out_v.addWidget(self.output)

        # Progress
        self.progress = QProgressBar()

        # Buttons
        btns = QHBoxLayout()
        self.scan_btn = QPushButton("Start Scan")
        self.scan_btn.clicked.connect(self._start_scan)
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self._stop_scan)
        self.save_report_btn = QPushButton("Save Report")
        self.save_report_btn.setEnabled(False)
        self.save_report_btn.clicked.connect(self._save_scan_report)
        btns.addWidget(self.scan_btn)
        btns.addWidget(self.stop_btn)
        btns.addWidget(self.save_report_btn)

        # Compose
        v.addWidget(target_group)
        v.addWidget(options_group)
        v.addWidget(output_group)
        v.addWidget(self.progress)
        v.addLayout(btns)

        return tab

    # --- Scan tab handlers (stubs) ---
    def _browse_target(self) -> None:
        # Let user choose either file or directory; prefer dir first
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Scan", "")
        if dir_path:
            self.target_input.setText(dir_path)
            return
        file_path, _ = QFileDialog.getOpenFileName(self, "Select File to Scan", "", "All Files (*.*)")
        if file_path:
            self.target_input.setText(file_path)

    def _start_scan(self) -> None:
        # Start real scan using clamscan via QProcess
        target = self.target_input.text().strip()
        if not target:
            self.output.append("Please select a target before starting the scan.")
            return
        # Resolve clamscan path from settings; fallback to 'clamscan'
        try:
            if not hasattr(self, "current_settings"):
                self.current_settings = self.settings.load_settings() or {}
        except Exception:
            self.current_settings = {}
        clamscan = self.current_settings.get("clamscan_path") or "clamscan"

        # Build arguments
        args = []
        if self.recursive_scan.isChecked():
            args.append("-r")
        # PUA detection flag if supported; include only if requested
        if self.scan_pua_opt.isChecked():
            args.append("--detect-pua")
        # Append target last
        args.append(target)

        # Prepare process
        self.scan_process = QProcess(self)
        # Merge channels to simplify output handling
        self.scan_process.setProcessChannelMode(QProcess.MergedChannels)
        self.scan_process.readyReadStandardOutput.connect(self._on_scan_output)
        self.scan_process.finished.connect(self._on_scan_finished)
        self.scan_process.errorOccurred.connect(self._on_scan_error)

        # UI state
        self.output.append(f"Running: {clamscan} {' '.join(args)}")
        self.progress.setRange(0, 0)
        self.scan_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.save_report_btn.setEnabled(False)

        try:
            self.scan_process.start(clamscan, args)
        except Exception as e:
            self.output.append(f"Failed to start scan: {e}")
            self.progress.setRange(0, 1)
            self.progress.setValue(0)
            self.scan_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)

    def _stop_scan(self) -> None:
        # Stop running scan process if any
        if self.scan_process is not None:
            try:
                if self.scan_process.state() != QProcess.NotRunning:
                    self.scan_process.terminate()
                    if not self.scan_process.waitForFinished(2000):
                        self.scan_process.kill()
            except Exception:
                pass
            self.scan_process = None
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.output.append("Scan stopped.")
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_report_btn.setEnabled(True)

    def _save_scan_report(self) -> None:
        # Stub: save current output to a file
        text = self.output.toPlainText()
        if not text:
            self.output.append("Nothing to save.")
            return
        path, _ = QFileDialog.getSaveFileName(self, "Save Report", "scan_report.txt", "Text Files (*.txt)")
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(text)
                self.output.append(f"Report saved to: {path}")
            except Exception as e:
                self.output.append(f"Failed to save report: {e}")

    # Scan process callbacks
    def _on_scan_output(self) -> None:
        try:
            data = self.scan_process.readAllStandardOutput() if self.scan_process else b""
            if not data:
                return
            try:
                text = bytes(data).decode("utf-8", errors="replace")
            except Exception:
                text = str(bytes(data))
            if text:
                self.output.append(text.rstrip())
        except Exception as e:
            self.output.append(f"Output error: {e}")

    def _on_scan_finished(self, exit_code: int, exit_status) -> None:
        self.progress.setRange(0, 1)
        self.progress.setValue(0)
        self.output.append(f"Scan finished with code {exit_code}.")
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.save_report_btn.setEnabled(True)
        self.scan_process = None

    def _on_scan_error(self, process_error) -> None:
        # Provide a helpful hint if clamscan is not found
        self.output.append("Scan process error occurred.")
        if self.scan_process is not None:
            self.output.append(f"Process error: {process_error}")
        self.scan_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setRange(0, 1)
        self.progress.setValue(0)

    def _apply_settings(self) -> None:
        cs = self.current_settings
        self.clamd_path.setText(cs.get("clamd_path", ""))
        self.freshclam_path.setText(cs.get("freshclam_path", ""))
        self.clamscan_path.setText(cs.get("clamscan_path", ""))
        self.db_dir_path.setText(cs.get("virus_db_dir", r"C:\\ProgramData\\ClamAV\\db"))
        self.scan_archives.setChecked(bool(cs.get("scan_archives", True)))
        self.scan_heuristics.setChecked(bool(cs.get("scan_heuristics", True)))
        self.scan_pua.setChecked(bool(cs.get("scan_pua", False)))
        self.enable_quarantine.setChecked(bool(cs.get("enable_quarantine", True)))

    def _save_settings(self) -> None:
        data = {
            "clamd_path": self.clamd_path.text().strip(),
            "freshclam_path": self.freshclam_path.text().strip(),
            "clamscan_path": self.clamscan_path.text().strip(),
            "virus_db_dir": self.db_dir_path.text().strip(),
            "scan_archives": self.scan_archives.isChecked(),
            "scan_heuristics": self.scan_heuristics.isChecked(),
            "scan_pua": self.scan_pua.isChecked(),
            "enable_quarantine": self.enable_quarantine.isChecked(),
        }
        try:
            self.settings.save_settings(data)
            logger.info("[MainUIWindow] Settings saved")
        except Exception as e:
            logger.error(f"[MainUIWindow] Failed to save settings: {e}")
