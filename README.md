# RAMGuard — Smart & Safe Windows Memory Optimization

> **Free memory. Stay in control. Stay safe.**

RAMGuard is a professional Windows desktop application that monitors system memory usage and helps users safely reduce unnecessary memory consumption. It **never** automatically closes applications — all optimization actions require explicit user confirmation.

---

## 🖥 Screenshots

RAMGuard features a modern dark-themed interface with:
- Real-time circular RAM gauge
- Live process table with safety classification
- One-click memory optimization workflow
- Before/after results display

---

## ✨ Features

| Feature | Description |
|---|---|
| **Real-Time Dashboard** | Live RAM %, CPU %, process count, and memory pressure indicator |
| **Process Scanner** | Sorted by memory consumption with safety classification |
| **Smart Classification** | SAFE TO CLOSE / REVIEW / PROTECTED per process |
| **One-Click Optimize** | Scan → Recommend → User Confirmation → Safe Close → Report |
| **Safety Manager** | 200+ protected system processes — never touched |
| **Graceful Shutdown** | Terminate → Wait → Kill only if needed |
| **Startup Manager** | View and toggle Windows startup programs |
| **Optimization History** | SQLite-backed history with full details |
| **Settings** | Monitoring interval, thresholds, theme preference, default mode |

---

## 🛡 Safety Rules (Non-Negotiable)

1. Never terminate a process simply because it uses high RAM
2. Never automatically terminate Windows critical processes
3. Never terminate RAMGuard itself
4. Never terminate security / antivirus / system-critical processes
5. Require user confirmation before any optimization
6. Prefer graceful application shutdown over force-kill
7. Re-check the process immediately before closing it
8. Handle permission errors without crashing
9. Log every optimization action
10. If uncertain about a process → classify as REVIEW/PROTECTED, **never** auto-close

---

## 🚀 Quick Start

### Prerequisites

- Windows 10 / 11
- Python 3.12+

### Installation

```bash
# 1. Clone or download the project
cd "Memory magement system (RamGuard)"

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run setup (creates data/ and logs/ directories)
python setup_dirs.py

# 4. Launch RAMGuard
python main.py
```

> **Tip:** Run as Administrator to unlock full process access and startup manager functionality.

---

## 📦 Dependencies

```
PyQt6>=6.5.0
psutil>=5.9.0
```

All dependencies are listed in `requirements.txt`. No additional packages are required.

---

## 📁 Project Structure

```
RAMGuard/
├── main.py                     # Entry point
├── setup_dirs.py               # First-run directory setup
├── requirements.txt
│
├── core/
│   ├── safety_manager.py       # ★ Process safety classification (most critical)
│   ├── process_scanner.py      # Live process enumeration
│   ├── memory_monitor.py       # RAM & CPU metrics
│   ├── optimizer.py            # Safe process closure orchestrator
│   └── startup_manager.py      # Windows startup entries
│
├── ui/
│   ├── main_window.py          # Main window & navigation controller
│   ├── dashboard.py            # Real-time dashboard with gauge
│   ├── applications.py         # Process table with filters
│   ├── optimization.py         # Optimization mode selector & dialogs
│   ├── startup.py              # Startup manager page
│   ├── history.py              # Optimization history page
│   ├── settings.py             # Settings page
│   ├── workers.py              # Background QThread workers
│   ├── styles.py               # Dark theme stylesheets
│   ├── custom_widgets.py       # Reusable custom Qt widgets
│   └── icon_helper.py          # Process icon resolution helper
│
├── database/
│   └── database.py             # SQLite persistence (history + settings)
│
├── config/
│   ├── config.json             # User configuration file
│   └── app_config.py           # Configuration manager
│
├── utils/
│   ├── logger.py               # Centralized logging
│   └── system_utils.py         # Windows API helpers
│
├── data/                       # SQLite database (auto-created)
│   └── ramguard.db
└── logs/                       # Log files (auto-created)
```

---

## 🎛 Optimization Modes

| Mode | Description |
|---|---|
| **SAFE** *(default)* | Only processes explicitly selected by the user are closed |
| **SMART** | RAMGuard recommends high-memory SAFE TO CLOSE applications |
| **CUSTOM** | User manually selects from the full application list |

---

## 🔒 Protected Process Categories

RAMGuard will **never** touch:

- Windows kernel processes (`System`, `smss.exe`, `csrss.exe`, `wininit.exe`, etc.)
- Authentication (`lsass.exe`, `winlogon.exe`)
- Windows Defender & antimalware (`MsMpEng.exe`, `NisSrv.exe`, `SecurityHealthService.exe`)
- Desktop Window Manager (`dwm.exe`)
- Windows Explorer shell (`explorer.exe`)
- Graphics drivers (`nvcontainer.exe`, `igfxEM.exe`, `igfxHK.exe`)
- Windows Update (`wuauclt.exe`, `TiWorker.exe`, `UsoClient.exe`)
- Network stack (`netsh.exe`, `dnscache`, etc.)
- RAMGuard itself (`python.exe`, `pythonw.exe`)
- Any process whose name contains: `system`, `kernel`, `driver`, `service`, `security`, `defender`, `antivirus`, `antimalware`, `firewall`, `nvidia`, `amd`, `intel`, `realtek`, `audio`, `display`, `windows`, `microsoft`, `update`, `trusted`, `credential`, `network`, `vpn`…

---

## 💾 Data & Privacy

- **No data leaves your machine.** All data is stored locally in `data/ramguard.db`.
- Logs are saved to `logs/ramguard_YYYYMMDD.log`.
- No telemetry, no cloud sync, no external connections.

---

## ⚙ Configuration

Edit `config/config.json` or use the in-app Settings page:

```json
{
    "app_name": "RAMGuard",
    "version": "1.0.0",
    "theme": "dark",
    "monitoring_interval_seconds": 3,
    "memory_warning_threshold_percent": 80,
    "memory_critical_threshold_percent": 90,
    "start_with_windows": false,
    "show_notifications": true,
    "default_optimization_mode": "SAFE",
    "min_memory_to_recommend_mb": 100,
    "max_history_entries": 100,
    "custom_protected_processes": [],
    "auto_refresh_process_list": true,
    "process_list_refresh_interval_seconds": 5
}
```

---

## 🧩 Architecture

RAMGuard follows an **MVC-style modular architecture**:

- **Model** → `core/` modules (process scanner, safety manager, optimizer)
- **View** → `ui/` pages (dashboard, applications, optimization, etc.)
- **Controller** → `ui/main_window.py` (orchestrates workers, signals, and page routing)

Background operations (monitoring, scanning, optimization) run on **QThread** workers to keep the UI responsive at all times.

---

## 📝 License

MIT License — Free for personal and educational use.

---

## ⚠ Disclaimer

RAMGuard helps manage user applications. It is **not** a RAM cleaner and does not manipulate physical memory directly. Optimization results depend on which applications you choose to close.

**SAFETY > OPTIMIZATION** — RAMGuard will always prefer doing nothing over risking system instability.

