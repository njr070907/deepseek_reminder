#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建桌面「当前模式」快捷方式（一键查看梁文谷/梁文峰状态）。

用法：python make_shortcut.py
说明：指向 pythonw.exe 运行 status_check.py，双击无控制台窗口闪动。
"""
import os
import subprocess
import sys
import tempfile


def main() -> int:
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable  # 退化：python.exe（双击会闪一下控制台）
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    lnk = os.path.join(desktop, "当前模式.lnk")
    script = os.path.join(os.path.dirname(os.path.abspath(__file__)), "status_check.py")
    ps = (
        "$ws = New-Object -ComObject WScript.Shell\n"
        f"$lnk = $ws.CreateShortcut('{lnk}')\n"
        f"$lnk.TargetPath = '{pythonw}'\n"
        f"$lnk.Arguments = '\"{script}\"'\n"
        f"$lnk.WorkingDirectory = '{os.path.dirname(script)}'\n"
        "$lnk.Description = '查看当前是梁文峰还是梁文谷'\n"
        "$lnk.Save()\n"
        "Write-Output 'OK'\n"
    )
    fd, path = tempfile.mkstemp(suffix=".ps1")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
            f.write(ps)
        r = subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
            capture_output=True, timeout=60,
        )
        out = r.stdout.decode("utf-8", "replace")
        print(out.strip() or f"returncode={r.returncode}")
        if r.returncode != 0:
            print(r.stderr.decode("utf-8", "replace"), file=sys.stderr)
            return 1
    finally:
        try:
            os.remove(path)
        except OSError:
            pass
    return 0


if __name__ == "__main__":
    sys.exit(main())
