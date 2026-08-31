"""
RAMGuard Settings Page
User-configurable settings with persistence.
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QCheckBox, QSpinBox, QComboBox, QFrame, QMessageBox,
    QGroupBox, QFormLayout,
)
from PyQt6.QtCore import Qt, pyqtSignal
from config.app_config import AppConfig
from utils.logger import get_logger

logger = get_logger("SettingsPage")


class SettingsPage(QWidget):
    """Application settings panel."""

    theme_changed = pyqtSignal(str)
    interval_changed = pyqtSignal(int)

    def __init__(self, config: AppConfig, parent=None) -> None:
        super().__init__(parent)
        self._config = config
        self._build_ui()

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 24)
        root.setSpacing(20)

        title = QLabel("Settings")
        title.setStyleSheet("font-size:22px;font-weight:700;color:#e6edf3;")
        sub = QLabel("Configure RAMGuard behaviour and preferences")
        sub.setStyleSheet("color:#8b949e;font-size:12px;")
        root.addWidget(title)
        root.addWidget(sub)

        # ── General ──
        root.addWidget(self._section("General Settings", [
            self._row_check("Start RAMGuard with Windows",
                            self._config.get("start_with_windows", False),
                            "start_with_windows"),
            self._row_check("Show notifications when memory is high",
                            self._config.get("show_notifications", True),
                            "show_notifications"),
        ]))

        # ── Monitoring ──
        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(1, 60)
        self._interval_spin.setValue(self._config.monitoring_interval)
        self._interval_spin.setSuffix(" seconds")
        self._interval_spin.valueChanged.connect(self._on_interval_changed)

        self._warn_spin = QSpinBox()
        self._warn_spin.setRange(50, 95)
        self._warn_spin.setValue(self._config.warning_threshold)
        self._warn_spin.setSuffix("%")

        self._crit_spin = QSpinBox()
        self._crit_spin.setRange(80, 99)
        self._crit_spin.setValue(self._config.critical_threshold)
        self._crit_spin.setSuffix("%")

        mon_group = self._group("Monitoring Settings")
        mon_layout = QVBoxLayout(mon_group)
        mon_layout.addLayout(self._form_row("Monitoring Interval:", self._interval_spin))
        mon_layout.addLayout(self._form_row("Warning Threshold:", self._warn_spin))
        mon_layout.addLayout(self._form_row("Critical Threshold:", self._crit_spin))
        root.addWidget(mon_group)

        # ── Appearance ──
        self._theme_combo = QComboBox()
        self._theme_combo.addItems(["dark", "light"])
        self._theme_combo.setCurrentText(self._config.theme)
        self._theme_combo.currentTextChanged.connect(self._on_theme_changed)

        self._mode_combo = QComboBox()
        self._mode_combo.addItems(["SAFE", "SMART", "CUSTOM"])
        self._mode_combo.setCurrentText(self._config.default_mode)

        appear_group = self._group("Appearance")
        appear_layout = QVBoxLayout(appear_group)
        appear_layout.addLayout(self._form_row("Theme:", self._theme_combo))
        appear_layout.addLayout(self._form_row("Default Optimization Mode:", self._mode_combo))
        root.addWidget(appear_group)

        # ── Protected processes info ──
        prot_group = self._group("Protected Processes")
        prot_layout = QVBoxLayout(prot_group)
        prot_info = QLabel(
            "RAMGuard permanently protects all Windows system processes, security software, "
            "drivers, and RAMGuard itself from termination.\n\n"
            "Protected categories include: Windows kernel processes, Windows Defender / antimalware, "
            "graphics drivers, network stack, session manager, and more."
        )
        prot_info.setStyleSheet("color:#8b949e;font-size:12px;")
        prot_info.setWordWrap(True)
        prot_layout.addWidget(prot_info)
        root.addWidget(prot_group)

        # ── Save ──
        btn_row = QHBoxLayout()
        save_btn = QPushButton("Save Settings")
        save_btn.setObjectName("optimize_btn")
        save_btn.setFixedHeight(44)
        save_btn.setFixedWidth(160)
        save_btn.clicked.connect(self._save)

        reset_btn = QPushButton("Reset to Defaults")
        reset_btn.setObjectName("secondary_btn")
        reset_btn.clicked.connect(self._reset)

        btn_row.addWidget(reset_btn)
        btn_row.addStretch()
        btn_row.addWidget(save_btn)
        root.addLayout(btn_row)

        root.addStretch()

    def _save(self) -> None:
        self._config.set("monitoring_interval_seconds", self._interval_spin.value())
        self._config.set("memory_warning_threshold_percent", self._warn_spin.value())
        self._config.set("memory_critical_threshold_percent", self._crit_spin.value())
        self._config.set("theme", self._theme_combo.currentText())
        self._config.set("default_optimization_mode", self._mode_combo.currentText())
        QMessageBox.information(self, "Settings Saved", "Your settings have been saved successfully.")

    def _reset(self) -> None:
        reply = QMessageBox.question(
            self, "Reset Settings",
            "Reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if reply == QMessageBox.StandardButton.Yes:
            self._interval_spin.setValue(3)
            self._warn_spin.setValue(80)
            self._crit_spin.setValue(90)
            self._theme_combo.setCurrentText("dark")
            self._mode_combo.setCurrentText("SAFE")
            self._save()

    def _on_theme_changed(self, theme: str) -> None:
        self.theme_changed.emit(theme)

    def _on_interval_changed(self, val: int) -> None:
        self.interval_changed.emit(val)

    # ── Helpers ──

    def _group(self, title: str) -> QGroupBox:
        g = QGroupBox(title)
        g.setStyleSheet("""
            QGroupBox {
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 8px;
                font-weight: 600;
                font-size: 13px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 4px;
            }
        """)
        return g

    def _section(self, heading: str, rows: list) -> QFrame:
        frame = QFrame()
        frame.setObjectName("card")
        layout = QVBoxLayout(frame)
        lbl = QLabel(heading)
        lbl.setStyleSheet("font-weight:600;color:#e6edf3;font-size:13px;")
        layout.addWidget(lbl)
        for row in rows:
            layout.addLayout(row)
        return frame

    def _row_check(self, label: str, value: bool, key: str) -> QHBoxLayout:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#c9d1d9;font-size:12px;")
        cb = QCheckBox()
        cb.setChecked(value)
        cb.stateChanged.connect(lambda state, k=key: self._config.set(k, bool(state)))
        row.addWidget(lbl)
        row.addStretch()
        row.addWidget(cb)
        return row

    def _form_row(self, label: str, widget) -> QHBoxLayout:
        row = QHBoxLayout()
        lbl = QLabel(label)
        lbl.setStyleSheet("color:#8b949e;font-size:12px;min-width:200px;")
        row.addWidget(lbl)
        row.addWidget(widget)
        row.addStretch()
        return row
