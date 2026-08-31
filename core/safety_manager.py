"""
RAMGuard Safety Manager
The most critical module — determines which processes are safe to terminate.
SAFETY IS THE HIGHEST PRIORITY.
"""

import os
import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from utils.logger import get_logger

logger = get_logger("SafetyManager")


class SafetyLevel(Enum):
    PROTECTED = "PROTECTED"
    REVIEW = "REVIEW"
    SAFE_TO_CLOSE = "SAFE TO CLOSE"
    UNKNOWN = "UNKNOWN"


@dataclass
class SafetyAssessment:
    level: SafetyLevel
    reason: str
    can_terminate: bool
    recommendation: str = ""
    warnings: list[str] = field(default_factory=list)


# ─────────────────────────────────────────────────────────────────
#  Master protected-process list (case-insensitive matching)
# ─────────────────────────────────────────────────────────────────
PROTECTED_PROCESS_NAMES: set[str] = {
    # Windows Core OS
    "system", "system idle process", "registry",
    "smss.exe", "csrss.exe", "wininit.exe", "winlogon.exe",
    "lsass.exe", "lsaiso.exe", "services.exe", "svchost.exe",
    "dwm.exe", "fontdrvhost.exe", "sihost.exe", "taskhostw.exe",
    "runtimebroker.exe", "startmenuexperiencehost.exe",
    "searchindexer.exe", "searchhost.exe",
    "spoolsv.exe", "audiodg.exe", "conhost.exe", "condrv.exe",
    "ctfloader.exe", "wlanext.exe", "wermgr.exe", "werfault.exe",
    "dllhost.exe", "msiexec.exe", "regsvc.exe",
    "ntoskrnl.exe", "hal.dll",
    # Shell / Explorer
    "explorer.exe",
    # Windows Defender & Security
    "msmpeng.exe", "nissrv.exe", "antimalware service executable",
    "securityhealthservice.exe", "securityhealthsystray.exe",
    "mssense.exe", "sensecncproc.exe", "mssensece.exe",
    # Windows Update
    "wuauclt.exe", "usoclient.exe", "musnotification.exe",
    "tiworker.exe", "trusstedinstaller.exe",
    # TPM / BitLocker / Credential Guard
    "tpmvscmgr.exe", "bdehdcfg.exe", "lsaiso.exe",
    # Network stack
    "netsh.exe", "ipconfig.exe", "dns.exe", "dnscache",
    # Input / HID
    "inputservice.exe", "tabtip.exe",
    # Graphics drivers
    "nvcontainer.exe", "nvspcap64.dll", "igfxem.exe", "igfxhk.exe",
    # RAMGuard itself (never terminate self)
    "ramguard.exe", "python.exe", "pythonw.exe",
    # Hardware management
    "hkcmd.exe", "persistence.exe",
    # System restore / VSS
    "vssvc.exe",
    # Task Scheduler
    "taskeng.exe", "schedsvc.exe",
}

PROTECTED_KEYWORDS: tuple[str, ...] = (
    "system", "kernel", "driver", "service", "security",
    "defender", "antivirus", "antimalware", "firewall",
    "nvidia", "amd", "intel", "realtek", "audio", "display",
    "windows", "microsoft", "update", "trusted", "credential",
    "lsa", "sam", "wmi", "wbem", "network", "vpn",
)

SAFE_TO_CLOSE_PATTERNS: tuple[str, ...] = (
    "chrome", "firefox", "msedge", "opera", "brave", "vivaldi",
    "discord", "slack", "telegram", "whatsapp", "signal",
    "spotify", "vlc", "musicbee", "foobar2000",
    "notepad", "notepad++", "wordpad",
    "steam", "epicgameslauncher", "origin", "gog", "battle.net",
    "zoom", "teams", "skype",  # review-level but user-closeable
    "7zfm", "winrar", "everything.exe",
    "obs", "obs64", "streamlabs",
    "gimp", "inkscape", "krita", "blender",
    "putty", "filezilla", "winscp",
    "calc", "mspaint", "snippingtool",
    "acrobat", "acrord32", "sumatra",
)

REVIEW_PATTERNS: tuple[str, ...] = (
    "teams", "zoom", "skype", "outlook", "thunderbird",
    "onedrive", "dropbox", "googledrivefs",
    "nvcontainer", "nvcplui", "radeonSoftware",
    "corsair", "razer", "logitech",
    "vmware", "virtualbox", "vboxsvc",
)


class ProcessSafetyManager:
    """
    Single source of truth for all process safety decisions in RAMGuard.
    
    Rules (non-negotiable):
    1. A protected process is NEVER terminated.
    2. RAMGuard itself is NEVER terminated.
    3. If a process cannot be confidently classified → REVIEW (not SAFE_TO_CLOSE).
    4. Every classification decision is logged.
    5. Classification is re-evaluated immediately before any termination attempt.
    """

    def __init__(self) -> None:
        self._own_pid: int = os.getpid()
        self._own_name: str = "python.exe"
        self._custom_protected: set[str] = set()
        logger.info("ProcessSafetyManager initialised (own PID=%d)", self._own_pid)

    # ──────────────────────────────────────────────────────────────
    #  Public API
    # ──────────────────────────────────────────────────────────────

    def assess(self, pid: int, name: str, exe: Optional[str] = None) -> SafetyAssessment:
        """
        Perform a full safety assessment for a process.
        
        Args:
            pid:  Process ID
            name: Process name (e.g. 'chrome.exe')
            exe:  Full executable path (optional, improves accuracy)
        
        Returns:
            SafetyAssessment with level, reason, and can_terminate flag
        """
        name_lower = name.lower().strip()

        # Rule 0: Never touch RAMGuard itself
        if pid == self._own_pid:
            return SafetyAssessment(
                level=SafetyLevel.PROTECTED,
                reason="This is the RAMGuard process itself.",
                can_terminate=False,
            )

        # Rule 1: Custom user-added protected processes
        if name_lower in self._custom_protected:
            return SafetyAssessment(
                level=SafetyLevel.PROTECTED,
                reason="This process has been marked as protected by the user.",
                can_terminate=False,
            )

        # Rule 2: Well-known protected list (exact match)
        if name_lower in PROTECTED_PROCESS_NAMES:
            return SafetyAssessment(
                level=SafetyLevel.PROTECTED,
                reason=self._protected_reason(name_lower),
                can_terminate=False,
            )

        # Rule 3: PID ≤ 4 (System / System Idle Process)
        if pid <= 4:
            return SafetyAssessment(
                level=SafetyLevel.PROTECTED,
                reason="Core Windows kernel process (PID ≤ 4).",
                can_terminate=False,
            )

        # Rule 4: Protected keyword scan (name)
        matched_kw = self._match_keyword(name_lower, PROTECTED_KEYWORDS)
        if matched_kw:
            return SafetyAssessment(
                level=SafetyLevel.PROTECTED,
                reason=f"Process name contains protected keyword '{matched_kw}' — may be a system or security component.",
                can_terminate=False,
            )

        # Rule 5: Exe path keyword scan
        if exe:
            exe_lower = exe.lower()
            if any(kw in exe_lower for kw in (r"\windows\system32", r"\windows\syswow64", r"\windows\winsxs")):
                return SafetyAssessment(
                    level=SafetyLevel.PROTECTED,
                    reason="Executable resides in a Windows system directory.",
                    can_terminate=False,
                )
            matched_kw = self._match_keyword(exe_lower, PROTECTED_KEYWORDS)
            if matched_kw:
                return SafetyAssessment(
                    level=SafetyLevel.PROTECTED,
                    reason=f"Executable path contains protected keyword '{matched_kw}'.",
                    can_terminate=False,
                )

        # Rule 6: Known REVIEW processes
        for pat in REVIEW_PATTERNS:
            if pat in name_lower:
                return SafetyAssessment(
                    level=SafetyLevel.REVIEW,
                    reason=f"'{name}' may have unsaved data or background sync jobs. Close with care.",
                    can_terminate=True,
                    recommendation="Save all work before closing.",
                    warnings=["May lose unsaved data", "Background sync may be interrupted"],
                )

        # Rule 7: Known SAFE patterns
        for pat in SAFE_TO_CLOSE_PATTERNS:
            if pat in name_lower:
                return SafetyAssessment(
                    level=SafetyLevel.SAFE_TO_CLOSE,
                    reason=f"'{name}' is a recognized user application that can generally be closed safely.",
                    can_terminate=True,
                    recommendation="Ensure you have saved any open work.",
                )

        # Rule 8: Fallback — unknown process → REVIEW (conservative)
        return SafetyAssessment(
            level=SafetyLevel.REVIEW,
            reason=(
                f"RAMGuard cannot confidently classify '{name}'. "
                "It has been marked for review — please verify before closing."
            ),
            can_terminate=True,
            warnings=["Unknown process — verify before closing"],
        )

    def can_terminate(self, pid: int, name: str, exe: Optional[str] = None) -> bool:
        """Quick boolean check — is termination allowed?"""
        assessment = self.assess(pid, name, exe)
        result = assessment.can_terminate and assessment.level != SafetyLevel.PROTECTED
        logger.debug("can_terminate(%d, %s) → %s [%s]", pid, name, result, assessment.level.value)
        return result

    def add_custom_protected(self, process_name: str) -> None:
        """Add a process name to the custom protected list."""
        self._custom_protected.add(process_name.lower().strip())
        logger.info("Added custom protected process: %s", process_name)

    def remove_custom_protected(self, process_name: str) -> None:
        """Remove a process name from the custom protected list."""
        self._custom_protected.discard(process_name.lower().strip())
        logger.info("Removed custom protected process: %s", process_name)

    def get_protected_list(self) -> list[str]:
        """Return the full list of protected process names."""
        return sorted(PROTECTED_PROCESS_NAMES | self._custom_protected)

    # ──────────────────────────────────────────────────────────────
    #  Private helpers
    # ──────────────────────────────────────────────────────────────

    @staticmethod
    def _protected_reason(name: str) -> str:
        reasons = {
            "lsass.exe": "Local Security Authority — handles authentication and credential storage.",
            "csrss.exe": "Client/Server Runtime Subsystem — essential for Windows operation.",
            "winlogon.exe": "Windows Logon Process — manages logon/logoff sequences.",
            "wininit.exe": "Windows Initialization Process — starts core services.",
            "services.exe": "Service Control Manager — manages all Windows services.",
            "svchost.exe": "Service Host — hosts multiple essential Windows services.",
            "smss.exe": "Session Manager — initialises the user session.",
            "dwm.exe": "Desktop Window Manager — renders the Windows desktop.",
            "explorer.exe": "Windows Shell / Explorer — provides the desktop and file manager.",
            "msmpeng.exe": "Windows Defender Antimalware — real-time security protection.",
            "python.exe": "RAMGuard host process — cannot terminate self.",
            "pythonw.exe": "RAMGuard host process — cannot terminate self.",
        }
        return reasons.get(
            name,
            "Critical Windows system/security process. RAMGuard will not terminate this process "
            "because it may be required for system stability, security, or core OS functionality.",
        )

    @staticmethod
    def _match_keyword(text: str, keywords: tuple[str, ...]) -> Optional[str]:
        for kw in keywords:
            if kw in text:
                return kw
        return None
