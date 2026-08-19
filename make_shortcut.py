#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""创建桌面「deepseek_reminder」快捷方式（一键查看梁文谷/梁文峰状态），含自定义图标。

- 图标源：产品目录 图标.jpg（首次运行自动转换为 .ico；快捷方式只认 .ico）
- 颜色保真：图标以 PNG 数据写入 ICO 容器（32 位色 + 透明无损，避免 GetHicon 掉色变灰）
- 文件名带内容哈希：源图一变文件名就变 → 绕开 Windows 图标缓存，无需重启资源管理器
- 用法：python make_shortcut.py
"""
import glob
import hashlib
import os
import subprocess
import sys
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ICON_JPG = os.path.join(BASE_DIR, "图标.jpg")
SHORTCUT_NAME = "deepseek_reminder"


def current_icon_path() -> str:
    """图标文件名 = 源图内容哈希（源图改动 → 新文件名 → 缓存自然失效）。"""
    h = ""
    if os.path.exists(ICON_JPG):
        with open(ICON_JPG, "rb") as f:
            h = hashlib.md5(f.read()).hexdigest()[:8]
    return os.path.join(BASE_DIR, f"deepseek_icon_{h}.ico")


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


def ensure_icon(ico: str) -> bool:
    """确保 .ico 存在（jpg 首次自动转换）；返回是否成功。"""
    if os.path.exists(ico):
        return True
    if not os.path.exists(ICON_JPG):
        print("[图标] 未找到 图标.jpg，快捷方式将使用默认图标")
        return False
    jpg = ICON_JPG.replace("\\", "\\\\")
    ps = (
        "Add-Type -AssemblyName System.Drawing\n"
        f"$img = [System.Drawing.Image]::FromFile('{jpg}')\n"
        "$size = 256\n"
        "$bmp = New-Object System.Drawing.Bitmap($size, $size, [System.Drawing.Imaging.PixelFormat]::Format32bppArgb)\n"
        "$g = [System.Drawing.Graphics]::FromImage($bmp)\n"
        "$g.Clear([System.Drawing.Color]::Transparent)\n"
        "$g.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic\n"
        "# 等比缩放居中，四周透明边距（避免拉伸变形）\n"
        "$ratio = [Math]::Min($size / $img.Width, $size / $img.Height)\n"
        "$w = [int]($img.Width * $ratio); $h = [int]($img.Height * $ratio)\n"
        "$x = [int](($size - $w) / 2); $y = [int](($size - $h) / 2)\n"
        "$g.DrawImage($img, $x, $y, $w, $h)\n"
        "$g.Dispose()\n"
        "# 转 PNG（完整保留 32 位色 + 透明，避免 GetHicon 转 ICO 掉色/变灰）\n"
        "$ms = New-Object System.IO.MemoryStream\n"
        "$bmp.Save($ms, [System.Drawing.Imaging.ImageFormat]::Png)\n"
        "$png = $ms.ToArray()\n"
        "$ms.Dispose(); $bmp.Dispose(); $img.Dispose()\n"
        "# 手工写 ICO 容器：6 字节头 + 16 字节条目 + PNG 数据\n"
        f"$fs = [System.IO.File]::Create('{ico}')\n"
        "$bw = New-Object System.IO.BinaryWriter($fs)\n"
        "$bw.Write([uint16]0); $bw.Write([uint16]1); $bw.Write([uint16]1)\n"
        "$bw.Write([byte]0); $bw.Write([byte]0); $bw.Write([byte]0); $bw.Write([byte]0)\n"
        "$bw.Write([uint16]1); $bw.Write([uint16]32)\n"
        "$bw.Write([uint32]$png.Length); $bw.Write([uint32]22)\n"
        "$bw.Write($png)\n"
        "$bw.Close(); $fs.Close()\n"
        "Write-Output 'ICON_OK'\n"
    )
    print("[图标] 正在转换 图标.jpg → 无损 PNG-ICO ...")
    run_ps(ps)
    return os.path.exists(ico)


def main() -> int:
    ico = current_icon_path()
    # 清理旧版图标文件（保留当前这个）
    for old in glob.glob(os.path.join(BASE_DIR, "deepseek_icon*.ico")):
        if old != ico:
            try:
                os.remove(old)
            except OSError:
                pass
    has_icon = ensure_icon(ico)
    pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
    if not os.path.exists(pythonw):
        pythonw = sys.executable  # 退化：python.exe（双击会闪一下控制台）
    desktop = os.path.join(os.path.expanduser("~"), "Desktop")
    lnk = os.path.join(desktop, SHORTCUT_NAME + ".lnk")
    script = os.path.join(BASE_DIR, "status_check.py")
    icon_line = f"$lnk.IconLocation = '{ico}'\n" if has_icon else ""
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
    print(f"[快捷方式] 已更新: {lnk}（图标: {os.path.basename(ico)}）")
    return 0


if __name__ == "__main__":
    sys.exit(main())
