"""
pyngjvt - NVIDIA GPU Junction/VRAM Temperature Library (Python)

Pure Python implementation of ngjvt for reading GPU junction/hotspot
and VRAM temperatures on Linux.

Requires:
  - Root privileges (for /dev/mem access)
  - iomem=relaxed kernel parameter, disabled Secure Boot

https://github.com/AlexanderChad/ngjvt
"""

import os
import mmap

NGJVT_OFFSET_JUNCTION = 0x0002046C
NGJVT_OFFSET_VRAM = 0x0000E2A8
NGJVT_PAGE_SIZE = os.sysconf(os.sysconf_names['SC_PAGE_SIZE'])

ngjvt_initialized = False
ngjvt_mem_fd = -1
ngjvt_error = ""


def ngjvt_init():
    """Initialize library. Returns 0 on success, -1 on error."""
    global ngjvt_initialized, ngjvt_mem_fd, ngjvt_error

    if ngjvt_initialized:
        return 0

    if os.geteuid() != 0:
        ngjvt_error = "Root required"
        return -1

    try:
        ngjvt_mem_fd = os.open("/dev/mem", os.O_RDONLY | os.O_SYNC)
    except OSError as e:
        ngjvt_error = f"open(/dev/mem): {e.strerror}"
        return -1

    ngjvt_initialized = True
    return 0


def ngjvt_get_error():
    """Returns last error message."""
    return ngjvt_error


def read_temp(bar, offset):
    """Internal: read temperature from GPU register."""
    global ngjvt_initialized, ngjvt_mem_fd

    if not ngjvt_initialized:
        return -1

    addr = bar + offset
    page = addr & ~(NGJVT_PAGE_SIZE - 1)

    try:
        m = mmap.mmap(ngjvt_mem_fd, NGJVT_PAGE_SIZE, mmap.MAP_SHARED, mmap.PROT_READ, offset=page)
        addr_offset = addr - page
        val = int.from_bytes(m[addr_offset:addr_offset + 4], 'little')
        m.close()
    except Exception:
        return -1

    if offset == NGJVT_OFFSET_JUNCTION:
        temp = (val >> 8) & 0xFF
    else:
        temp = (val & 0xFFF) // 0x20

    return temp if temp < 127 else -1


def ngjvt_get_junction_temp(bar):
    """Get junction/hotspot temperature. Returns -1 on error."""
    return read_temp(bar, NGJVT_OFFSET_JUNCTION)


def ngjvt_get_vram_temp(bar):
    """Get VRAM temperature. Returns -1 on error."""
    return read_temp(bar, NGJVT_OFFSET_VRAM)


def ngjvt_shutdown():
    """Cleanup resources."""
    global ngjvt_initialized, ngjvt_mem_fd

    if not ngjvt_initialized:
        return

    if ngjvt_mem_fd >= 0:
        os.close(ngjvt_mem_fd)

    ngjvt_initialized = False
    ngjvt_mem_fd = -1


def ngjvt_version():
    """Returns library version string."""
    return "1.0"
