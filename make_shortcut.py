#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建桌面「当前模式」快捷方式（一键查看梁文谷/梁文峰状态），含自定义图标。

- 图标源：产品目录 图标.jpg（首次运行自动转换为 图标.ico；快捷方式只认 .ico）
- 用法：python make_shortcut.py
"""
import os
import subprocess
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_JPG = os.path.join(BASE_DIR, "图标.jpg")
# 独立文件名用于绕过 Windows 图标缓存（同一路径的 .ico 改内容不生效）
ICON_ICO = os.path.join(BASE_DIR, "deepseek_icon.ico")
SHORTCUT_NAME = "deepseek_reminder"


def run_ps(ps: str) -> None:
    """把 PS 脚本写入临时文件（utf-8-sig 保证 PS5.1 正确读中文）并执行。"""
    fd, path = tempfile.mkstemp(suffix=".ps1")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
            f.write(ps)
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
            capture_output=True, timeout=120,
        )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def ensure_icon() -> bool:
    """确保 图标.ico 存在（jpg 首次自动转换）；返回是否有自定义图标。"""
    if os.path.exists(ICON_ICO):
        return True
    if not os.path.exists(ICON_JPG):
        print("[图标] 未找到 图标.jpg，快捷方式将使用默认图标")
        return False
    jpg = ICON_JPG.replace("\\", "\\\\")
    ico = ICON_ICO.replace("\\", "\\\\")
    ps = (
        "Add-Type -AssemblyName System.Drawing\n"
        f"$img = [System.Drawing.Image]::FromFile('{jpg}')\n"
        "$size = 256\n"
        "$bmp = New-Object System.Drawing.Bitmap($size, $size)\n"
        "$g = [System.Drawing.Graphics]::FromImage($bmp)\n"
        "$g.Clear([System.Drawing.Color]::Transparent)\n"
        "# 等比缩放居中，四周透明边距（避免拉伸变形）\n"
        "$ratio = [Math]::Min($size / $img.Width, $size / $img.Height)\n"
        "$w = [int]($img.Width * $ratio); $h = [int]($img.Height * $ratio)\n"
        "$x = [int](($size - $w) / 2); $y = [int](($size - $h) / 2)\n"
        "$g.DrawImage($img, $x, $y, $w, $h)\n"
        "$g.Dispose()\n"
        "$icon = [System.Drawing.Icon]::FromHandle($bmp.GetHicon())\n"
        f"$fs = [System.IO.File]::Create('{ico}')\n"
        "$icon.Save($fs)\n"
        "$fs.Close()\n"
        "$icon.Dispose(); $bmp.Dispose(); $img.Dispose()\n"
        "Write-Output 'ICON_OK'\n"
    )
    print("[图标] 正在转换 图标.jpg → 图标.ico ...")
    run_ps(ps)
    return os.path.exists(ICON_ICO)


def main() -> int:
    has_icon = ensure_icon()
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable  # 退化：python.exe（双击会闪一下控制台）
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    lnk = os.path.join(desktop, SHORTCUT_NAME + ".lnk")
    script = os.path.join(BASE_DIR, "status_check.py")
    icon_line = f"$lnk.IconLocation = '{ICON_ICO}'\n" if has_icon else ""
    ps = (
        "$ws = New-Object -ComObject WScript.Shell\n"
        f"$lnk = $ws.CreateShortcut('{lnk}')\n"
        f"$lnk.TargetPath = '{pythonw}'\n"
        f"$lnk.Arguments = '\"{script}\"'\n"
        f"$lnk.WorkingDirectory = '{BASE_DIR}'\n"
        "$lnk.Description = '查看当前是梁文峰还是梁文谷'\n"
        + icon_line
        + "$lnk.Save()\n"
        "Write-Output 'OK'\n"
    )
    run_ps(ps)
    print(f"[快捷方式] 已更新: {lnk}" + ("（自定义图标）" if has_icon else "（默认图标）"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
