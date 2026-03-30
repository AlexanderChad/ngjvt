#!/usr/bin/env python3
"""
Test ngjvt library - read junction/VRAM temps for NVIDIA GPUs.
"""

import ctypes
import time
import sys
from pathlib import Path

NVIDIA_VENDOR = "0x10de"
VGA_CLASS = "0x030000"
_3D_CLASS = "0x030200"


def find_nvidia_gpus():
    """Find all NVIDIA VGA/3D controllers and their BAR0 addresses."""
    gpus = []
    base = Path("/sys/bus/pci/devices")
    if not base.exists():
        return gpus

    for device in base.iterdir():
        try:
            vendor = (device / "vendor").read_text().strip()
            if vendor != NVIDIA_VENDOR:
                continue

            dev_class = (device / "class").read_text().strip()
            if dev_class not in (VGA_CLASS, _3D_CLASS):
                continue

            bar0 = int((device / "resource").read_text().split()[0], 16)
            if bar0:
                gpus.append(bar0)
        except:
            pass

    return gpus


def main():
    # Load library
    lib_path = Path(__file__).parent / "ngjvt.so"
    if not lib_path.exists():
        print("ngjvt.so not found. Run: gcc -shared -fPIC -O3 -o ngjvt.so ngjvt.c")
        return 1

    lib = ctypes.CDLL(str(lib_path))
    lib.ngjvt_init.restype = ctypes.c_int
    lib.ngjvt_get_junction_temp.argtypes = [ctypes.c_uint64]
    lib.ngjvt_get_junction_temp.restype = ctypes.c_int
    lib.ngjvt_get_vram_temp.argtypes = [ctypes.c_uint64]
    lib.ngjvt_get_vram_temp.restype = ctypes.c_int
    lib.ngjvt_version.restype = ctypes.c_char_p

    # Initialize
    if lib.ngjvt_init() != 0:
        print("Init failed (need root?)")
        return 1

    # Find GPUs
    gpus = find_nvidia_gpus()
    if not gpus:
        print("No NVIDIA GPUs found")
        lib.ngjvt_shutdown()
        return 0

    # Print version (header, stays on screen)
    print(f"ngjvt v{lib.ngjvt_version().decode()}")
    sys.stdout.flush()

    # Hide cursor
    print("\033[?25l", end="")
    sys.stdout.flush()

    try:
        # Move cursor up for updating lines
        first = True
        while True:
            if not first:
                # Move cursor up N lines
                print(f"\033[{len(gpus)}A", end="")
            first = False

            for bar in gpus:
                j = lib.ngjvt_get_junction_temp(ctypes.c_uint64(bar))
                v = lib.ngjvt_get_vram_temp(ctypes.c_uint64(bar))
                print(f"0x{bar:016x} j={j:2d}°C vram={v:2d}°C")
            sys.stdout.flush()

            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        # Show cursor
        print("\033[?25h", end="")
        sys.stdout.flush()
        lib.ngjvt_shutdown()

    return 0


if __name__ == "__main__":
    exit(main())
