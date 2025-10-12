# Translation data
TRANSLATIONS = {
    "en_US": {
        # Main window
        "window.title": "ClamAV GUI",
        "status.ready": "Ready",
        "status.scanning": "Scanning...",
        "status.updating": "Updating...",
        
        # Tabs
        "tab.scan": "Scan",
        "tab.update": "Update",
        "tab.settings": "Settings",
        "tab.config_editor": "Config Editor",
        "tab.quarantine": "Quarantine",
        "tab.email_scan": "Email Scan",
        "tab.home": "Home",
        "tab.status": "Status",
        "tab.virus_db": "Virus DB",

        # Menu titles
        "menu.file": "&File",
        "menu.tools": "&Tools",
        "menu.help": "&Help",
        "menu.language": "&Language",

        # Menu actions (literal keys used by menu)
        "E&xit": "E&xit",
        "Check for &Updates...": "Check for &Updates...",
        "&Help": "&Help",
        "&About": "&About",
        "&Sponsor": "&Sponsor",
        "&Wiki": "&Wiki",
        "View &Logs": "View &Logs",
        
        # Scan tab
        "scan.target": "Scan Target",
        "scan.browse": "Browse...",
        "scan.start": "Start Scan",
        "scan.stop": "Stop",
        "scan.output": "Output",
        "scan.select_file": "Select file or directory to scan",
        "scan.subdirectories": "Scan subdirectories",
        "scan.heuristic": "Enable heuristic scan",
        "scan.auto_quarantine": "Auto-quarantine infected files",
        "scan.archives": "Scan archives (zip, rar, etc.)",
        "scan.pua": "Scan potentially unwanted applications (PUA)",
        "scan.save_report": "Save Report",
        "scan.view_quarantine": "View Quarantine",
        
        # Update tab
        "update.database": "Virus Database Update",
        "update.now": "Update Now",
        "update.output": "Update Output",
        "update.last_updated": "Last updated: {}",
        "update.never": "Never",
        
        # Settings tab
        "settings.paths": "ClamAV Paths",
        "settings.clamd_path": "ClamD Path",
        "settings.freshclam_path": "FreshClam Path",
        "settings.clamscan_path": "ClamScan Path",
        "settings.virus_db_dir": "Virus DB Directory",
        "settings.scan_options": "Scan Settings",
        "settings.auto_update": "Check for updates automatically",
        "settings.scan_archives": "Scan inside archives",
        "settings.scan_heuristics": "Enable heuristic scanning",
        "settings.scan_pua": "Scan for potentially unwanted applications",
        "settings.save": "Save Settings",
        "settings.reset": "Reset to Defaults",
        "settings.saved": "Settings saved successfully",
        "settings.save_error": "Failed to save settings",
        "settings.reset_confirm": "Are you sure you want to reset all settings to default values?",
        "settings.general": "General Settings",
        "settings.theme": "Theme:",
        "settings.language": "Language:",
        "settings.basic_options": "Basic Options",
        "settings.heuristic_analysis": "Enable heuristic analysis",
        "settings.performance": "Performance Settings",
        "settings.max_file_size": "Max file size (MB):",
        "settings.max_scan_time": "Max scan time (sec):",
        "settings.file_patterns": "File Patterns",
        "settings.exclude_patterns": "Exclude patterns:",
        "settings.include_patterns": "Include patterns:",
        
        # Quarantine tab
        "quarantine.stats": "Quarantine Statistics",
        "quarantine.refresh": "Refresh Stats",
        "quarantine.files": "Quarantined Files",
        "quarantine.restore": "Restore Selected",
        "quarantine.delete": "Delete Selected",
        "quarantine.export": "Export List",
        "quarantine.no_files": "No quarantined files",
        "quarantine.no_selection": "No Selection",
        "quarantine.select_restore": "Please select a file to restore",
        "quarantine.confirm_restore": "Are you sure you want to restore",
        "quarantine.restore_warning": "Warning: This file was detected as infected and may be dangerous.",
        "quarantine.restore_success": "File restoration is not yet fully implemented. This feature will be available in a future update.",
        "quarantine.confirm_delete": "Are you sure you want to permanently delete",
        "quarantine.delete_warning": "This action cannot be undone.",
        "quarantine.delete_success": "File deletion is not yet fully implemented. This feature will be available in a future update.",
        "quarantine.export_title": "Export Quarantine List",
        "quarantine.export_filter": "JSON Files (*.json);;All Files (*)",
        "quarantine.export_success": "Quarantine list exported successfully",
        "quarantine.export_failed": "Failed to export quarantine list",
        
        # Config editor tab
        "config.editor": "Configuration Editor",
        "config.load": "Load Config",
        "config.save": "Save Config",
        
        # File dialogs
        "dialog.select_folder": "Select Folder",
        "dialog.all_files": "All Files (*)",
        
        # Messages
        "msg.error": "Error",
        "msg.warning": "Warning",
        "msg.info": "Information",
        "msg.success": "Success",
        "msg.confirm_exit": "Are you sure you want to exit?",
        "msg.no_target": "Please select a target to scan",
        "msg.scan_complete": "Scan completed successfully",
        "msg.scan_complete_clean": "The scan completed successfully. No threats were found.",
        "msg.scan_complete_threats": "The scan completed and found {} potential threats. Check the scan results for details.",
        "msg.scan_failed": "The scan failed to complete. Please check if ClamAV is properly installed and configured.",
        "msg.settings_saved": "Settings saved successfully",
        "msg.db_create_error": "Failed to create database directory: {}",
        "msg.clamav_not_found": "ClamAV Not Found",
        "msg.auto_detect": "Auto-detect ClamAV?",
        "msg.use_detected_path": "Would you like to use the detected path: {}?",
        "msg.language_changed": "Language changed to {}",
        "logs.open_failed": "Could not open logs folder",
        "logs.opened": "Opened logs: {}",
        
        # Home tab
        "home.title": "ClamAV GUI",
        "home.welcome": "Welcome! Use the tabs above to scan, update, and manage quarantine.",
        "home.quick_scan": "Quick Scan...",
        "home.check_updates": "Check for Updates",
        "home.open_logs": "Open Logs Folder",
        
        # Status tab
        "status.env": "Environment",
        "status.tools": "Tools",
        "status.app_version": "App Version:",
        "status.python": "Python:",
        "status.os": "OS:",
        "status.open_settings": "Open Settings",
        "status.view_logs": "View Logs",
        
        # Virus DB tab
        "virus_db.info": "Update ClamAV virus definitions using freshclam",
        "virus_db.update": "Update Virus DB",
        "virus_db.stopped": "Virus DB update stopped.",
        "virus_db.finished": "Virus DB update finished with code {}.",
        "virus_db.process_error": "Virus DB update process error occurred.",
    }
}    

# Available languages - keep only those with actual translations
AVAILABLE_LANGUAGES = {
    "en_US": "English (United States)",
    "it_IT": "Italiano (Italia)",   
}
