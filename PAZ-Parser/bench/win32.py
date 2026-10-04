"""The Windows API calls the benchmark needs, through ctypes.

Every function declares its argument and return types. Without them ctypes
passes the process pseudo-handle as a 32-bit int, Windows rejects it, and the
affinity call fails without an error, so the benchmark would run unpinned.
"""
from __future__ import annotations

import sys

if sys.platform != "win32":
    raise ImportError("bench.win32 needs Windows")

import ctypes  # noqa: E402
import re  # noqa: E402
import subprocess  # noqa: E402
import winreg  # noqa: E402
from ctypes import wintypes  # noqa: E402

_HIGH_PRIORITY_CLASS = 0x80
_ERROR_INSUFFICIENT_BUFFER = 122
_CPU_NAME_KEY = r"HARDWARE\DESCRIPTION\System\CentralProcessor\0"
# `powercfg /getactivescheme` prints "Power Scheme GUID: <guid>  (<name>)".
_POWER_PLAN_NAME_RE = re.compile(r"\(([^)]+)\)\s*$")
_POWERCFG_TIMEOUT_S = 10


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_ulonglong),
        ("ullAvailPhys", ctypes.c_ulonglong),
        ("ullTotalPageFile", ctypes.c_ulonglong),
        ("ullAvailPageFile", ctypes.c_ulonglong),
        ("ullTotalVirtual", ctypes.c_ulonglong),
        ("ullAvailVirtual", ctypes.c_ulonglong),
        ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
    ]


_kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

_kernel32.GetCurrentProcess.argtypes = []
_kernel32.GetCurrentProcess.restype = wintypes.HANDLE
_kernel32.SetProcessAffinityMask.argtypes = [wintypes.HANDLE, ctypes.c_size_t]
_kernel32.SetProcessAffinityMask.restype = wintypes.BOOL
_kernel32.GetProcessAffinityMask.argtypes = [
    wintypes.HANDLE,
    ctypes.POINTER(ctypes.c_size_t),
    ctypes.POINTER(ctypes.c_size_t),
]
_kernel32.GetProcessAffinityMask.restype = wintypes.BOOL
_kernel32.SetPriorityClass.argtypes = [wintypes.HANDLE, wintypes.DWORD]
_kernel32.SetPriorityClass.restype = wintypes.BOOL
_kernel32.GetPriorityClass.argtypes = [wintypes.HANDLE]
_kernel32.GetPriorityClass.restype = wintypes.DWORD
_kernel32.GetCurrentProcessorNumber.argtypes = []
_kernel32.GetCurrentProcessorNumber.restype = wintypes.DWORD
_kernel32.GetSystemCpuSetInformation.argtypes = [
    ctypes.c_void_p,
    wintypes.ULONG,
    ctypes.POINTER(wintypes.ULONG),
    wintypes.HANDLE,
    wintypes.ULONG,
]
_kernel32.GetSystemCpuSetInformation.restype = wintypes.BOOL
_kernel32.GlobalMemoryStatusEx.argtypes = [ctypes.POINTER(_MemoryStatusEx)]
_kernel32.GlobalMemoryStatusEx.restype = wintypes.BOOL


def _check(ok: int, call: str) -> None:
    if not ok:
        code = ctypes.get_last_error()
        raise OSError(code, f"{call} failed: {ctypes.FormatError(code).strip()}")


def set_affinity(cpu: int) -> None:
    """Allow the process to run on logical CPU `cpu` only (processor group 0)."""
    _check(_kernel32.SetProcessAffinityMask(_kernel32.GetCurrentProcess(), 1 << cpu), "SetProcessAffinityMask")


def affinity_mask() -> int:
    """The process affinity mask as Windows reports it back."""
    process_mask = ctypes.c_size_t()
    system_mask = ctypes.c_size_t()
    _check(
        _kernel32.GetProcessAffinityMask(
            _kernel32.GetCurrentProcess(), ctypes.byref(process_mask), ctypes.byref(system_mask)
        ),
        "GetProcessAffinityMask",
    )
    return process_mask.value


def set_high_priority() -> None:
    _check(_kernel32.SetPriorityClass(_kernel32.GetCurrentProcess(), _HIGH_PRIORITY_CLASS), "SetPriorityClass")


def is_high_priority() -> bool:
    return _kernel32.GetPriorityClass(_kernel32.GetCurrentProcess()) == _HIGH_PRIORITY_CLASS


def current_cpu() -> int:
    """The logical CPU the calling thread is running on right now."""
    return int(_kernel32.GetCurrentProcessorNumber())


def cpu_set_buffer() -> bytes:
    """The raw SYSTEM_CPU_SET_INFORMATION records, parsed by `pinning.parse_cpu_sets`."""
    needed = wintypes.ULONG()
    if not _kernel32.GetSystemCpuSetInformation(None, 0, ctypes.byref(needed), None, 0):
        if ctypes.get_last_error() != _ERROR_INSUFFICIENT_BUFFER:
            _check(0, "GetSystemCpuSetInformation")
    buffer = ctypes.create_string_buffer(needed.value)
    _check(
        _kernel32.GetSystemCpuSetInformation(buffer, needed, ctypes.byref(needed), None, 0),
        "GetSystemCpuSetInformation",
    )
    return buffer.raw[: needed.value]


def total_ram_bytes() -> int:
    status = _MemoryStatusEx()
    status.dwLength = ctypes.sizeof(_MemoryStatusEx)
    _check(_kernel32.GlobalMemoryStatusEx(ctypes.byref(status)), "GlobalMemoryStatusEx")
    return int(status.ullTotalPhys)


def cpu_model() -> str | None:
    """The CPU brand string, e.g. "13th Gen Intel(R) Core(TM) i9-13900K"."""
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, _CPU_NAME_KEY) as key:
            value, _ = winreg.QueryValueEx(key, "ProcessorNameString")
    except OSError:
        return None
    return str(value).strip() or None


def power_plan() -> str | None:
    """The active power plan's name, or None when powercfg cannot say."""
    try:
        completed = subprocess.run(
            ["powercfg", "/getactivescheme"],
            capture_output=True,
            text=True,
            timeout=_POWERCFG_TIMEOUT_S,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    match = _POWER_PLAN_NAME_RE.search(completed.stdout.strip())
    return match.group(1).strip() if match else None
