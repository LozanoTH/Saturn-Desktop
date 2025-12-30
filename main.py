# -*- coding: utf-8 -*-
import time, math, ctypes, tkinter as tk, threading
from ctypes import wintypes
from tkinter import ttk

# Global parameters for live updates
params = {
    'center_x': 960,
    'center_y': 540,
    'a': 400,
    'b': 100,
    'radius': 50,
    'mouse_speed_control': True,
    'speed_base': 0.3,
    'speed_far': 0.6,
    'speed_min': 0.12,
    'speed_inside': 0.1,
    'slow_band': 220,
    'fps': 60.0,
    'black_hole_name': 'Ojo Negro',
    'running': False
}

# -----------------------------------------------------------------------------
# Constants
# -----------------------------------------------------------------------------
LVM_FIRST = 0x1000
LVIF_TEXT = 0x0001
LVS_EX_SNAPTOGRID = 0x00080000
LVM_GETITEMCOUNT = LVM_FIRST + 4
LVM_SETITEMPOSITION = LVM_FIRST + 15
LVM_GETITEMTEXTW = LVM_FIRST + 115
LVM_SETEXTENDEDLISTVIEWSTYLE = LVM_FIRST + 54
LVM_GETEXTENDEDLISTVIEWSTYLE = LVM_FIRST + 55
LVM_GETITEMPOSITION = LVM_FIRST + 16

SM_CXSCREEN = 0
SM_CYSCREEN = 1

VK_P = 0x50

PROCESS_VM_OPERATION = 0x0008
PROCESS_VM_READ = 0x0010
PROCESS_VM_WRITE = 0x0020
PROCESS_QUERY_INFORMATION = 0x0400
PROCESS_ALL_ACCESS = 0x1F0FFF

MEM_COMMIT = 0x1000
MEM_RESERVE = 0x2000
MEM_RELEASE = 0x8000
PAGE_READWRITE = 0x04

if not hasattr(wintypes, "LRESULT"):
    wintypes.LRESULT = wintypes.LPARAM

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

# Windows 10+: best option (Per-monitor DPI aware v2)
try:
    SetProcessDpiAwarenessContext = user32.SetProcessDpiAwarenessContext
    SetProcessDpiAwarenessContext.argtypes = [wintypes.HANDLE]
    SetProcessDpiAwarenessContext.restype = wintypes.BOOL
    DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2 = wintypes.HANDLE(-4)
    SetProcessDpiAwarenessContext(DPI_AWARENESS_CONTEXT_PER_MONITOR_AWARE_V2)
except Exception:
    # Legacy fallback
    try:
        user32.SetProcessDPIAware()
    except Exception:
        pass

# -----------------------------------------------------------------------------
# user32: FindWindowExW, SendMessageW, GetWindowThreadProcessId
# -----------------------------------------------------------------------------
FindWindowEx = user32.FindWindowExW
FindWindowEx.argtypes = [
    wintypes.HWND,    # hwndParent
    wintypes.HWND,    # hwndChildAfter
    wintypes.LPCWSTR, # lpszClass
    wintypes.LPCWSTR, # lpszWindow
]
FindWindowEx.restype = wintypes.HWND

SendMessage = user32.SendMessageW
# NOTE: no argtypes on purpose, since we sometimes pass ints and sometimes pointers
SendMessage.restype = wintypes.LRESULT

GetWindowThreadProcessId = user32.GetWindowThreadProcessId
GetWindowThreadProcessId.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.DWORD)]
GetWindowThreadProcessId.restype = wintypes.DWORD

# --- user32 extras ---
class POINT(ctypes.Structure):
    _fields_ = [("x", wintypes.LONG), ("y", wintypes.LONG)]

GetCursorPos = user32.GetCursorPos
GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
GetCursorPos.restype = wintypes.BOOL

ScreenToClient = user32.ScreenToClient
ScreenToClient.argtypes = [wintypes.HWND, ctypes.POINTER(POINT)]
ScreenToClient.restype = wintypes.BOOL

ClientToScreen = user32.ClientToScreen
ClientToScreen.argtypes = [wintypes.HWND, ctypes.POINTER(POINT)]
ClientToScreen.restype = wintypes.BOOL

GetSystemMetrics = user32.GetSystemMetrics
GetSystemMetrics.argtypes = [wintypes.INT]
GetSystemMetrics.restype = wintypes.INT

GetAsyncKeyState = user32.GetAsyncKeyState
GetAsyncKeyState.argtypes = [wintypes.INT]
GetAsyncKeyState.restype = wintypes.SHORT

# -----------------------------------------------------------------------------
# kernel32: OpenProcess, VirtualAllocEx, Read/WriteProcessMemory, VirtualFreeEx
# -----------------------------------------------------------------------------
OpenProcess = kernel32.OpenProcess
OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
OpenProcess.restype = wintypes.HANDLE

VirtualAllocEx = kernel32.VirtualAllocEx
VirtualAllocEx.argtypes = [
    wintypes.HANDLE,  # hProcess
    wintypes.LPVOID,  # lpAddress
    ctypes.c_size_t,  # dwSize
    wintypes.DWORD,   # flAllocationType
    wintypes.DWORD,   # flProtect
]
VirtualAllocEx.restype = wintypes.LPVOID

WriteProcessMemory = kernel32.WriteProcessMemory
WriteProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    wintypes.LPCVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
WriteProcessMemory.restype = wintypes.BOOL

ReadProcessMemory = kernel32.ReadProcessMemory
ReadProcessMemory.argtypes = [
    wintypes.HANDLE,
    wintypes.LPCVOID,
    wintypes.LPVOID,
    ctypes.c_size_t,
    ctypes.POINTER(ctypes.c_size_t),
]
ReadProcessMemory.restype = wintypes.BOOL

VirtualFreeEx = kernel32.VirtualFreeEx
VirtualFreeEx.argtypes = [
    wintypes.HANDLE,
    wintypes.LPVOID,
    ctypes.c_size_t,
    wintypes.DWORD,
]
VirtualFreeEx.restype = wintypes.BOOL

CloseHandle = kernel32.CloseHandle
CloseHandle.argtypes = [wintypes.HANDLE]
CloseHandle.restype = wintypes.BOOL

# -----------------------------------------------------------------------------
# LVITEMW structure (wide / Unicode)
# -----------------------------------------------------------------------------
class LVITEMW(ctypes.Structure):
    _fields_ = [
        ("mask", wintypes.UINT),
        ("iItem", wintypes.INT),
        ("iSubItem", wintypes.INT),
        ("state", wintypes.UINT),
        ("stateMask", wintypes.UINT),
        ("pszText", wintypes.LPWSTR),
        ("cchTextMax", wintypes.INT),
        ("iImage", wintypes.INT),
        ("lParam", wintypes.LPARAM),
        ("iIndent", wintypes.INT),
        ("iGroupId", wintypes.INT),
        ("cColumns", wintypes.UINT),
        ("puColumns", ctypes.POINTER(wintypes.UINT)),
        ("piColFmt", ctypes.POINTER(ctypes.c_int)),
        ("iGroup", ctypes.c_int),
    ]

# -----------------------------------------------------------------------------
# Helper: allocate remote memory
# -----------------------------------------------------------------------------
def remote_alloc(hProcess, size):
    addr = VirtualAllocEx(
        hProcess,
        None,
        size,
        MEM_COMMIT | MEM_RESERVE,
        PAGE_READWRITE,
    )
    if not addr:
        err = ctypes.get_last_error()
        raise OSError(err, f"VirtualAllocEx failed with error {err:#x}")
    return addr

def remote_free(hProcess, addr):
    if addr:
        if not VirtualFreeEx(hProcess, addr, 0, MEM_RELEASE):
            err = ctypes.get_last_error()
            print(f"[warn] VirtualFreeEx error {err:#x}")

def get_screen_size():
    width = GetSystemMetrics(SM_CXSCREEN)
    height = GetSystemMetrics(SM_CYSCREEN)
    return width, height

# -----------------------------------------------------------------------------
# Helper: get the desktop SysListView32
# -----------------------------------------------------------------------------
def get_desktop_listview():
    progman = FindWindowEx(0, 0, "Progman", None)
    defview = FindWindowEx(progman, 0, "SHELLDLL_DefView", None)

    if not defview:
        workerw = FindWindowEx(0, 0, "WorkerW", None)
        while workerw and not defview:
            defview = FindWindowEx(workerw, 0, "SHELLDLL_DefView", None)
            workerw = FindWindowEx(0, workerw, "WorkerW", None)

    if not defview:
        return None

    listview = FindWindowEx(defview, 0, "SysListView32", None)
    return listview

# -----------------------------------------------------------------------------
# Helper: open the process that owns the ListView
# -----------------------------------------------------------------------------
def open_listview_process(hwnd):
    pid = wintypes.DWORD(0)
    thread_id = GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
    if thread_id == 0 or pid.value == 0:
        raise RuntimeError("Failed to get the ListView PID")

    # Try ALL_ACCESS; if it fails, you can narrow the required flags
    hProcess = OpenProcess(PROCESS_ALL_ACCESS, False, pid.value)
    if not hProcess:
        err = ctypes.get_last_error()
        raise OSError(err, f"OpenProcess failed with error {err:#x}")

    return hProcess

# -----------------------------------------------------------------------------
# get_icon_name(index)
# -----------------------------------------------------------------------------
def get_icon_name(index):
    listview = get_desktop_listview()
    if not listview:
        print("Desktop ListView not found")
        return None

    # Number of icons
    count = SendMessage(listview, LVM_GETITEMCOUNT, 0, 0)
    print("[dbg] Desktop icons reported by ListView:", count)
    if index < 0 or index >= count:
        print("Index out of range")
        return None

    # Open the ListView owner process (explorer.exe)
    hProcess = open_listview_process(listview)

    # Structure sizes
    text_max = 260
    local_text_buffer = ctypes.create_unicode_buffer(text_max)
    lvitem_local = LVITEMW()
    lvitem_size = ctypes.sizeof(LVITEMW)

    try:
        # Allocate remote memory: first for the text buffer, then for the LVITEM
        remote_text = remote_alloc(hProcess, text_max * ctypes.sizeof(ctypes.c_wchar))
        remote_lvitem = remote_alloc(hProcess, lvitem_size)

        # Prepare local LVITEM, but with pszText pointing to remote_text (in the remote process)
        lvitem_local.mask = LVIF_TEXT
        lvitem_local.iItem = index
        lvitem_local.iSubItem = 0
        lvitem_local.state = 0
        lvitem_local.stateMask = 0
        # Cast the remote address to LPWSTR
        lvitem_local.pszText = ctypes.cast(remote_text, wintypes.LPWSTR)
        lvitem_local.cchTextMax = text_max
        lvitem_local.iImage = 0
        lvitem_local.lParam = 0
        lvitem_local.iIndent = 0
        lvitem_local.iGroupId = 0
        lvitem_local.cColumns = 0
        lvitem_local.puColumns = None
        lvitem_local.piColFmt = None
        lvitem_local.iGroup = 0

        # Write LVITEM into remote memory
        written = ctypes.c_size_t(0)
        ok = WriteProcessMemory(
            hProcess,
            remote_lvitem,
            ctypes.byref(lvitem_local),
            lvitem_size,
            ctypes.byref(written),
        )
        if not ok or written.value != lvitem_size:
            err = ctypes.get_last_error()
            raise OSError(err, f"WriteProcessMemory(LVITEM) failed: {err:#x}")

        # Send the message to the ListView using the remote LVITEM pointer
        SendMessage(listview, LVM_GETITEMTEXTW, index, remote_lvitem)

        # Read the text from remote memory into the local buffer
        read = ctypes.c_size_t(0)
        ok = ReadProcessMemory(
            hProcess,
            remote_text,
            local_text_buffer,
            text_max * ctypes.sizeof(ctypes.c_wchar),
            ctypes.byref(read),
        )
        if not ok:
            err = ctypes.get_last_error()
            raise OSError(err, f"ReadProcessMemory(text) failed: {err:#x}")

        # Return the buffer value (Python string)
        return local_text_buffer.value

    finally:
        # Free remote memory and close handle
        remote_free(hProcess, remote_text)
        remote_free(hProcess, remote_lvitem)
        CloseHandle(hProcess)

# -----------------------------------------------------------------------------
# move_first_icon(x, y)
# -----------------------------------------------------------------------------
def move_first_icon(x, y):
    listview = get_desktop_listview()
    if not listview:
        print("Desktop icon list not found")
        return

    count = SendMessage(listview, LVM_GETITEMCOUNT, 0, 0)
    print("Total icons:", count)
    if count == 0:
        print("No icons")
        return

    lparam = (x & 0xFFFF) | (y << 16)
    SendMessage(listview, LVM_SETITEMPOSITION, 0, lparam)
    print(f"Icon 0 moved to ({x}, {y})")

def move_icon(index, x, y):
    listview = get_desktop_listview()
    if not listview:
        return

    # ListView client coordinates
    lparam = (int(x) & 0xFFFF) | ((int(y) & 0xFFFF) << 16)
    SendMessage(listview, LVM_SETITEMPOSITION, index, lparam)

def get_item_count() -> int:
    listview = get_desktop_listview()
    count = SendMessage(listview, LVM_GETITEMCOUNT, 0, 0)
    return count

def disable_snap_to_grid() -> bool:
    listview = get_desktop_listview()
    if not listview:
        return False

    # Clear only the SNAPTOGRID bit (mask in wParam)
    SendMessage(listview, LVM_SETEXTENDEDLISTVIEWSTYLE, LVS_EX_SNAPTOGRID, 0)

    # Verify
    ex_style = int(SendMessage(listview, LVM_GETEXTENDEDLISTVIEWSTYLE, 0, 0))
    return (ex_style & LVS_EX_SNAPTOGRID) == 0

# -----------------------------------------------------------------------------
def get_mouse_screen_pos():
    pt = POINT()
    if not GetCursorPos(ctypes.byref(pt)):
        raise OSError(ctypes.get_last_error(), "GetCursorPos failed")
    return pt.x, pt.y

def get_icon_client_pos(listview_hwnd, index):
    # LVM_GETITEMPOSITION writes a POINT into lParam (a pointer). Since the ListView
    # belongs to another process, we use remote memory the same way as with LVITEM.
    hProcess = open_listview_process(listview_hwnd)
    try:
        remote_pt = remote_alloc(hProcess, ctypes.sizeof(POINT))
        SendMessage(listview_hwnd, LVM_GETITEMPOSITION, index, remote_pt)

        local_pt = POINT()
        read = ctypes.c_size_t(0)
        ok = ReadProcessMemory(
            hProcess,
            remote_pt,
            ctypes.byref(local_pt),
            ctypes.sizeof(POINT),
            ctypes.byref(read),
        )
        if not ok:
            err = ctypes.get_last_error()
            raise OSError(err, f"ReadProcessMemory(POINT) failed: {err:#x}")

        return local_pt.x, local_pt.y

    finally:
        remote_free(hProcess, remote_pt)
        CloseHandle(hProcess)

def get_mouse_pos_relative_to_icon(index=0):
    listview = get_desktop_listview()
    if not listview:
        raise RuntimeError("Desktop ListView not found")

    # Mouse: screen coords -> ListView client coords
    mx, my = get_mouse_screen_pos()
    mpt = POINT(mx, my)
    if not ScreenToClient(listview, ctypes.byref(mpt)):
        raise OSError(ctypes.get_last_error(), "ScreenToClient failed")

    # Icon position in ListView client coords
    ix, iy = get_icon_client_pos(listview, index)

    dx = mpt.x - ix
    dy = mpt.y - iy
    return {
        "mouse_screen": (mx, my),
        "mouse_client": (mpt.x, mpt.y),
        "icon_client": (ix, iy),
        "delta": (dx, dy),
    }

# -----------------------------------------------------------------------------


def animate_saturn_rings():
    while not params['running']:
        time.sleep(0.1)

    while params['running']:
        cx = params['center_x']
        cy = params['center_y']
        a = params['a']
        b = params['b']
        radius = params['radius']
        mouse_speed_control = params['mouse_speed_control']
        speed_base = params['speed_base']
        speed_far = params['speed_far']
        speed_min = params['speed_min']
        speed_inside = params['speed_inside']
        slow_band = params['slow_band']
        fps = params['fps']
        black_hole_name = params['black_hole_name']

        planet_r2 = int(radius) * int(radius)

        # Get listview for client coord conversion
        listview_hwnd = get_desktop_listview()

        # Find the black hole icon index
        black_hole_index = None
        count = get_item_count()
        for i in range(count):
            name = get_icon_name(i)
            if black_hole_name in name:
                black_hole_index = i
                break

        dt_target = 1.0 / fps

        # Where to hide icons (ListView client coordinates)
        HIDE_X, HIDE_Y = -5000, -5000

        t0 = time.perf_counter()
        last_t = t0
        phase = 0.0
        paused = False
        shine_phase = 0.0

        while params['running']:
            count = get_item_count()
            if count <= 0:
                print("No icons")
                time.sleep(1)
                continue

            now = time.perf_counter()

            # Check for pause key
            if GetAsyncKeyState(VK_P) & 0x8000:
                paused = not paused
                time.sleep(0.1)  # debounce

            if paused:
                time.sleep(dt_target)
                continue

            dt = now - last_t
            last_t = now

            shine_phase += dt * 5.0  # slower for shine effect

            # --- Phase update ---
            if mouse_speed_control:
                mx, my = get_mouse_screen_pos()
                dxm = mx - cx
                dym = my - cy
                dist = math.hypot(dxm, dym)

                if dist <= radius:
                    cur_speed = speed_inside
                else:
                    tnorm = (dist - radius) / slow_band
                    tnorm = max(0.0, min(1.0, tnorm))
                    # smoothstep
                    tnorm = tnorm * tnorm * (3.0 - 2.0 * tnorm)
                    cur_speed = speed_min + (speed_far - speed_min) * tnorm

                phase += cur_speed * dt
            else:
                # Original behaviour (time-based)
                t = now - t0
                phase = speed_base * t

            # Entry animation: scale positions over first 3 seconds
            entry_duration = 3.0
            elapsed = now - t0
            scale = min(1.0, elapsed / entry_duration)

            # --- Icon placement ---
            for i in range(count):
                if i == black_hole_index:
                    # Black hole at center with shine effect (blinking)
                    if math.sin(shine_phase) > 0:
                        move_icon(i, cx, cy)
                    else:
                        move_icon(i, HIDE_X, HIDE_Y)
                else:
                    base = (2.0 * math.pi) * (i / (count - 1 if black_hole_index is not None else count))
                    ang = base + phase

                    target_x = cx + a * math.cos(ang)
                    target_y = cy + b * math.sin(ang)

                    x = cx + scale * (target_x - cx)
                    y = cy + scale * (target_y - cy)

                    # "Behind" the planet: back half of the orbit
                    behind = math.sin(ang) < 0.0

                    # Occlusion by the planet disk
                    dx = x - cx
                    dy = y - cy
                    occluded = (dx * dx + dy * dy) <= planet_r2

                    if behind and occluded:
                        move_icon(i, HIDE_X, HIDE_Y)
                    else:
                        move_icon(i, int(x), int(y))

            time.sleep(dt_target)

class SaturnGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Animador de Escritorio Saturno")
        self.root.geometry("300x500")
        self.root.attributes("-topmost", True)
        self.hidden = False

        # Set initial params
        screen_width, screen_height = get_screen_size()
        params['center_x'] = screen_width // 2
        params['center_y'] = screen_height // 2
        params['a'] = screen_width // 3
        params['b'] = screen_height // 10
        params['radius'] = min(screen_width, screen_height) // 8

        # Create widgets
        row = 0
        ttk.Label(root, text="Centro X:").grid(row=row, column=0, sticky="w")
        self.cx_entry = ttk.Entry(root)
        self.cx_entry.insert(0, str(params['center_x']))
        self.cx_entry.grid(row=row, column=1)
        self.cx_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Centro Y:").grid(row=row, column=0, sticky="w")
        self.cy_entry = ttk.Entry(root)
        self.cy_entry.insert(0, str(params['center_y']))
        self.cy_entry.grid(row=row, column=1)
        self.cy_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Semieje Horizontal (a):").grid(row=row, column=0, sticky="w")
        self.a_entry = ttk.Entry(root)
        self.a_entry.insert(0, str(params['a']))
        self.a_entry.grid(row=row, column=1)
        self.a_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Semieje Vertical (b):").grid(row=row, column=0, sticky="w")
        self.b_entry = ttk.Entry(root)
        self.b_entry.insert(0, str(params['b']))
        self.b_entry.grid(row=row, column=1)
        self.b_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Radio del Planeta:").grid(row=row, column=0, sticky="w")
        self.radius_entry = ttk.Entry(root)
        self.radius_entry.insert(0, str(params['radius']))
        self.radius_entry.grid(row=row, column=1)
        self.radius_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Velocidad según Distancia del Cursor:").grid(row=row, column=0, sticky="w")
        self.mouse_control_var = tk.BooleanVar(value=params['mouse_speed_control'])
        ttk.Checkbutton(root, variable=self.mouse_control_var, command=self.update_params).grid(row=row, column=1, sticky="w")

        row += 1
        ttk.Label(root, text="Velocidad Base:").grid(row=row, column=0, sticky="w")
        self.speed_base_entry = ttk.Entry(root)
        self.speed_base_entry.insert(0, str(params['speed_base']))
        self.speed_base_entry.grid(row=row, column=1)
        self.speed_base_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Velocidad Lejana:").grid(row=row, column=0, sticky="w")
        self.speed_far_entry = ttk.Entry(root)
        self.speed_far_entry.insert(0, str(params['speed_far']))
        self.speed_far_entry.grid(row=row, column=1)
        self.speed_far_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Velocidad Mínima:").grid(row=row, column=0, sticky="w")
        self.speed_min_entry = ttk.Entry(root)
        self.speed_min_entry.insert(0, str(params['speed_min']))
        self.speed_min_entry.grid(row=row, column=1)
        self.speed_min_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Velocidad Interior:").grid(row=row, column=0, sticky="w")
        self.speed_inside_entry = ttk.Entry(root)
        self.speed_inside_entry.insert(0, str(params['speed_inside']))
        self.speed_inside_entry.grid(row=row, column=1)
        self.speed_inside_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Banda de Desaceleración:").grid(row=row, column=0, sticky="w")
        self.slow_band_entry = ttk.Entry(root)
        self.slow_band_entry.insert(0, str(params['slow_band']))
        self.slow_band_entry.grid(row=row, column=1)
        self.slow_band_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="FPS:").grid(row=row, column=0, sticky="w")
        self.fps_entry = ttk.Entry(root)
        self.fps_entry.insert(0, str(params['fps']))
        self.fps_entry.grid(row=row, column=1)
        self.fps_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        ttk.Label(root, text="Nombre del Agujero Negro:").grid(row=row, column=0, sticky="w")
        self.black_hole_entry = ttk.Entry(root)
        self.black_hole_entry.insert(0, params['black_hole_name'])
        self.black_hole_entry.grid(row=row, column=1)
        self.black_hole_entry.bind("<KeyRelease>", self.update_params)

        row += 1
        self.start_btn = ttk.Button(root, text="Iniciar Animación", command=self.start_animation)
        self.start_btn.grid(row=row, column=0, columnspan=2)

        row += 1
        self.hide_btn = ttk.Button(root, text="Ocultar Menú", command=self.toggle_visibility)
        self.hide_btn.grid(row=row, column=0, columnspan=2)

    def update_params(self, event=None):
        try:
            params['center_x'] = int(self.cx_entry.get())
            params['center_y'] = int(self.cy_entry.get())
            params['a'] = int(self.a_entry.get())
            params['b'] = int(self.b_entry.get())
            params['radius'] = int(self.radius_entry.get())
            params['mouse_speed_control'] = self.mouse_control_var.get()
            params['speed_base'] = float(self.speed_base_entry.get())
            params['speed_far'] = float(self.speed_far_entry.get())
            params['speed_min'] = float(self.speed_min_entry.get())
            params['speed_inside'] = float(self.speed_inside_entry.get())
            params['slow_band'] = int(self.slow_band_entry.get())
            params['fps'] = float(self.fps_entry.get())
            params['black_hole_name'] = self.black_hole_entry.get()
        except ValueError:
            pass  # Ignore invalid inputs

    def start_animation(self):
        ok = disable_snap_to_grid()
        if not ok:
            print("Error disabling snap to grid")
            return

        params['running'] = True
        self.start_btn.config(text="Detener Animación", command=self.stop_animation)
        threading.Thread(target=animate_saturn_rings, daemon=True).start()

    def stop_animation(self):
        params['running'] = False
        self.start_btn.config(text="Iniciar Animación", command=self.start_animation)

    def toggle_visibility(self):
        if self.hidden:
            self.root.deiconify()
            self.hide_btn.config(text="Ocultar Menú")
            self.hidden = False
        else:
            self.root.withdraw()
            self.hidden = True

if __name__ == "__main__":
    root = tk.Tk()
    gui = SaturnGUI(root)
    root.mainloop()