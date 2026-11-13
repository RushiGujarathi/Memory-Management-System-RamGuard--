"""
RAMGuard OS Memory Management Lab
Interactive OS Architecture & Virtual Memory Laboratory.
Covers:
1. Memory Management Requirements (Relocation, Protection, Sharing, Logical/Physical Org)
2. Memory Partitioning (Fixed MFT vs Variable MVT)
3. Allocation Strategies (First Fit, Best Fit, Worst Fit, Next Fit)
4. Fragmentation & Compaction
5. Swapping (RAM <-> Backing Store)
6. Paging (Page Table, Frames, Logical to Physical Address Translation)
7. Segmentation (Base, Limit, SegFault Detection)
8. Virtual Memory, TLB & Effective Memory Access Time (EMAT)
9. Demand Paging & Page Replacement Algorithms (FIFO, LRU, Optimal, Clock, LFU, MFU)
10. Thrashing & Working Set Model
11. Buddy System (Binary Buddy Allocation & Coalescing)
12. Slab Allocation (Kernel Object Caches: Full, Partial, Empty Slabs)
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView,
    QLineEdit, QComboBox, QSpinBox, QSlider, QScrollArea,
    QProgressBar, QMessageBox, QGridLayout, QSizePolicy,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen

import psutil
from core.os_memory_core import (
    FixedPartitioningSystem, VariablePartitioningSystem, AllocationStrategy,
    SwappingSimulator, SwappedProcess, PagingSystem, SegmentationSystem, TLBSimulator,
    PageReplacementSimulator, ReplacementPolicy, ThrashingAnalyzer,
    BuddySystemAllocator, SlabAllocator, SlabState
)
from ui.styles import rgba
from utils.logger import get_logger

logger = get_logger("OSMemoryLab")


def _kpi_card(title: str, value: str, sub: str, color: str = "#38bdf8") -> QFrame:
    card = QFrame()
    card.setObjectName("card")
    card.setStyleSheet(f"""
        QFrame#card {{
            background-color: #0b1930;
            border: 1px solid rgba(59, 130, 246, 0.25);
            border-radius: 12px;
            padding: 12px 16px;
        }}
    """)
    lay = QVBoxLayout(card)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(4)

    t_lbl = QLabel(title)
    t_lbl.setStyleSheet("color:#8c9eb5; font-size:11px; font-weight:600; text-transform:uppercase;")
    v_lbl = QLabel(value)
    v_lbl.setStyleSheet(f"color:{color}; font-size:22px; font-weight:800;")
    s_lbl = QLabel(sub)
    s_lbl.setStyleSheet("color:#64748b; font-size:10px;")

    lay.addWidget(t_lbl)
    lay.addWidget(v_lbl)
    lay.addWidget(s_lbl)
    return card


class MemoryBarWidget(QWidget):
    """Custom painted bar rendering contiguous memory blocks and free holes."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.blocks: list[dict] = []
        self.total_memory: int = 1024
        self.setFixedHeight(54)

    def set_data(self, blocks: list[dict], total_mem: int):
        self.blocks = blocks
        self.total_memory = max(total_mem, 1)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Background track
        painter.setBrush(QColor("#071224"))
        painter.setPen(QPen(QColor("rgba(59, 130, 246, 0.3)"), 1))
        painter.drawRoundedRect(0, 0, w, h, 8, 8)

        if not self.blocks:
            return

        COLORS = ["#2563eb", "#10b981", "#8b5cf6", "#f59e0b", "#ec4899", "#06b6d4"]
        color_idx = 0

        for b in self.blocks:
            start_frac = b["start"] / self.total_memory
            size_frac = b["size"] / self.total_memory
            bx = int(start_frac * w)
            bw = max(int(size_frac * w), 3)

            if b["is_allocated"]:
                c = QColor(COLORS[color_idx % len(COLORS)])
                color_idx += 1
                painter.setBrush(c)
                painter.setPen(QPen(QColor("#ffffff"), 0.5))
                painter.drawRoundedRect(bx + 1, 2, bw - 2, h - 4, 4, 4)

                # Text label
                painter.setPen(QColor("#ffffff"))
                font = painter.font()
                font.setPointSize(9)
                font.setBold(True)
                painter.setFont(font)
                lbl = f"{b['name']} ({b['size']}K)"
                if bw > 55:
                    painter.drawText(bx, 0, bw, h, Qt.AlignmentFlag.AlignCenter, lbl)
            else:
                # Free hole
                painter.setBrush(QColor("rgba(148, 163, 184, 0.08)"))
                painter.setPen(QPen(QColor("rgba(148, 163, 184, 0.25)"), 1, Qt.PenStyle.DashLine))
                painter.drawRoundedRect(bx + 1, 2, bw - 2, h - 4, 4, 4)

                painter.setPen(QColor("#94a3b8"))
                font = painter.font()
                font.setPointSize(8)
                font.setBold(False)
                painter.setFont(font)
                lbl = f"Free: {b['size']}K"
                if bw > 50:
                    painter.drawText(bx, 0, bw, h, Qt.AlignmentFlag.AlignCenter, lbl)


class OSMemoryLabPage(QWidget):
    """Complete OS Memory Management & Architecture Laboratory."""

    def __init__(self, parent=None):
        super().__init__(parent)
        # Simulation Engines
        self.fixed_sys = FixedPartitioningSystem()
        self.var_sys = VariablePartitioningSystem(total_memory_kb=1024)
        self.swapping_sys = SwappingSimulator()
        self.paging_sys = PagingSystem()
        self.seg_sys = SegmentationSystem()
        self.buddy_sys = BuddySystemAllocator(total_memory_kb=1024)
        self.slab_sys = SlabAllocator()

        # Prepopulate sample processes in variable system
        self.var_sys.allocate("OS_Kernel", 128, AllocationStrategy.FIRST_FIT)
        self.var_sys.allocate("Process_A", 200, AllocationStrategy.FIRST_FIT)
        self.var_sys.allocate("Process_B", 150, AllocationStrategy.FIRST_FIT)
        self.var_sys.deallocate("Process_A")  # Leaves a hole to demonstrate fragmentation

        # Swapping sample
        self.swapping_sys.ram_processes["Chrome.exe"] = SwappedProcess(101, "Chrome.exe", 320.0, "RAM")
        self.swapping_sys.ram_processes["VSCode.exe"] = SwappedProcess(102, "VSCode.exe", 240.0, "RAM")
        self.swapping_sys.backing_store["Spotify.exe"] = SwappedProcess(103, "Spotify.exe", 180.0, "BACKING_STORE")

        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(28, 20, 28, 20)
        root.setSpacing(14)

        # ── Header ──
        hdr = QHBoxLayout()
        hdr.setSpacing(12)

        icon_lbl = QLabel("🧠")
        icon_lbl.setStyleSheet("font-size:28px;")

        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title = QLabel("OS Memory Management & Architecture Lab")
        title.setStyleSheet("font-size:24px; font-weight:800; color:#ffffff; letter-spacing:-0.3px;")
        sub = QLabel("Interactive simulators for Main Memory, Virtual Memory, Paging, Segmentation, Replacement, and Kernel Allocators")
        sub.setStyleSheet("font-size:12px; color:#8c9eb5;")
        title_col.addWidget(title)
        title_col.addWidget(sub)

        hdr.addWidget(icon_lbl)
        hdr.addLayout(title_col)
        hdr.addStretch()
        root.addLayout(hdr)

        # ── Tabbed Interface ──
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet("""
            QTabWidget::pane {
                border: 1px solid rgba(59, 130, 246, 0.25);
                background-color: #071324;
                border-radius: 12px;
                padding: 14px;
            }
            QTabBar::tab {
                background: #0b1930;
                color: #8c9eb5;
                padding: 10px 20px;
                margin-right: 6px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                font-weight: 600;
                font-size: 12px;
            }
            QTabBar::tab:selected {
                background: #1e3a8a;
                color: #ffffff;
                border-bottom: 2px solid #38bdf8;
            }
            QTabBar::tab:hover {
                background: #122544;
                color: #e2e8f0;
            }
        """)

        # Add all 5 specialized tabs
        self.tabs.addTab(self._build_main_memory_tab(), "🧩 1. Main Memory & Allocation")
        self.tabs.addTab(self._build_paging_seg_tab(), "📑 2. Paging & Segmentation")
        self.tabs.addTab(self._build_virtual_mem_tab(), "⚡ 3. Virtual Memory & Replacement")
        self.tabs.addTab(self._build_buddy_slab_tab(), "🌳 4. Buddy System & Slab")
        self.tabs.addTab(self._build_theory_guide_tab(), "📚 5. OS Memory Guide & Architecture")

        root.addWidget(self.tabs, 1)

    # =========================================================================
    # TAB 1: MAIN MEMORY, PARTITIONING, ALLOCATION STRATEGIES, FRAGMENTATION & SWAPPING
    # =========================================================================
    def _build_main_memory_tab(self) -> QWidget:
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setSpacing(14)

        # Top Control Row
        ctrl_card = QFrame()
        ctrl_card.setObjectName("card")
        ctrl_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.2); border-radius:10px; padding:12px; }")
        cc_lay = QHBoxLayout(ctrl_card)
        cc_lay.setSpacing(12)

        # Strategy selector
        cc_lay.addWidget(QLabel("Allocation Strategy:"))
        self.strat_combo = QComboBox()
        self.strat_combo.addItems(["First Fit", "Best Fit", "Worst Fit", "Next Fit"])
        self.strat_combo.setFixedHeight(34)
        cc_lay.addWidget(self.strat_combo)

        cc_lay.addWidget(QLabel("Process Name:"))
        self.proc_name_input = QLineEdit("Process_C")
        self.proc_name_input.setFixedWidth(100)
        self.proc_name_input.setFixedHeight(34)
        cc_lay.addWidget(self.proc_name_input)

        cc_lay.addWidget(QLabel("Size (KB):"))
        self.proc_size_input = QSpinBox()
        self.proc_size_input.setRange(16, 1024)
        self.proc_size_input.setValue(180)
        self.proc_size_input.setFixedHeight(34)
        cc_lay.addWidget(self.proc_size_input)

        alloc_btn = QPushButton("✓ Allocate")
        alloc_btn.setObjectName("optimize_btn")
        alloc_btn.setFixedHeight(34)
        alloc_btn.clicked.connect(self._on_allocate_variable)
        cc_lay.addWidget(alloc_btn)

        dealloc_btn = QPushButton("✕ Deallocate")
        dealloc_btn.setObjectName("secondary_btn")
        dealloc_btn.setFixedHeight(34)
        dealloc_btn.clicked.connect(self._on_deallocate_variable)
        cc_lay.addWidget(dealloc_btn)

        compact_btn = QPushButton("🗜 Compact Memory")
        compact_btn.setStyleSheet("background:#7c3aed; color:#ffffff; font-weight:700; border-radius:6px; padding:6px 14px;")
        compact_btn.setFixedHeight(34)
        compact_btn.clicked.connect(self._on_compact_memory)
        cc_lay.addWidget(compact_btn)

        layout.addWidget(ctrl_card)

        # Memory Map Bar Visualizer
        v_title = QLabel("Main Memory Physical Layout (1024 KB Total):")
        v_title.setStyleSheet("color:#ffffff; font-weight:700; font-size:13px;")
        layout.addWidget(v_title)

        self.mem_bar = MemoryBarWidget()
        layout.addWidget(self.mem_bar)

        # Status output
        self.alloc_status_lbl = QLabel("Ready. Select an allocation strategy and click Allocate.")
        self.alloc_status_lbl.setStyleSheet("color:#38bdf8; font-size:12px; font-weight:600;")
        layout.addWidget(self.alloc_status_lbl)

        # Fragmentation KPI row
        kpi_row = QHBoxLayout()
        kpi_row.setSpacing(12)
        self.internal_frag_card = _kpi_card("Internal Fragmentation", "0 KB", "Fixed Partitioning (MFT) artifact", "#10b981")
        self.external_frag_card = _kpi_card("External Fragmentation", "0 KB", "Free scattered non-contiguous holes", "#f59e0b")
        self.total_free_card = _kpi_card("Total Free Space", "0 KB", "Available in RAM", "#38bdf8")
        kpi_row.addWidget(self.internal_frag_card)
        kpi_row.addWidget(self.external_frag_card)
        kpi_row.addWidget(self.total_free_card)
        layout.addLayout(kpi_row)

        # Swapping Section
        swap_box = QFrame()
        swap_box.setObjectName("card")
        swap_box.setStyleSheet("QFrame#card { background:#08162b; border:1px solid rgba(59,130,246,0.2); border-radius:10px; padding:12px; }")
        sb_lay = QVBoxLayout(swap_box)
        sb_lay.setSpacing(10)

        sb_hdr = QHBoxLayout()
        sb_title = QLabel("🔄 Process Swapping Engine (Main Memory <-> Backing Store / Swap)")
        sb_title.setStyleSheet("font-size:14px; font-weight:700; color:#ffffff;")
        sb_hdr.addWidget(sb_title)
        sb_hdr.addStretch()

        # Live Windows swap metric
        try:
            sw = psutil.swap_memory()
            live_swap = f"Windows Pagefile: {sw.used / (1024**2):.0f} MB / {sw.total / (1024**2):.0f} MB ({sw.percent}%)"
        except Exception:
            live_swap = "Windows Pagefile: Active"
        sb_live = QLabel(live_swap)
        sb_live.setStyleSheet("color:#10b981; font-weight:700; font-size:11px;")
        sb_hdr.addWidget(sb_live)
        sb_lay.addLayout(sb_hdr)

        # Swapping dual list
        dual_row = QHBoxLayout()
        dual_row.setSpacing(14)

        # RAM resident
        ram_col = QVBoxLayout()
        ram_col.addWidget(QLabel("Resident in RAM (Fast Access):"))
        self.ram_list = QTableWidget()
        self.ram_list.setColumnCount(3)
        self.ram_list.setHorizontalHeaderLabels(["PID", "Process", "Size"])
        self.ram_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.ram_list.setFixedHeight(110)
        ram_col.addWidget(self.ram_list)

        swap_out_btn = QPushButton("⬇ Swap Out to Disk")
        swap_out_btn.setObjectName("secondary_btn")
        swap_out_btn.clicked.connect(self._on_swap_out)
        ram_col.addWidget(swap_out_btn)
        dual_row.addLayout(ram_col)

        # Backing Store
        swap_col = QVBoxLayout()
        swap_col.addWidget(QLabel("Backing Store / Pagefile (Swap Partition):"))
        self.swap_list = QTableWidget()
        self.swap_list.setColumnCount(3)
        self.swap_list.setHorizontalHeaderLabels(["PID", "Process", "Size"])
        self.swap_list.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.swap_list.setFixedHeight(110)
        swap_col.addWidget(self.swap_list)

        swap_in_btn = QPushButton("⬆ Swap In to RAM")
        swap_in_btn.setObjectName("secondary_btn")
        swap_in_btn.clicked.connect(self._on_swap_in)
        swap_col.addWidget(swap_in_btn)
        dual_row.addLayout(swap_col)

        sb_lay.addLayout(dual_row)
        layout.addWidget(swap_box)

        # Update visual display
        self._refresh_main_memory_display()
        return tab

    def _refresh_main_memory_display(self):
        blocks_data = []
        for b in self.var_sys.blocks:
            blocks_data.append({
                "start": b.start_address,
                "size": b.size_kb,
                "is_allocated": b.is_allocated,
                "name": b.process_name,
            })
        self.mem_bar.set_data(blocks_data, self.var_sys.total_memory_kb)

        # Update metrics
        total_free = sum(b.size_kb for b in self.var_sys.blocks if not b.is_allocated)
        free_blocks = [b.size_kb for b in self.var_sys.blocks if not b.is_allocated]
        ext_frag = total_free if len(free_blocks) > 1 else 0

        self.internal_frag_card.findChild(QLabel, "").setText(f"{self.fixed_sys.total_internal_fragmentation()} KB") if False else None
        # update kpi values directly
        self.external_frag_card.layout().itemAt(1).widget().setText(f"{ext_frag} KB")
        self.total_free_card.layout().itemAt(1).widget().setText(f"{total_free} KB")

        # Update swapping tables
        self.ram_list.setRowCount(len(self.swapping_sys.ram_processes))
        for r, (pname, p) in enumerate(self.swapping_sys.ram_processes.items()):
            self.ram_list.setItem(r, 0, QTableWidgetItem(str(p.pid)))
            self.ram_list.setItem(r, 1, QTableWidgetItem(p.name))
            self.ram_list.setItem(r, 2, QTableWidgetItem(f"{p.size_mb:.0f} MB"))

        self.swap_list.setRowCount(len(self.swapping_sys.backing_store))
        for r, (pname, p) in enumerate(self.swapping_sys.backing_store.items()):
            self.swap_list.setItem(r, 0, QTableWidgetItem(str(p.pid)))
            self.swap_list.setItem(r, 1, QTableWidgetItem(p.name))
            self.swap_list.setItem(r, 2, QTableWidgetItem(f"{p.size_mb:.0f} MB"))

    def _on_allocate_variable(self):
        strat_map = {
            "First Fit": AllocationStrategy.FIRST_FIT,
            "Best Fit": AllocationStrategy.BEST_FIT,
            "Worst Fit": AllocationStrategy.WORST_FIT,
            "Next Fit": AllocationStrategy.NEXT_FIT,
        }
        strat = strat_map.get(self.strat_combo.currentText(), AllocationStrategy.FIRST_FIT)
        pname = self.proc_name_input.text().strip() or "Proc"
        size = self.proc_size_input.value()

        ok, msg, _ = self.var_sys.allocate(pname, size, strat)
        self.alloc_status_lbl.setText(msg)
        self.alloc_status_lbl.setStyleSheet(f"color:{'#10b981' if ok else '#ef4444'}; font-size:12px; font-weight:600;")
        self._refresh_main_memory_display()

    def _on_deallocate_variable(self):
        pname = self.proc_name_input.text().strip()
        ok, msg = self.var_sys.deallocate(pname)
        self.alloc_status_lbl.setText(msg)
        self.alloc_status_lbl.setStyleSheet(f"color:{'#10b981' if ok else '#f59e0b'}; font-size:12px; font-weight:600;")
        self._refresh_main_memory_display()

    def _on_compact_memory(self):
        freed, msg = self.var_sys.compact()
        self.alloc_status_lbl.setText(msg)
        self.alloc_status_lbl.setStyleSheet("color:#a855f7; font-size:12px; font-weight:600;")
        self._refresh_main_memory_display()

    def _on_swap_out(self):
        row = self.ram_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "Swapping", "Please select a process from the RAM list to swap out.")
            return
        pname = self.ram_list.item(row, 1).text()
        ok, msg = self.swapping_sys.swap_out(pname)
        self.alloc_status_lbl.setText(msg)
        self._refresh_main_memory_display()

    def _on_swap_in(self):
        row = self.swap_list.currentRow()
        if row < 0:
            QMessageBox.information(self, "Swapping", "Please select a process from the Backing Store to swap in.")
            return
        pname = self.swap_list.item(row, 1).text()
        ok, msg = self.swapping_sys.swap_in(pname)
        self.alloc_status_lbl.setText(msg)
        self._refresh_main_memory_display()

    # =========================================================================
    # TAB 2: PAGING & SEGMENTATION (ADDRESS TRANSLATION & MMU CHECKS)
    # =========================================================================
    def _build_paging_seg_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent; border:none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # ── Section A: Paging & Address Translation ──
        p_card = QFrame()
        p_card.setObjectName("card")
        p_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-radius:12px; padding:16px; }")
        pc_lay = QVBoxLayout(p_card)
        pc_lay.setSpacing(10)

        p_title = QLabel("📖 Paging Architecture & Logical-to-Physical Address Translation")
        p_title.setStyleSheet("font-size:16px; font-weight:700; color:#38bdf8;")
        p_sub = QLabel("Logical Address is split into Page Number (p) and Offset (d). Physical Address = (Frame Number * Page Size) + Offset.")
        p_sub.setStyleSheet("font-size:11px; color:#8c9eb5;")
        pc_lay.addWidget(p_title)
        pc_lay.addWidget(p_sub)

        # Translation interactive input
        t_row = QHBoxLayout()
        t_row.addWidget(QLabel("Page Size: 4096 Bytes (4 KB)"))
        t_row.addSpacing(16)
        t_row.addWidget(QLabel("Logical Address (Bytes):"))
        self.logical_addr_input = QSpinBox()
        self.logical_addr_input.setRange(0, 65535)
        self.logical_addr_input.setValue(9216)  # Page 2, Offset 1024
        self.logical_addr_input.setFixedWidth(120)
        self.logical_addr_input.setFixedHeight(34)
        t_row.addWidget(self.logical_addr_input)

        translate_btn = QPushButton("⚡ Translate Address")
        translate_btn.setObjectName("optimize_btn")
        translate_btn.setFixedHeight(34)
        translate_btn.clicked.connect(self._on_translate_paging)
        t_row.addWidget(translate_btn)
        t_row.addStretch()
        pc_lay.addLayout(t_row)

        self.paging_result_box = QLabel("Result: Click 'Translate Address' to view step-by-step arithmetic.")
        self.paging_result_box.setStyleSheet("background:#071224; border:1px solid rgba(59,130,246,0.2); border-radius:8px; padding:10px; color:#e2e8f0; font-family:Consolas, monospace; font-size:12px;")
        pc_lay.addWidget(self.paging_result_box)

        # Page Table View
        pc_lay.addWidget(QLabel("Current Page Table (Resident vs Non-Resident Pages):"))
        self.page_table_widget = QTableWidget()
        self.page_table_widget.setColumnCount(5)
        self.page_table_widget.setHorizontalHeaderLabels(["Page #", "Frame #", "Valid Bit", "Dirty Bit", "Protection"])
        self.page_table_widget.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.page_table_widget.setFixedHeight(140)
        pc_lay.addWidget(self.page_table_widget)
        self._refresh_page_table()

        layout.addWidget(p_card)

        # ── Section B: Segmentation & Protection ──
        s_card = QFrame()
        s_card.setObjectName("card")
        s_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-radius:12px; padding:16px; }")
        sc_lay = QVBoxLayout(s_card)
        sc_lay.setSpacing(10)

        s_title = QLabel("🛡 Segmentation & Hardware Memory Protection (SegFault Trap)")
        s_title.setStyleSheet("font-size:16px; font-weight:700; color:#10b981;")
        s_sub = QLabel("Logical Address = (Segment Number, Offset). The MMU hardware verifies Offset < Limit. If false, a SEGMENTATION FAULT is thrown!")
        s_sub.setStyleSheet("font-size:11px; color:#8c9eb5;")
        sc_lay.addWidget(s_title)
        sc_lay.addWidget(s_sub)

        # Translation row
        st_row = QHBoxLayout()
        st_row.addWidget(QLabel("Segment:"))
        self.seg_selector = QComboBox()
        self.seg_selector.addItems(["0: Code (Limit: 400)", "1: Data (Limit: 400)", "2: Heap (Limit: 500)", "3: Stack (Limit: 600)"])
        self.seg_selector.setFixedHeight(34)
        st_row.addWidget(self.seg_selector)

        st_row.addWidget(QLabel("Offset:"))
        self.seg_offset_input = QSpinBox()
        self.seg_offset_input.setRange(0, 1000)
        self.seg_offset_input.setValue(250)
        self.seg_offset_input.setFixedWidth(100)
        self.seg_offset_input.setFixedHeight(34)
        st_row.addWidget(self.seg_offset_input)

        seg_check_btn = QPushButton("🔍 Check Address & Bound")
        seg_check_btn.setObjectName("optimize_btn")
        seg_check_btn.setFixedHeight(34)
        seg_check_btn.clicked.connect(self._on_check_segment)
        st_row.addWidget(seg_check_btn)
        st_row.addStretch()
        sc_lay.addLayout(st_row)

        self.seg_result_box = QLabel("Result: Ready. Test valid offsets vs boundary violations (e.g. Offset 650 on Code).")
        self.seg_result_box.setStyleSheet("background:#071224; border:1px solid rgba(59,130,246,0.2); border-radius:8px; padding:10px; color:#e2e8f0; font-family:Consolas, monospace; font-size:12px;")
        sc_lay.addWidget(self.seg_result_box)

        layout.addWidget(s_card)
        scroll.setWidget(container)

        tab_lay = QVBoxLayout(tab)
        tab_lay.setContentsMargins(0, 0, 0, 0)
        tab_lay.addWidget(scroll)
        return tab

    def _refresh_page_table(self):
        self.page_table_widget.setRowCount(len(self.paging_sys.page_table))
        for r, (pnum, entry) in enumerate(self.paging_sys.page_table.items()):
            self.page_table_widget.setItem(r, 0, QTableWidgetItem(f"Page {pnum}"))
            f_str = f"Frame {entry.frame_number}" if entry.frame_number is not None else "— (On Disk)"
            self.page_table_widget.setItem(r, 1, QTableWidgetItem(f_str))
            v_item = QTableWidgetItem("1 (Resident)" if entry.valid else "0 (Page Fault)")
            v_item.setForeground(QColor("#10b981" if entry.valid else "#ef4444"))
            self.page_table_widget.setItem(r, 2, v_item)
            self.page_table_widget.setItem(r, 3, QTableWidgetItem("1 (Modified)" if entry.dirty else "0 (Clean)"))
            self.page_table_widget.setItem(r, 4, QTableWidgetItem(entry.protection))

    def _on_translate_paging(self):
        addr = self.logical_addr_input.value()
        res = self.paging_sys.translate(addr)
        if res["success"]:
            text = (f"✔ LOGICAL TO PHYSICAL TRANSLATION SUCCESSFUL:\n"
                    f"• Logical Address: {addr} Bytes\n"
                    f"• Page Number (p) = {addr} // 4096 = {res['page_number']}\n"
                    f"• Offset (d) = {addr} % 4096 = {res['offset']}\n"
                    f"• Page Table Lookup: Page {res['page_number']} -> Frame {res['frame_number']}\n"
                    f"• Physical Address = (Frame {res['frame_number']} * 4096) + Offset {res['offset']} = {res['physical_address']}")
            color = "#10b981"
        else:
            text = (f"✖ PAGE FAULT OCCURRED:\n"
                    f"• Logical Address: {addr} Bytes (Page {res.get('page', 0)}, Offset {res.get('offset', 0)})\n"
                    f"• Status: Page is NOT in Physical Memory (Valid bit = 0).\n"
                    f"• Action: MMU generates trap to OS kernel -> Demand Paging initiates disk I/O read.")
            color = "#ef4444"

        self.paging_result_box.setText(text)
        self.paging_result_box.setStyleSheet(f"background:#071224; border:1px solid {color}; border-radius:8px; padding:10px; color:{color}; font-family:Consolas, monospace; font-size:12px;")
        self._refresh_page_table()

    def _on_check_segment(self):
        seg_id = self.seg_selector.currentIndex()
        offset = self.seg_offset_input.value()
        res = self.seg_sys.translate(seg_id, offset)

        if res["success"]:
            text = (f"✔ VALID MEMORY ACCESS:\n"
                    f"• Segment: {res['segment'].name} (Base: {res['segment'].base_address}, Limit: {res['segment'].limit_length})\n"
                    f"• Check: Offset {offset} < Limit {res['segment'].limit_length} -> PASS\n"
                    f"• Physical Address = Base {res['segment'].base_address} + Offset {offset} = {res['physical_address']}")
            color = "#10b981"
        else:
            text = (f"🚨 CRITICAL SEGMENTATION FAULT (SIGSEGV / TRAP):\n"
                    f"• Segment: {res['segment'].name} (Base: {res['segment'].base_address}, Limit: {res['segment'].limit_length})\n"
                    f"• Check: Offset {offset} >= Limit {res['segment'].limit_length} -> FAILED!\n"
                    f"• Hardware MMU Trap triggered: Process access violation prevented.")
            color = "#ef4444"

        self.seg_result_box.setText(text)
        self.seg_result_box.setStyleSheet(f"background:#071224; border:1px solid {color}; border-radius:8px; padding:10px; color:{color}; font-family:Consolas, monospace; font-size:12px;")

    # =========================================================================
    # TAB 3: VIRTUAL MEMORY, PAGE REPLACEMENT, TLB/EMAT & THRASHING
    # =========================================================================
    def _build_virtual_mem_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent; border:none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # ── Section A: Page Replacement Algorithms Simulator ──
        pr_card = QFrame()
        pr_card.setObjectName("card")
        pr_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-radius:12px; padding:16px; }")
        pr_lay = QVBoxLayout(pr_card)
        pr_lay.setSpacing(12)

        pr_title = QLabel("🔄 Virtual Memory: Page Replacement Algorithms Simulator")
        pr_title.setStyleSheet("font-size:16px; font-weight:700; color:#38bdf8;")
        pr_lay.addWidget(pr_title)

        # Reference String Controls
        r_row = QHBoxLayout()
        r_row.addWidget(QLabel("Reference String:"))
        self.ref_string_input = QLineEdit("7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1")
        self.ref_string_input.setFixedHeight(34)
        r_row.addWidget(self.ref_string_input, 1)

        r_row.addWidget(QLabel("Frames:"))
        self.frames_spin = QSpinBox()
        self.frames_spin.setRange(2, 8)
        self.frames_spin.setValue(3)
        self.frames_spin.setFixedHeight(34)
        r_row.addWidget(self.frames_spin)

        r_row.addWidget(QLabel("Algorithm:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(["FIFO", "LRU", "Optimal", "Clock (Second Chance)", "LFU", "MFU"])
        self.algo_combo.setFixedHeight(34)
        r_row.addWidget(self.algo_combo)

        run_pr_btn = QPushButton("▶ Run Simulation")
        run_pr_btn.setObjectName("optimize_btn")
        run_pr_btn.setFixedHeight(34)
        run_pr_btn.clicked.connect(self._on_run_page_replacement)
        r_row.addWidget(run_pr_btn)

        compare_btn = QPushButton("📊 Compare All")
        compare_btn.setStyleSheet("background:#7c3aed; color:#ffffff; font-weight:700; border-radius:6px; padding:6px 14px;")
        compare_btn.setFixedHeight(34)
        compare_btn.clicked.connect(self._on_compare_all_algorithms)
        r_row.addWidget(compare_btn)

        pr_lay.addLayout(r_row)

        # Presets row
        preset_row = QHBoxLayout()
        preset_row.addWidget(QLabel("Presets:"))
        p1 = QPushButton("Standard Textbook (7,0,1,2...)")
        p1.setObjectName("secondary_btn")
        p1.clicked.connect(lambda: self.ref_string_input.setText("7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3, 2, 1, 2, 0, 1, 7, 0, 1"))
        preset_row.addWidget(p1)

        p2 = QPushButton("Belady's Anomaly (1,2,3,4,1,2,5...)")
        p2.setObjectName("secondary_btn")
        p2.clicked.connect(lambda: (self.ref_string_input.setText("1, 2, 3, 4, 1, 2, 5, 1, 2, 3, 4, 5"), self.frames_spin.setValue(3)))
        preset_row.addWidget(p2)

        p3 = QPushButton("High Locality (2,3,2,1,5,2,4,5...)")
        p3.setObjectName("secondary_btn")
        p3.clicked.connect(lambda: self.ref_string_input.setText("2, 3, 2, 1, 5, 2, 4, 5, 3, 2, 5, 2"))
        preset_row.addWidget(p3)
        preset_row.addStretch()
        pr_lay.addLayout(preset_row)

        # Summary KPIs
        kpi_pr = QHBoxLayout()
        self.kpi_faults = _kpi_card("Page Faults", "0", "Miss count", "#ef4444")
        self.kpi_hits = _kpi_card("Page Hits", "0", "Resident hits", "#10b981")
        self.kpi_fault_rate = _kpi_card("Fault Ratio", "0%", "Lower is better", "#f59e0b")
        self.kpi_hit_rate = _kpi_card("Hit Ratio", "0%", "Efficiency", "#38bdf8")
        kpi_pr.addWidget(self.kpi_faults)
        kpi_pr.addWidget(self.kpi_hits)
        kpi_pr.addWidget(self.kpi_fault_rate)
        kpi_pr.addWidget(self.kpi_hit_rate)
        pr_lay.addLayout(kpi_pr)

        # Step-by-Step Table
        self.pr_table = QTableWidget()
        self.pr_table.setFixedHeight(180)
        pr_lay.addWidget(self.pr_table)

        layout.addWidget(pr_card)

        # ── Section B: TLB & Caching (EMAT) ──
        tlb_card = QFrame()
        tlb_card.setObjectName("card")
        tlb_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-radius:12px; padding:16px; }")
        tc_lay = QVBoxLayout(tlb_card)
        tc_lay.setSpacing(10)

        tc_title = QLabel("⚡ TLB (Translation Lookaside Buffer) & Effective Memory Access Time (EMAT)")
        tc_title.setStyleSheet("font-size:16px; font-weight:700; color:#f59e0b;")
        tc_lay.addWidget(tc_title)

        tlb_row = QHBoxLayout()
        tlb_row.addWidget(QLabel("TLB Hit Ratio (%):"))
        self.tlb_hit_slider = QSlider(Qt.Orientation.Horizontal)
        self.tlb_hit_slider.setRange(50, 99)
        self.tlb_hit_slider.setValue(90)
        self.tlb_hit_slider.valueChanged.connect(self._on_tlb_changed)
        tlb_row.addWidget(self.tlb_hit_slider)

        self.tlb_hit_lbl = QLabel("90%")
        self.tlb_hit_lbl.setStyleSheet("color:#38bdf8; font-weight:700; min-width:40px;")
        tlb_row.addWidget(self.tlb_hit_lbl)

        tlb_row.addSpacing(20)
        tlb_row.addWidget(QLabel("TLB Access: 20 ns  |  RAM Access: 100 ns"))
        tc_lay.addLayout(tlb_row)

        self.emat_result_lbl = QLabel("EMAT: Calculating...")
        self.emat_result_lbl.setStyleSheet("color:#ffffff; font-weight:700; font-size:13px;")
        tc_lay.addWidget(self.emat_result_lbl)
        self._on_tlb_changed()

        layout.addWidget(tlb_card)

        # ── Section C: Thrashing & Working Set Model ──
        th_card = QFrame()
        th_card.setObjectName("card")
        th_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-radius:12px; padding:16px; }")
        thc_lay = QVBoxLayout(th_card)
        thc_lay.setSpacing(10)

        th_title = QLabel("⚠️ Thrashing & Working Set Model Analysis")
        th_title.setStyleSheet("font-size:16px; font-weight:700; color:#ef4444;")
        thc_lay.addWidget(th_title)

        th_sub = QLabel("When sum of Working Set Sizes > Total Available Physical Frames, system collapses into Thrashing where CPU utilization drops to zero.")
        th_sub.setStyleSheet("font-size:11px; color:#8c9eb5;")
        thc_lay.addWidget(th_sub)

        th_row = QHBoxLayout()
        th_row.addWidget(QLabel("Total Working Sets (WSS):"))
        self.wss_spin = QSpinBox()
        self.wss_spin.setRange(1, 20)
        self.wss_spin.setValue(12)
        self.wss_spin.setFixedHeight(34)
        th_row.addWidget(self.wss_spin)

        th_row.addWidget(QLabel("Available Physical Frames (D):"))
        self.d_frames_spin = QSpinBox()
        self.d_frames_spin.setRange(1, 20)
        self.d_frames_spin.setValue(8)
        self.d_frames_spin.setFixedHeight(34)
        th_row.addWidget(self.d_frames_spin)

        eval_th_btn = QPushButton("Evaluate Thrashing Risk")
        eval_th_btn.setObjectName("optimize_btn")
        eval_th_btn.setFixedHeight(34)
        eval_th_btn.clicked.connect(self._on_evaluate_thrashing)
        th_row.addWidget(eval_th_btn)
        th_row.addStretch()
        thc_lay.addLayout(th_row)

        self.thrash_result_lbl = QLabel("Thrashing Status: Click evaluate to compute CPU utilization impact.")
        self.thrash_result_lbl.setStyleSheet("background:#071224; border:1px solid rgba(239,68,68,0.3); border-radius:8px; padding:10px; color:#ef4444; font-weight:700;")
        thc_lay.addWidget(self.thrash_result_lbl)

        layout.addWidget(th_card)
        scroll.setWidget(container)

        tab_lay = QVBoxLayout(tab)
        tab_lay.setContentsMargins(0, 0, 0, 0)
        tab_lay.addWidget(scroll)

        # Run initial default simulation
        self._on_run_page_replacement()
        return tab

    def _parse_ref_string(self) -> list[int]:
        raw = self.ref_string_input.text()
        try:
            return [int(x.strip()) for x in raw.split(",") if x.strip()]
        except ValueError:
            return [7, 0, 1, 2, 0, 3, 0, 4, 2, 3]

    def _on_run_page_replacement(self):
        refs = self._parse_ref_string()
        frames = self.frames_spin.value()
        policy_name = self.algo_combo.currentText()

        policy_map = {
            "FIFO": ReplacementPolicy.FIFO,
            "LRU": ReplacementPolicy.LRU,
            "Optimal": ReplacementPolicy.OPTIMAL,
            "Clock (Second Chance)": ReplacementPolicy.CLOCK,
            "LFU": ReplacementPolicy.LFU,
            "MFU": ReplacementPolicy.MFU,
        }
        policy = policy_map.get(policy_name, ReplacementPolicy.FIFO)

        sim = PageReplacementSimulator(refs, frames)
        res = sim.simulate(policy)

        # Update KPIs
        self.kpi_faults.layout().itemAt(1).widget().setText(str(res["page_faults"]))
        self.kpi_hits.layout().itemAt(1).widget().setText(str(res["hits"]))
        self.kpi_fault_rate.layout().itemAt(1).widget().setText(f"{res['fault_ratio_percent']:.1f}%")
        self.kpi_hit_rate.layout().itemAt(1).widget().setText(f"{res['hit_ratio_percent']:.1f}%")

        # Populate Step Matrix Table
        steps = res["steps"]
        cols = ["Step", "Page Ref"] + [f"Frame #{f}" for f in range(frames)] + ["Status", "Note"]
        self.pr_table.setColumnCount(len(cols))
        self.pr_table.setHorizontalHeaderLabels(cols)
        self.pr_table.setRowCount(len(steps))

        for r, step in enumerate(steps):
            self.pr_table.setItem(r, 0, QTableWidgetItem(str(step.step_number)))
            self.pr_table.setItem(r, 1, QTableWidgetItem(str(step.page)))
            for f in range(frames):
                val = str(step.frames[f]) if step.frames[f] is not None else "—"
                self.pr_table.setItem(r, 2 + f, QTableWidgetItem(val))

            status_item = QTableWidgetItem("HIT" if step.is_hit else "FAULT")
            status_item.setForeground(QColor("#10b981" if step.is_hit else "#ef4444"))
            status_item.setFont(QFont("Segoe UI", 9, QFont.Weight.Bold))
            self.pr_table.setItem(r, 2 + frames, status_item)
            self.pr_table.setItem(r, 3 + frames, QTableWidgetItem(step.note))

        self.pr_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)

    def _on_compare_all_algorithms(self):
        refs = self._parse_ref_string()
        frames = self.frames_spin.value()
        sim = PageReplacementSimulator(refs, frames)
        results = sim.compare_all()

        msg = "📊 Page Replacement Performance Comparison:\n\n"
        for r in results:
            msg += f"• {r['algorithm']}: {r['page_faults']} Faults | {r['hits']} Hits | Fault Rate: {r['fault_ratio_percent']:.1f}%\n"
        msg += f"\nTotal Page References: {len(refs)} | Number of Frames: {frames}"
        QMessageBox.information(self, "Algorithm Benchmark Comparison", msg)

    def _on_tlb_changed(self):
        hit_ratio = self.tlb_hit_slider.value() / 100.0
        self.tlb_hit_lbl.setText(f"{int(hit_ratio * 100)}%")
        res = TLBSimulator.calculate_emat(hit_ratio, tlb_access_ns=20.0, ram_access_ns=100.0)
        self.emat_result_lbl.setText(
            f"Effective Memory Access Time (EMAT) = {res['emat_ns']:.1f} ns   |   "
            f"Slowdown vs Pure RAM: {res['slowdown_factor']:.2f}x   (Without TLB: 200 ns)"
        )

    def _on_evaluate_thrashing(self):
        wss = self.wss_spin.value()
        frames = self.d_frames_spin.value()
        res = ThrashingAnalyzer.evaluate_thrashing_risk(wss, frames)
        self.thrash_result_lbl.setText(
            f"Status: {res['status']}   |   WSS / Frames Ratio: {res['wss_to_frames_ratio']:.2f}   |   "
            f"CPU Utilization: {res['estimated_cpu_utilization']:.0f}%\n"
            f"Recommendation: {res['recommendation']}"
        )
        color = "#10b981" if "OPTIMAL" in res["status"] else "#ef4444"
        self.thrash_result_lbl.setStyleSheet(f"background:#071224; border:1px solid {color}; border-radius:8px; padding:10px; color:{color}; font-weight:700;")

    # =========================================================================
    # TAB 4: BUDDY SYSTEM & SLAB ALLOCATION (KERNEL MEMORY MANAGEMENT)
    # =========================================================================
    def _build_buddy_slab_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent; border:none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        # ── Section A: Binary Buddy System Allocator ──
        b_card = QFrame()
        b_card.setObjectName("card")
        b_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-radius:12px; padding:16px; }")
        bc_lay = QVBoxLayout(b_card)
        bc_lay.setSpacing(12)

        b_title = QLabel("🌳 Binary Buddy System Allocator (Powers-of-2 Splitting & Coalescing)")
        b_title.setStyleSheet("font-size:16px; font-weight:700; color:#38bdf8;")
        b_sub = QLabel("Allocates memory in power-of-2 blocks. When free, adjacent buddy blocks are automatically merged (coalesced).")
        b_sub.setStyleSheet("font-size:11px; color:#8c9eb5;")
        bc_lay.addWidget(b_title)
        bc_lay.addWidget(b_sub)

        # Buddy controls
        bc_ctrl = QHBoxLayout()
        bc_ctrl.addWidget(QLabel("Process Name:"))
        self.buddy_proc_input = QLineEdit("Task_1")
        self.buddy_proc_input.setFixedWidth(100)
        self.buddy_proc_input.setFixedHeight(34)
        bc_ctrl.addWidget(self.buddy_proc_input)

        bc_ctrl.addWidget(QLabel("Request Size (KB):"))
        self.buddy_size_input = QSpinBox()
        self.buddy_size_input.setRange(16, 512)
        self.buddy_size_input.setValue(70)  # Fits into 128 KB buddy
        self.buddy_size_input.setFixedHeight(34)
        bc_ctrl.addWidget(self.buddy_size_input)

        b_alloc_btn = QPushButton("✓ Buddy Allocate")
        b_alloc_btn.setObjectName("optimize_btn")
        b_alloc_btn.setFixedHeight(34)
        b_alloc_btn.clicked.connect(self._on_buddy_allocate)
        bc_ctrl.addWidget(b_alloc_btn)

        b_dealloc_btn = QPushButton("✕ Buddy Free (Coalesce)")
        b_dealloc_btn.setObjectName("secondary_btn")
        b_dealloc_btn.setFixedHeight(34)
        b_dealloc_btn.clicked.connect(self._on_buddy_deallocate)
        bc_ctrl.addWidget(b_dealloc_btn)
        bc_ctrl.addStretch()
        bc_lay.addLayout(bc_ctrl)

        self.buddy_status_lbl = QLabel("Ready. Try allocating 70 KB to observe power-of-2 splitting into a 128 KB buddy block.")
        self.buddy_status_lbl.setStyleSheet("color:#38bdf8; font-weight:600;")
        bc_lay.addWidget(self.buddy_status_lbl)

        # Buddy Blocks visual table
        bc_lay.addWidget(QLabel("Current Buddy Memory Blocks:"))
        self.buddy_table = QTableWidget()
        self.buddy_table.setColumnCount(5)
        self.buddy_table.setHorizontalHeaderLabels(["Start Address", "Block Size", "Status", "Process", "Internal Frag"])
        self.buddy_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.buddy_table.setFixedHeight(140)
        bc_lay.addWidget(self.buddy_table)
        self._refresh_buddy_table()

        layout.addWidget(b_card)

        # ── Section B: Slab Allocation (Kernel Object Caches) ──
        s_card = QFrame()
        s_card.setObjectName("card")
        s_card.setStyleSheet("QFrame#card { background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-radius:12px; padding:16px; }")
        sc_lay = QVBoxLayout(s_card)
        sc_lay.setSpacing(12)

        s_title = QLabel("🧱 Slab Allocation (Linux/Windows Kernel Object Caches)")
        s_title.setStyleSheet("font-size:16px; font-weight:700; color:#10b981;")
        s_sub = QLabel("Slab caches store pre-allocated memory for frequent kernel objects (task_struct, mm_struct, inodes) with zero internal/external fragmentation.")
        s_sub.setStyleSheet("font-size:11px; color:#8c9eb5;")
        sc_lay.addWidget(s_title)
        sc_lay.addWidget(s_sub)

        # Slab controls
        slab_ctrl = QHBoxLayout()
        slab_ctrl.addWidget(QLabel("Kernel Object Cache:"))
        self.slab_cache_combo = QComboBox()
        self.slab_cache_combo.addItems(list(self.slab_sys.caches.keys()))
        self.slab_cache_combo.setFixedHeight(34)
        self.slab_cache_combo.currentIndexChanged.connect(self._refresh_slab_display)
        slab_ctrl.addWidget(self.slab_cache_combo)

        alloc_obj_btn = QPushButton("➕ Allocate Object (O(1))")
        alloc_obj_btn.setObjectName("optimize_btn")
        alloc_obj_btn.setFixedHeight(34)
        alloc_obj_btn.clicked.connect(self._on_slab_allocate)
        slab_ctrl.addWidget(alloc_obj_btn)

        free_obj_btn = QPushButton("➖ Free Object")
        free_obj_btn.setObjectName("secondary_btn")
        free_obj_btn.setFixedHeight(34)
        free_obj_btn.clicked.connect(self._on_slab_free)
        slab_ctrl.addWidget(free_obj_btn)
        slab_ctrl.addStretch()
        sc_lay.addLayout(slab_ctrl)

        self.slab_status_lbl = QLabel("Ready. Allocate objects to watch slabs transition between Empty -> Partial -> Full.")
        self.slab_status_lbl.setStyleSheet("color:#10b981; font-weight:600;")
        sc_lay.addWidget(self.slab_status_lbl)

        # Slab Table
        self.slab_table = QTableWidget()
        self.slab_table.setColumnCount(5)
        self.slab_table.setHorizontalHeaderLabels(["Slab #", "Object Size", "Objects Used", "Capacity", "Slab State"])
        self.slab_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.slab_table.setFixedHeight(140)
        sc_lay.addWidget(self.slab_table)
        self._refresh_slab_display()

        layout.addWidget(s_card)
        scroll.setWidget(container)

        tab_lay = QVBoxLayout(tab)
        tab_lay.setContentsMargins(0, 0, 0, 0)
        tab_lay.addWidget(scroll)
        return tab

    def _refresh_buddy_table(self):
        leaves = self.buddy_sys.get_leaf_blocks()
        self.buddy_table.setRowCount(len(leaves))
        for r, node in enumerate(leaves):
            self.buddy_table.setItem(r, 0, QTableWidgetItem(f"{node.address} KB"))
            self.buddy_table.setItem(r, 1, QTableWidgetItem(f"{node.size_kb} KB"))
            status = "Allocated" if node.is_allocated else "Free (Available)"
            st_item = QTableWidgetItem(status)
            st_item.setForeground(QColor("#10b981" if node.is_allocated else "#38bdf8"))
            self.buddy_table.setItem(r, 2, st_item)
            self.buddy_table.setItem(r, 3, QTableWidgetItem(node.process_name if node.is_allocated else "—"))
            self.buddy_table.setItem(r, 4, QTableWidgetItem("Power-of-2 fitting"))

    def _on_buddy_allocate(self):
        pname = self.buddy_proc_input.text().strip() or "Task"
        size = self.buddy_size_input.value()
        ok, msg = self.buddy_sys.allocate(pname, size)
        self.buddy_status_lbl.setText(msg)
        self.buddy_status_lbl.setStyleSheet(f"color:{'#10b981' if ok else '#ef4444'}; font-weight:600;")
        self._refresh_buddy_table()

    def _on_buddy_deallocate(self):
        pname = self.buddy_proc_input.text().strip()
        ok, msg = self.buddy_sys.deallocate(pname)
        self.buddy_status_lbl.setText(msg)
        self.buddy_status_lbl.setStyleSheet(f"color:{'#10b981' if ok else '#f59e0b'}; font-weight:600;")
        self._refresh_buddy_table()

    def _refresh_slab_display(self):
        cache_name = self.slab_cache_combo.currentText()
        cache = self.slab_sys.caches.get(cache_name)
        if not cache:
            return

        self.slab_table.setRowCount(len(cache.slabs))
        for r, slab in enumerate(cache.slabs):
            self.slab_table.setItem(r, 0, QTableWidgetItem(f"Slab #{slab.slab_id}"))
            self.slab_table.setItem(r, 1, QTableWidgetItem(f"{slab.object_size_bytes} Bytes"))
            self.slab_table.setItem(r, 2, QTableWidgetItem(f"{slab.allocated_count}"))
            self.slab_table.setItem(r, 3, QTableWidgetItem(f"{slab.objects_per_slab}"))

            state_item = QTableWidgetItem(slab.state.value)
            if slab.state == SlabState.FULL:
                state_item.setForeground(QColor("#ef4444"))
            elif slab.state == SlabState.PARTIAL:
                state_item.setForeground(QColor("#f59e0b"))
            else:
                state_item.setForeground(QColor("#10b981"))
            self.slab_table.setItem(r, 4, state_item)

    def _on_slab_allocate(self):
        cache_name = self.slab_cache_combo.currentText()
        cache = self.slab_sys.caches.get(cache_name)
        if cache:
            ok, msg, _ = cache.allocate_object()
            self.slab_status_lbl.setText(msg)
            self._refresh_slab_display()

    def _on_slab_free(self):
        cache_name = self.slab_cache_combo.currentText()
        cache = self.slab_sys.caches.get(cache_name)
        if cache:
            ok, msg = cache.free_object()
            self.slab_status_lbl.setText(msg)
            self._refresh_slab_display()

    # =========================================================================
    # TAB 5: OS MEMORY THEORY & REQUIREMENTS GUIDE
    # =========================================================================
    def _build_theory_guide_tab(self) -> QWidget:
        tab = QWidget()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("background:transparent; border:none;")

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setSpacing(16)

        guide_cards = [
            ("1. Five Requirements of Memory Management", [
                "• Relocation: Program can be loaded into any physical memory address; dynamic address binding using Base/Relocation registers.",
                "• Protection: Hardware MMU checks limit/base registers so processes cannot write outside their address boundaries.",
                "• Sharing: Allows multiple processes to share the same code copy (e.g. C runtime, kernel32.dll, shared memory pages).",
                "• Logical Organisation: Linear 1D addresses vs modules/segments (code, data, stack, heap).",
                "• Physical Organisation: Seamless multi-level movement between fast RAM and secondary storage (Backing store / Pagefile)."
            ], "#38bdf8"),

            ("2. Memory Partitioning: Fixed vs Variable", [
                "• Fixed Partitioning (MFT): Memory divided into static partitions at boot. Leads to INTERNAL FRAGMENTATION (wasted space inside partition).",
                "• Variable Partitioning (MVT): Memory allocated dynamically to exact process size. Leads to EXTERNAL FRAGMENTATION (free space split into small non-contiguous holes).",
                "• Memory Compaction: Relocates resident processes to collect external fragments into one contiguous block."
            ], "#10b981"),

            ("3. Allocation Strategies Comparison", [
                "• First Fit: Allocates the first free hole that is large enough. Fast search, low overhead.",
                "• Best Fit: Allocates the smallest free hole large enough. Minimizes immediate wastage, but leaves tiny unusable leftover holes.",
                "• Worst Fit: Allocates the largest free hole. Leaves the largest residual hole, but quickly destroys large contiguous blocks."
            ], "#f59e0b"),

            ("4. Paging, Segmentation & Virtual Memory", [
                "• Paging: Physical memory divided into Frames, logical memory divided into Pages. Completely eliminates external fragmentation.",
                "• Segmentation: User-view modular division (Code, Data, Stack). Hardware base and limit checks throw Segmentation Faults on overflow.",
                "• Virtual Memory & Demand Paging: Separates logical and physical memory. Brings pages into RAM only when referenced via Page Fault interrupts."
            ], "#8b5cf6"),

            ("5. Buddy System & Slab Allocation (Kernel Level)", [
                "• Buddy System: Binary power-of-2 allocation. Fast block splitting and coalescing with low external fragmentation.",
                "• Slab Allocation: High-speed kernel cache of pre-allocated objects (task_struct, inodes) with zero fragmentation and O(1) allocation."
            ], "#ec4899"),

            ("6. How RAMGuard Connects to Operating System Principles", [
                "• RAMGuard inspects process Working Sets (resident pages loaded in RAM).",
                "• During Optimization, RAMGuard commands Windows Memory Manager to trim working sets (EmptyWorkingSet), releasing physical frames back to the OS pool and paging inactive memory to pagefile.sys."
            ], "#06b6d4"),
        ]

        for title, points, color in guide_cards:
            card = QFrame()
            card.setObjectName("card")
            card.setStyleSheet(f"QFrame#card {{ background:#0b1930; border:1px solid rgba(59,130,246,0.25); border-left:4px solid {color}; border-radius:10px; padding:14px; }}")
            c_lay = QVBoxLayout(card)
            c_lay.setSpacing(6)

            t_lbl = QLabel(title)
            t_lbl.setStyleSheet(f"color:{color}; font-size:14px; font-weight:700;")
            c_lay.addWidget(t_lbl)

            for p in points:
                p_lbl = QLabel(p)
                p_lbl.setStyleSheet("color:#cbd5e1; font-size:11px; line-height:1.4;")
                p_lbl.setWordWrap(True)
                c_lay.addWidget(p_lbl)

            layout.addWidget(card)

        scroll.setWidget(container)
        tab_lay = QVBoxLayout(tab)
        tab_lay.setContentsMargins(0, 0, 0, 0)
        tab_lay.addWidget(scroll)
        return tab
