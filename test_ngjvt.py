#!/usr/bin/env python3
"""
Test ngjvt library - read junction/VRAM temps for NVIDIA GPUs.

Supports both C (ngjvt.so) and Python (pyngjvt.py) implementations.
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


def load_c_library():
    """Load C implementation (ngjvt.so)."""
    lib_path = Path(__file__).parent / "ngjvt.so"
    if not lib_path.exists():
        return None

    lib = ctypes.CDLL(str(lib_path))
    lib.ngjvt_init.restype = ctypes.c_int
    lib.ngjvt_get_junction_temp.argtypes = [ctypes.c_uint64]
    lib.ngjvt_get_junction_temp.restype = ctypes.c_int
    lib.ngjvt_get_vram_temp.argtypes = [ctypes.c_uint64]
    lib.ngjvt_get_vram_temp.restype = ctypes.c_int
    lib.ngjvt_version.restype = ctypes.c_char_p
    lib.ngjvt_get_error.restype = ctypes.c_char_p

    # Wrapper to decode bytes from C
    lib._version = lib.ngjvt_version
    lib.ngjvt_version = lambda: lib._version().decode()
    lib._get_error = lib.ngjvt_get_error
    lib.ngjvt_get_error = lambda: lib._get_error().decode()

    return lib


def load_py_library():
    """Load Python implementation (pyngjvt.py)."""
    sys.path.insert(0, str(Path(__file__).parent))
    import pyngjvt
    return pyngjvt


def select_implementation():
    """Let user choose implementation."""
    c_available = (Path(__file__).parent / "ngjvt.so").exists()
    py_available = (Path(__file__).parent / "pyngjvt.py").exists()

    print("Select implementation:")
    if c_available:
        print("  [1] C (ngjvt.so)")
    else:
        print("  [1] C (ngjvt.so) - NOT FOUND")

    if py_available:
        print("  [2] Python (pyngjvt.py)")
    else:
        print("  [2] Python (pyngjvt.py) - NOT FOUND")

    while True:
        try:
            choice = input("\nEnter choice [1/2]: ").strip()
            if choice == "1" and c_available:
                lib = load_c_library()
                if lib:
                    return lib, "C"
                print("Failed to load ngjvt.so")
            elif choice == "2" and py_available:
                lib = load_py_library()
                if lib:
                    return lib, "Python"
                print("Failed to load pyngjvt.py")
            else:
                print("Invalid choice or not available")
        except (EOFError, KeyboardInterrupt):
            print("\nCancelled")
            sys.exit(0)


def main():
    # Select and load library
    lib, impl = select_implementation()
    print(f"\nUsing {impl} implementation\n")

    # Initialize
    if lib.ngjvt_init() != 0:
        print(f"Init failed: {lib.ngjvt_get_error()}")
        return 1

    # Find GPUs
    gpus = find_nvidia_gpus()
    if not gpus:
        print("No NVIDIA GPUs found")
        lib.ngjvt_shutdown()
        return 0

    # Print version (header, stays on screen)
    print(f"ngjvt v{lib.ngjvt_version()} ({impl})")
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
                j = lib.ngjvt_get_junction_temp(bar)
                v = lib.ngjvt_get_vram_temp(bar)
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
