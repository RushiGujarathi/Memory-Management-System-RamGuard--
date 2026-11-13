"""
RAMGuard OS Memory Management Core Module
Comprehensive theoretical & simulation engine implementing core Operating System
Memory Management and Virtual Memory concepts:

1. Memory Management Requirements (Relocation, Protection, Sharing, Logical/Physical Organisation)
2. Memory Partitioning (Fixed MFT & Variable MVT)
3. Allocation Strategies (First Fit, Best Fit, Worst Fit, Next Fit)
4. Fragmentation (Internal, External) & Memory Compaction
5. Swapping (RAM <-> Backing Store / Swap)
6. Paging (Page Table, Frames, Address Translation)
7. Segmentation (Segments, Base, Limit, SegFault Detection)
8. Virtual Memory & Caching (TLB, Hierarchy, EMAT)
9. Demand Paging & Page Replacement (FIFO, LRU, Optimal, Clock, LFU, MFU)
10. Thrashing & Working Set Model
11. Buddy System Allocation (Binary Buddy System: Splitting & Coalescing)
12. Slab Allocation (Kernel Object Caches: Full, Partial, Empty Slabs)
"""

from dataclasses import dataclass, field
from enum import Enum
import math
from typing import List, Dict, Tuple, Optional, Any


# ============================================================================
# 1. MEMORY MANAGEMENT REQUIREMENTS & HARDWARE REGISTERS
# ============================================================================

@dataclass
class HardwareRegisters:
    """
    Simulates Base Register, Limit Register, and Relocation Register used for
    Relocation and Hardware Memory Protection.
    """
    base_register: int = 0
    limit_register: int = 0
    relocation_register: int = 0

    def check_and_translate(self, logical_address: int) -> Tuple[bool, int, str]:
        """
        Hardware Protection Check:
        0 <= logical_address < limit_register
        Physical Address = logical_address + relocation_register (or base_register)
        """
        if logical_address < 0 or logical_address >= self.limit_register:
            return False, -1, f"TRAP: Memory Protection Violation! Address {logical_address} >= Limit {self.limit_register}"
        physical = logical_address + self.relocation_register
        return True, physical, f"Valid: Physical Address = {logical_address} + {self.relocation_register} = {physical}"


@dataclass
class SharedMemorySegment:
    """Represents a shared memory region (e.g. shared library or IPC shared memory)."""
    segment_id: str
    name: str
    size_kb: int
    authorized_pids: List[int] = field(default_factory=list)

    def can_access(self, pid: int) -> bool:
        return pid in self.authorized_pids


# ============================================================================
# 2. MEMORY PARTITIONING: FIXED (MFT) & VARIABLE (MVT)
# ============================================================================

class PartitionType(Enum):
    FIXED = "Fixed Partitioning (MFT)"
    VARIABLE = "Variable Partitioning (MVT)"


@dataclass
class MemoryPartition:
    id: int
    start_address: int
    size_kb: int
    is_allocated: bool = False
    process_name: str = ""
    allocated_size_kb: int = 0

    @property
    def internal_fragmentation_kb(self) -> int:
        if self.is_allocated:
            return max(0, self.size_kb - self.allocated_size_kb)
        return 0

    @property
    def free_space_kb(self) -> int:
        return 0 if self.is_allocated else self.size_kb


class FixedPartitioningSystem:
    """
    Fixed Partitioning (Multiprogramming with a Fixed Number of Tasks - MFT).
    Partitions are created at boot time and remain fixed.
    Characterized by Internal Fragmentation.
    """
    def __init__(self, partition_sizes_kb: Optional[List[int]] = None):
        sizes = partition_sizes_kb or [64, 128, 256, 512, 1024]
        self.partitions: List[MemoryPartition] = []
        addr = 0
        for i, s in enumerate(sizes):
            self.partitions.append(MemoryPartition(id=i, start_address=addr, size_kb=s))
            addr += s

    def allocate(self, process_name: str, requested_size_kb: int) -> Tuple[bool, str, Optional[int]]:
        # Look for the smallest available partition that fits (Best Fit for MFT)
        best_part = None
        for p in self.partitions:
            if not p.is_allocated and p.size_kb >= requested_size_kb:
                if best_part is None or p.size_kb < best_part.size_kb:
                    best_part = p

        if best_part is None:
            return False, f"Cannot allocate {requested_size_kb} KB: No free partition large enough.", None

        best_part.is_allocated = True
        best_part.process_name = process_name
        best_part.allocated_size_kb = requested_size_kb
        frag = best_part.internal_fragmentation_kb
        return True, f"Allocated to Partition #{best_part.id} ({best_part.size_kb} KB). Internal Fragmentation = {frag} KB", best_part.id

    def deallocate(self, process_name: str) -> bool:
        for p in self.partitions:
            if p.is_allocated and p.process_name == process_name:
                p.is_allocated = False
                p.process_name = ""
                p.allocated_size_kb = 0
                return True
        return False

    def total_internal_fragmentation(self) -> int:
        return sum(p.internal_fragmentation_kb for p in self.partitions)


# ============================================================================
# 3. DYNAMIC / VARIABLE PARTITIONING & ALLOCATION STRATEGIES
# ============================================================================

class AllocationStrategy(Enum):
    FIRST_FIT = "First Fit"
    BEST_FIT = "Best Fit"
    WORST_FIT = "Worst Fit"
    NEXT_FIT = "Next Fit"


@dataclass
class VariableBlock:
    start_address: int
    size_kb: int
    is_allocated: bool = False
    process_name: str = ""


class VariablePartitioningSystem:
    """
    Variable / Dynamic Partitioning (MVT).
    Partitions are created dynamically according to exact process requirements.
    Eliminates internal fragmentation, but suffers from External Fragmentation.
    Supports Compaction (Defragmentation).
    """
    def __init__(self, total_memory_kb: int = 1024):
        self.total_memory_kb = total_memory_kb
        self.blocks: List[VariableBlock] = [VariableBlock(0, total_memory_kb, is_allocated=False)]
        self.last_allocated_index: int = 0

    def allocate(self, process_name: str, size_kb: int, strategy: AllocationStrategy) -> Tuple[bool, str, List[int]]:
        """
        Allocates a process using First Fit, Best Fit, Worst Fit, or Next Fit.
        Returns: (success, message, inspected_hole_indices)
        """
        if size_kb <= 0:
            return False, "Requested size must be greater than 0 KB.", []

        free_indices = [i for i, b in enumerate(self.blocks) if not b.is_allocated and b.size_kb >= size_kb]
        inspected: List[int] = []

        target_index = -1

        if strategy == AllocationStrategy.FIRST_FIT:
            for i, b in enumerate(self.blocks):
                if not b.is_allocated:
                    inspected.append(i)
                    if b.size_kb >= size_kb:
                        target_index = i
                        break

        elif strategy == AllocationStrategy.BEST_FIT:
            # Smallest hole that is large enough
            best_diff = float("inf")
            for i, b in enumerate(self.blocks):
                if not b.is_allocated:
                    inspected.append(i)
                    if b.size_kb >= size_kb:
                        diff = b.size_kb - size_kb
                        if diff < best_diff:
                            best_diff = diff
                            target_index = i

        elif strategy == AllocationStrategy.WORST_FIT:
            # Largest available hole
            worst_size = -1
            for i, b in enumerate(self.blocks):
                if not b.is_allocated:
                    inspected.append(i)
                    if b.size_kb >= size_kb and b.size_kb > worst_size:
                        worst_size = b.size_kb
                        target_index = i

        elif strategy == AllocationStrategy.NEXT_FIT:
            n = len(self.blocks)
            start = self.last_allocated_index % n
            for step in range(n):
                idx = (start + step) % n
                b = self.blocks[idx]
                if not b.is_allocated:
                    inspected.append(idx)
                    if b.size_kb >= size_kb:
                        target_index = idx
                        self.last_allocated_index = idx
                        break

        if target_index == -1:
            # Check for external fragmentation:
            total_free = sum(b.size_kb for b in self.blocks if not b.is_allocated)
            if total_free >= size_kb:
                msg = (f"Allocation Failed due to EXTERNAL FRAGMENTATION! "
                       f"Total free memory = {total_free} KB >= requested {size_kb} KB, "
                       f"but no single contiguous hole is large enough. Run Compaction!")
            else:
                msg = f"Allocation Failed: Insufficient total memory (free={total_free} KB, requested={size_kb} KB)."
            return False, msg, inspected

        # Split the hole if larger than requested
        hole = self.blocks[target_index]
        remaining = hole.size_kb - size_kb

        hole.is_allocated = True
        hole.process_name = process_name
        hole.size_kb = size_kb

        if remaining > 0:
            new_hole = VariableBlock(
                start_address=hole.start_address + size_kb,
                size_kb=remaining,
                is_allocated=False,
            )
            self.blocks.insert(target_index + 1, new_hole)

        self.last_allocated_index = target_index
        return True, f"Successfully allocated {size_kb} KB to '{process_name}' at [{hole.start_address} - {hole.start_address + size_kb} KB] using {strategy.value}.", inspected

    def deallocate(self, process_name: str) -> Tuple[bool, str]:
        found = False
        for b in self.blocks:
            if b.is_allocated and b.process_name == process_name:
                b.is_allocated = False
                b.process_name = ""
                found = True

        if not found:
            return False, f"Process '{process_name}' not found."

        # Coalesce adjacent free holes
        self.merge_adjacent_free()
        return True, f"Process '{process_name}' deallocated and adjacent free blocks coalesced."

    def merge_adjacent_free(self) -> None:
        """Coalesces contiguous free memory holes into single blocks."""
        new_blocks: List[VariableBlock] = []
        for b in self.blocks:
            if new_blocks and not new_blocks[-1].is_allocated and not b.is_allocated:
                new_blocks[-1].size_kb += b.size_kb
            else:
                new_blocks.append(b)
        self.blocks = new_blocks

    def compact(self) -> Tuple[int, str]:
        """
        Memory Compaction: Shifts all allocated processes to the beginning of memory,
        consolidating all external fragments into one large contiguous free block.
        """
        allocated = [b for b in self.blocks if b.is_allocated]
        total_free = sum(b.size_kb for b in self.blocks if not b.is_allocated)

        new_blocks: List[VariableBlock] = []
        cur_addr = 0
        for b in allocated:
            b.start_address = cur_addr
            cur_addr += b.size_kb
            new_blocks.append(b)

        if total_free > 0:
            new_blocks.append(VariableBlock(
                start_address=cur_addr,
                size_kb=total_free,
                is_allocated=False,
            ))

        self.blocks = new_blocks
        return total_free, f"Compaction Complete: Consolidated {total_free} KB into one contiguous free hole at address {cur_addr} KB."


# ============================================================================
# 4. SWAPPING SIMULATOR
# ============================================================================

@dataclass
class SwappedProcess:
    pid: int
    name: str
    size_mb: float
    location: str  # "RAM" or "BACKING_STORE"
    priority: int = 1


class SwappingSimulator:
    """
    Swapping Simulator:
    Simulates swapping processes between Main Memory (RAM) and Backing Store (Swap/Disk).
    Connects with live Windows pagefile telemetry when available.
    """
    def __init__(self, ram_capacity_mb: float = 2048.0, swap_capacity_mb: float = 4096.0):
        self.ram_capacity_mb = ram_capacity_mb
        self.swap_capacity_mb = swap_capacity_mb
        self.ram_processes: Dict[str, SwappedProcess] = {}
        self.backing_store: Dict[str, SwappedProcess] = {}

    @property
    def ram_used_mb(self) -> float:
        return sum(p.size_mb for p in self.ram_processes.values())

    @property
    def swap_used_mb(self) -> float:
        return sum(p.size_mb for p in self.backing_store.values())

    def swap_out(self, process_name: str) -> Tuple[bool, str]:
        """Swap out a process from RAM to the Backing Store."""
        if process_name not in self.ram_processes:
            return False, f"Process '{process_name}' is not in RAM."

        proc = self.ram_processes[process_name]
        if self.swap_used_mb + proc.size_mb > self.swap_capacity_mb:
            return False, "Swap file / Backing Store is FULL! Cannot swap out."

        del self.ram_processes[process_name]
        proc.location = "BACKING_STORE"
        self.backing_store[process_name] = proc
        return True, f"Swapped OUT '{process_name}' ({proc.size_mb:.1f} MB) from RAM to Backing Store."

    def swap_in(self, process_name: str) -> Tuple[bool, str]:
        """Swap in a process from Backing Store into RAM."""
        if process_name not in self.backing_store:
            return False, f"Process '{process_name}' is not in Backing Store."

        proc = self.backing_store[process_name]
        if self.ram_used_mb + proc.size_mb > self.ram_capacity_mb:
            return False, f"Insufficient RAM ({self.ram_capacity_mb - self.ram_used_mb:.1f} MB free, needs {proc.size_mb:.1f} MB). Must swap out another process first."

        del self.backing_store[process_name]
        proc.location = "RAM"
        self.ram_processes[process_name] = proc
        return True, f"Swapped IN '{process_name}' ({proc.size_mb:.1f} MB) into RAM from Backing Store."


# ============================================================================
# 5. PAGING & ADDRESS TRANSLATION
# ============================================================================

@dataclass
class PageTableEntry:
    page_number: int
    frame_number: Optional[int]
    valid: bool = False
    dirty: bool = False
    referenced: bool = False
    protection: str = "r-x"


class PagingSystem:
    """
    Paging System & Logical-to-Physical Address Translation:
    Page Size = 2^k bytes.
    Logical Address = [ Page Number (p) | Offset (d) ]
    Physical Address = [ Frame Number (f) | Offset (d) ]
    """
    def __init__(self, page_size_bytes: int = 4096, num_pages: int = 16, num_frames: int = 8):
        self.page_size = page_size_bytes
        self.num_pages = num_pages
        self.num_frames = num_frames
        self.offset_bits = int(math.log2(page_size_bytes))

        # Page Table
        self.page_table: Dict[int, PageTableEntry] = {}
        # Prepopulate sample pages
        for p in range(num_pages):
            if p < num_frames // 2:
                self.page_table[p] = PageTableEntry(
                    page_number=p,
                    frame_number=(p * 2) % num_frames,
                    valid=True,
                    dirty=False,
                    referenced=True,
                )
            else:
                self.page_table[p] = PageTableEntry(
                    page_number=p,
                    frame_number=None,
                    valid=False,
                    dirty=False,
                    referenced=False,
                )

    def translate(self, logical_address: int) -> Dict[str, Any]:
        """Translates a logical address into a physical address with complete step breakdown."""
        page_num = logical_address // self.page_size
        offset = logical_address % self.page_size

        if page_num not in self.page_table:
            return {
                "success": False,
                "error": f"Invalid Logical Address: Page {page_num} exceeds Page Table bounds (Max: {self.num_pages - 1}).",
                "page": page_num,
                "offset": offset,
            }

        entry = self.page_table[page_num]
        if not entry.valid or entry.frame_number is None:
            return {
                "success": False,
                "page_fault": True,
                "error": f"PAGE FAULT! Page {page_num} is not currently resident in Physical Memory (Valid bit = 0). Demand paging required.",
                "page": page_num,
                "offset": offset,
            }

        physical_address = (entry.frame_number * self.page_size) + offset
        entry.referenced = True

        return {
            "success": True,
            "page_fault": False,
            "logical_address": logical_address,
            "page_number": page_num,
            "offset": offset,
            "frame_number": entry.frame_number,
            "physical_address": physical_address,
            "formula": f"Physical = (Frame {entry.frame_number} * {self.page_size}) + Offset {offset} = {physical_address}",
        }


# ============================================================================
# 6. SEGMENTATION & SEGMENT FAULT DETECTION
# ============================================================================

@dataclass
class SegmentTableEntry:
    segment_id: int
    name: str
    base_address: int
    limit_length: int
    access_rights: str = "Read/Write"


class SegmentationSystem:
    """
    Segmentation System:
    Programs divided into logical modules: Code, Data, Stack, Heap.
    Logical Address = [ Segment Number (s) | Offset (d) ]
    Hardware check: if offset >= limit -> Segmentation Fault!
    Else: Physical Address = Base + Offset.
    """
    def __init__(self):
        self.segments: Dict[int, SegmentTableEntry] = {
            0: SegmentTableEntry(0, "Code (Text)", base_address=1400, limit_length=400, access_rights="Read/Execute"),
            1: SegmentTableEntry(1, "Data (Globals)", base_address=6300, limit_length=400, access_rights="Read/Write"),
            2: SegmentTableEntry(2, "Heap (Dynamic)", base_address=4300, limit_length=500, access_rights="Read/Write"),
            3: SegmentTableEntry(3, "Stack (Call Frame)", base_address=3200, limit_length=600, access_rights="Read/Write"),
        }

    def translate(self, segment_id: int, offset: int) -> Dict[str, Any]:
        if segment_id not in self.segments:
            return {
                "success": False,
                "error": f"Invalid Segment ID {segment_id}. Allowed segments: 0..{len(self.segments)-1}.",
            }

        seg = self.segments[segment_id]
        if offset < 0 or offset >= seg.limit_length:
            return {
                "success": False,
                "segmentation_fault": True,
                "error": f"SEGMENTATION FAULT! Offset {offset} exceeds Segment '{seg.name}' Limit ({seg.limit_length}). Trap generated by Memory Management Unit (MMU).",
                "segment": seg,
                "offset": offset,
            }

        physical_address = seg.base_address + offset
        return {
            "success": True,
            "segmentation_fault": False,
            "segment": seg,
            "offset": offset,
            "physical_address": physical_address,
            "formula": f"Physical Address = Base ({seg.base_address}) + Offset ({offset}) = {physical_address}",
        }


# ============================================================================
# 7. VIRTUAL MEMORY, TLB & EFFECTIVE MEMORY ACCESS TIME (EMAT)
# ============================================================================

class TLBSimulator:
    """
    Translation Lookaside Buffer (TLB) & Cache Hierarchy:
    Computes Effective Memory Access Time (EMAT).
    Formula:
      EMAT = Hit_Ratio * (TLB_access + RAM_access) + (1 - Hit_Ratio) * (TLB_access + 2 * RAM_access)
    """
    @staticmethod
    def calculate_emat(
        hit_ratio: float,
        tlb_access_ns: float = 20.0,
        ram_access_ns: float = 100.0,
        page_table_levels: int = 1,
    ) -> Dict[str, float]:
        # If TLB Hit: TLB lookup + 1 RAM access to data
        t_hit = tlb_access_ns + ram_access_ns
        # If TLB Miss: TLB lookup + (levels * RAM access for page table) + 1 RAM access to data
        t_miss = tlb_access_ns + ((page_table_levels + 1) * ram_access_ns)
        emat = (hit_ratio * t_hit) + ((1.0 - hit_ratio) * t_miss)
        slowdown = emat / ram_access_ns
        return {
            "emat_ns": emat,
            "t_hit_ns": t_hit,
            "t_miss_ns": t_miss,
            "slowdown_factor": slowdown,
        }


# ============================================================================
# 8. DEMAND PAGING & PAGE REPLACEMENT POLICIES
# ============================================================================

class ReplacementPolicy(Enum):
    FIFO = "FIFO (First In First Out)"
    LRU = "LRU (Least Recently Used)"
    OPTIMAL = "Optimal (Belady's Optimal)"
    CLOCK = "Clock (Second Chance)"
    LFU = "LFU (Least Frequently Used)"
    MFU = "MFU (Most Frequently Used)"


@dataclass
class ReplacementStep:
    step_number: int
    page: int
    frames: List[Optional[int]]
    is_hit: bool
    victim_page: Optional[int] = None
    note: str = ""


class PageReplacementSimulator:
    """
    Simulates Page Replacement Policies:
    - FIFO
    - LRU
    - Optimal (MIN / Belady)
    - Clock (Second Chance)
    - LFU
    - MFU
    """
    def __init__(self, reference_string: List[int], num_frames: int):
        self.ref_string = reference_string
        self.num_frames = num_frames

    def simulate(self, policy: ReplacementPolicy) -> Dict[str, Any]:
        if policy == ReplacementPolicy.FIFO:
            return self._sim_fifo()
        elif policy == ReplacementPolicy.LRU:
            return self._sim_lru()
        elif policy == ReplacementPolicy.OPTIMAL:
            return self._sim_optimal()
        elif policy == ReplacementPolicy.CLOCK:
            return self._sim_clock()
        elif policy == ReplacementPolicy.LFU:
            return self._sim_lfu()
        elif policy == ReplacementPolicy.MFU:
            return self._sim_mfu()
        return self._sim_fifo()

    def _sim_fifo(self) -> Dict[str, Any]:
        frames: List[Optional[int]] = [None] * self.num_frames
        queue: List[int] = []
        steps: List[ReplacementStep] = []
        hits = 0
        faults = 0

        for i, page in enumerate(self.ref_string):
            if page in frames:
                hits += 1
                steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=True, note="Hit (page already in memory)"))
            else:
                faults += 1
                victim = None
                if None in frames:
                    idx = frames.index(None)
                    frames[idx] = page
                    queue.append(page)
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, note="Page Fault (empty frame loaded)"))
                else:
                    victim = queue.pop(0)
                    idx = frames.index(victim)
                    frames[idx] = page
                    queue.append(page)
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, victim_page=victim,
                                                 note=f"Page Fault (victim: Page {victim} replaced via FIFO)"))

        return self._package_result("FIFO", steps, hits, faults)

    def _sim_lru(self) -> Dict[str, Any]:
        frames: List[Optional[int]] = [None] * self.num_frames
        last_used: Dict[int, int] = {}
        steps: List[ReplacementStep] = []
        hits = 0
        faults = 0

        for i, page in enumerate(self.ref_string):
            if page in frames:
                hits += 1
                last_used[page] = i
                steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=True, note="Hit (recency updated)"))
            else:
                faults += 1
                victim = None
                if None in frames:
                    idx = frames.index(None)
                    frames[idx] = page
                    last_used[page] = i
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, note="Page Fault (empty frame loaded)"))
                else:
                    # Page with smallest last_used index
                    victim = min(frames, key=lambda p: last_used.get(p, -1))
                    idx = frames.index(victim)
                    frames[idx] = page
                    last_used[page] = i
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, victim_page=victim,
                                                 note=f"Page Fault (victim: Page {victim} least recently used)"))

        return self._package_result("LRU", steps, hits, faults)

    def _sim_optimal(self) -> Dict[str, Any]:
        frames: List[Optional[int]] = [None] * self.num_frames
        steps: List[ReplacementStep] = []
        hits = 0
        faults = 0

        for i, page in enumerate(self.ref_string):
            if page in frames:
                hits += 1
                steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=True, note="Hit (page resident)"))
            else:
                faults += 1
                victim = None
                if None in frames:
                    idx = frames.index(None)
                    frames[idx] = page
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, note="Page Fault (empty frame loaded)"))
                else:
                    # Find page in frames that won't be used for the longest time in future
                    future = self.ref_string[i + 1:]
                    furthest_dist = -1
                    victim = frames[0]
                    for f in frames:
                        if f not in future:
                            victim = f
                            break
                        else:
                            dist = future.index(f)
                            if dist > furthest_dist:
                                furthest_dist = dist
                                victim = f

                    idx = frames.index(victim)
                    frames[idx] = page
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, victim_page=victim,
                                                 note=f"Page Fault (victim: Page {victim} furthest in future)"))

        return self._package_result("Optimal", steps, hits, faults)

    def _sim_clock(self) -> Dict[str, Any]:
        frames: List[Optional[int]] = [None] * self.num_frames
        use_bits: List[int] = [0] * self.num_frames
        hand = 0
        steps: List[ReplacementStep] = []
        hits = 0
        faults = 0

        for i, page in enumerate(self.ref_string):
            if page in frames:
                hits += 1
                idx = frames.index(page)
                use_bits[idx] = 1
                steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=True, note="Hit (use bit set to 1)"))
            else:
                faults += 1
                if None in frames:
                    idx = frames.index(None)
                    frames[idx] = page
                    use_bits[idx] = 1
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, note="Page Fault (empty frame loaded)"))
                else:
                    victim = None
                    while True:
                        if use_bits[hand] == 0:
                            victim = frames[hand]
                            frames[hand] = page
                            use_bits[hand] = 1
                            hand = (hand + 1) % self.num_frames
                            break
                        else:
                            use_bits[hand] = 0
                            hand = (hand + 1) % self.num_frames

                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, victim_page=victim,
                                                 note=f"Page Fault (victim: Page {victim} via Clock circular scan)"))

        return self._package_result("Clock (Second Chance)", steps, hits, faults)

    def _sim_lfu(self) -> Dict[str, Any]:
        frames: List[Optional[int]] = [None] * self.num_frames
        counts: Dict[int, int] = {}
        steps: List[ReplacementStep] = []
        hits = 0
        faults = 0

        for i, page in enumerate(self.ref_string):
            counts[page] = counts.get(page, 0) + 1
            if page in frames:
                hits += 1
                steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=True, note=f"Hit (frequency={counts[page]})"))
            else:
                faults += 1
                if None in frames:
                    idx = frames.index(None)
                    frames[idx] = page
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, note="Page Fault (empty frame loaded)"))
                else:
                    # Find min frequency in frames
                    victim = min(frames, key=lambda p: counts.get(p, 0))
                    idx = frames.index(victim)
                    frames[idx] = page
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, victim_page=victim,
                                                 note=f"Page Fault (victim: Page {victim} with least frequency {counts.get(victim, 0)})"))

        return self._package_result("LFU", steps, hits, faults)

    def _sim_mfu(self) -> Dict[str, Any]:
        frames: List[Optional[int]] = [None] * self.num_frames
        counts: Dict[int, int] = {}
        steps: List[ReplacementStep] = []
        hits = 0
        faults = 0

        for i, page in enumerate(self.ref_string):
            counts[page] = counts.get(page, 0) + 1
            if page in frames:
                hits += 1
                steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=True, note=f"Hit (frequency={counts[page]})"))
            else:
                faults += 1
                if None in frames:
                    idx = frames.index(None)
                    frames[idx] = page
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, note="Page Fault (empty frame loaded)"))
                else:
                    # Find max frequency in frames
                    victim = max(frames, key=lambda p: counts.get(p, 0))
                    idx = frames.index(victim)
                    frames[idx] = page
                    steps.append(ReplacementStep(i + 1, page, list(frames), is_hit=False, victim_page=victim,
                                                 note=f"Page Fault (victim: Page {victim} with highest frequency {counts.get(victim, 0)})"))

        return self._package_result("MFU", steps, hits, faults)

    def _package_result(self, name: str, steps: List[ReplacementStep], hits: int, faults: int) -> Dict[str, Any]:
        total = len(self.ref_string)
        hit_ratio = (hits / total) * 100 if total > 0 else 0
        fault_ratio = (faults / total) * 100 if total > 0 else 0
        return {
            "algorithm": name,
            "total_references": total,
            "hits": hits,
            "page_faults": faults,
            "hit_ratio_percent": hit_ratio,
            "fault_ratio_percent": fault_ratio,
            "steps": steps,
        }

    def compare_all(self) -> List[Dict[str, Any]]:
        return [
            self.simulate(ReplacementPolicy.FIFO),
            self.simulate(ReplacementPolicy.LRU),
            self.simulate(ReplacementPolicy.OPTIMAL),
            self.simulate(ReplacementPolicy.CLOCK),
            self.simulate(ReplacementPolicy.LFU),
        ]


# ============================================================================
# 9. THRASHING & WORKING SET MODEL
# ============================================================================

class ThrashingAnalyzer:
    """
    Thrashing Analysis & Working Set Model:
    When sum(WSS_i) > Available Frames (D), Thrashing occurs:
    Processes spend more time paging than executing, causing CPU utilization to collapse.
    """
    @staticmethod
    def calculate_working_set(reference_stream: List[int], window_delta: int) -> Dict[str, Any]:
        """
        Calculates the Working Set WSS(t, delta) for the most recent window of size delta.
        """
        recent = reference_stream[-window_delta:] if len(reference_stream) >= window_delta else reference_stream
        wss = set(recent)
        return {
            "window_delta": window_delta,
            "working_set_pages": sorted(list(wss)),
            "wss_size": len(wss),
        }

    @staticmethod
    def evaluate_thrashing_risk(total_wss: int, available_frames: int) -> Dict[str, Any]:
        ratio = total_wss / available_frames if available_frames > 0 else 1.0
        if ratio > 1.0:
            status = "THRASHING CRITICAL"
            advice = "Total Working Sets exceed physical frames! Suspend/swap-out low priority processes immediately."
            cpu_util = max(5.0, 95.0 - (ratio - 1.0) * 120.0)
        elif ratio > 0.85:
            status = "HIGH PAGING PRESSURE"
            advice = "Memory close to saturation. Monitor Page Fault Frequency (PFF)."
            cpu_util = 75.0
        else:
            status = "OPTIMAL EXECUTION"
            advice = "Working sets fit comfortably in RAM. CPU utilization is maximized."
            cpu_util = 90.0

        return {
            "status": status,
            "wss_to_frames_ratio": ratio,
            "estimated_cpu_utilization": min(100.0, max(5.0, cpu_util)),
            "recommendation": advice,
        }


# ============================================================================
# 10. BUDDY SYSTEM ALLOCATOR (BINARY BUDDY ALLOCATION)
# ============================================================================

@dataclass
class BuddyNode:
    address: int
    size_kb: int
    is_allocated: bool = False
    process_name: str = ""
    left: Optional['BuddyNode'] = None
    right: Optional['BuddyNode'] = None

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None


class BuddySystemAllocator:
    """
    Binary Buddy System Allocation:
    Memory is partitioned into blocks of powers of 2.
    When size is requested, block is recursively split in halves (buddies).
    When freed, adjacent buddies coalesce back into a parent block.
    """
    def __init__(self, total_memory_kb: int = 1024):
        # Round up to nearest power of 2
        exp = math.ceil(math.log2(max(total_memory_kb, 16)))
        self.total_memory_kb = 2 ** exp
        self.root = BuddyNode(address=0, size_kb=self.total_memory_kb)

    def allocate(self, process_name: str, requested_size_kb: int) -> Tuple[bool, str]:
        if requested_size_kb <= 0:
            return False, "Size must be > 0 KB."
        target_size = 2 ** math.ceil(math.log2(requested_size_kb))
        if target_size > self.total_memory_kb:
            return False, f"Requested {requested_size_kb} KB exceeds total buddy pool ({self.total_memory_kb} KB)."

        node = self._find_and_split(self.root, target_size)
        if node:
            node.is_allocated = True
            node.process_name = process_name
            internal_frag = node.size_kb - requested_size_kb
            return True, (f"Allocated {requested_size_kb} KB to '{process_name}' in a {node.size_kb} KB Buddy block "
                          f"at address [{node.address} - {node.address + node.size_kb} KB]. Internal Frag = {internal_frag} KB.")
        return False, f"Buddy allocation failed: No suitable power-of-2 block free for {target_size} KB."

    def _find_and_split(self, node: BuddyNode, target_size: int) -> Optional[BuddyNode]:
        if not node.is_leaf:
            res = self._find_and_split(node.left, target_size)
            if res:
                return res
            return self._find_and_split(node.right, target_size)

        if node.is_allocated or node.size_kb < target_size:
            return None

        # If exactly this size, take it
        if node.size_kb == target_size:
            return node

        # Split into two equal halves (buddies)
        half = node.size_kb // 2
        node.left = BuddyNode(address=node.address, size_kb=half)
        node.right = BuddyNode(address=node.address + half, size_kb=half)
        return self._find_and_split(node.left, target_size)

    def deallocate(self, process_name: str) -> Tuple[bool, str]:
        freed = self._free_node(self.root, process_name)
        if freed:
            self._coalesce(self.root)
            return True, f"Freed process '{process_name}' and coalesced buddies."
        return False, f"Process '{process_name}' not found in Buddy memory."

    def _free_node(self, node: BuddyNode, process_name: str) -> bool:
        if node.is_leaf:
            if node.is_allocated and node.process_name == process_name:
                node.is_allocated = False
                node.process_name = ""
                return True
            return False

        if node.left and self._free_node(node.left, process_name):
            return True
        if node.right and self._free_node(node.right, process_name):
            return True
        return False

    def _coalesce(self, node: BuddyNode) -> None:
        if node.is_leaf:
            return
        if node.left:
            self._coalesce(node.left)
        if node.right:
            self._coalesce(node.right)

        # If both children are free leaves, merge them!
        if (node.left and node.left.is_leaf and not node.left.is_allocated and
            node.right and node.right.is_leaf and not node.right.is_allocated):
            node.left = None
            node.right = None

    def get_leaf_blocks(self) -> List[BuddyNode]:
        leaves: List[BuddyNode] = []
        def dfs(n: BuddyNode):
            if n.is_leaf:
                leaves.append(n)
            else:
                if n.left: dfs(n.left)
                if n.right: dfs(n.right)
        dfs(self.root)
        return sorted(leaves, key=lambda b: b.address)


# ============================================================================
# 11. SLAB ALLOCATION (KERNEL OBJECT CACHES)
# ============================================================================

class SlabState(Enum):
    FULL = "Full (All Objects Used)"
    PARTIAL = "Partial (Some Free, Some Used)"
    EMPTY = "Empty (All Objects Free)"


@dataclass
class KernelSlab:
    slab_id: int
    object_size_bytes: int
    objects_per_slab: int
    allocated_count: int = 0

    @property
    def state(self) -> SlabState:
        if self.allocated_count == 0:
            return SlabState.EMPTY
        if self.allocated_count >= self.objects_per_slab:
            return SlabState.FULL
        return SlabState.PARTIAL


class SlabCache:
    """
    Slab Cache for a specific kernel object type (e.g. task_struct, inode, mm_struct).
    Maintains lists of Full, Partial, and Empty slabs.
    """
    def __init__(self, cache_name: str, object_size_bytes: int, objects_per_slab: int = 8):
        self.name = cache_name
        self.object_size_bytes = object_size_bytes
        self.objects_per_slab = objects_per_slab
        self.slabs: List[KernelSlab] = []
        self._next_slab_id = 0
        # Initialize with 1 empty slab
        self._add_slab()

    def _add_slab(self) -> KernelSlab:
        slab = KernelSlab(
            slab_id=self._next_slab_id,
            object_size_bytes=self.object_size_bytes,
            objects_per_slab=self.objects_per_slab,
        )
        self._next_slab_id += 1
        self.slabs.append(slab)
        return slab

    def allocate_object(self) -> Tuple[bool, str, int]:
        # 1. Search in Partial slabs
        for s in self.slabs:
            if s.state == SlabState.PARTIAL:
                s.allocated_count += 1
                return True, f"Allocated object from PARTIAL Slab #{s.slab_id}.", s.slab_id

        # 2. Search in Empty slabs
        for s in self.slabs:
            if s.state == SlabState.EMPTY:
                s.allocated_count += 1
                return True, f"Allocated object from EMPTY Slab #{s.slab_id}.", s.slab_id

        # 3. Create a new slab if all are full
        new_slab = self._add_slab()
        new_slab.allocated_count += 1
        return True, f"Created new Slab #{new_slab.slab_id} and allocated object.", new_slab.slab_id

    def free_object(self) -> Tuple[bool, str]:
        # Free from Partial first, else from Full
        for s in reversed(self.slabs):
            if s.state == SlabState.PARTIAL and s.allocated_count > 0:
                s.allocated_count -= 1
                return True, f"Freed object in Slab #{s.slab_id}."
        for s in reversed(self.slabs):
            if s.state == SlabState.FULL:
                s.allocated_count -= 1
                return True, f"Freed object in Slab #{s.slab_id}."
        return False, "No allocated objects to free."

    @property
    def total_objects_capacity(self) -> int:
        return len(self.slabs) * self.objects_per_slab

    @property
    def total_allocated_objects(self) -> int:
        return sum(s.allocated_count for s in self.slabs)


class SlabAllocator:
    """Kernel Slab Allocator managing standard OS Kernel Object Caches."""
    def __init__(self):
        self.caches: Dict[str, SlabCache] = {
            "task_struct (Process Control Block)": SlabCache("task_struct", object_size_bytes=1800, objects_per_slab=8),
            "mm_struct (Memory Descriptor)": SlabCache("mm_struct", object_size_bytes=1024, objects_per_slab=8),
            "inode (VFS Filesystem Inode)": SlabCache("inode", object_size_bytes=512, objects_per_slab=16),
            "file_struct (Open File Handle)": SlabCache("file_struct", object_size_bytes=256, objects_per_slab=16),
        }
