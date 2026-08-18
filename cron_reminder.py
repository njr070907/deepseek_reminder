#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
梁文峰临近提醒（cron no_agent 看门狗脚本）

- 仅在当前北京时间落在 [08:50, 09:00) 或 [13:50, 14:00) 时触发：
    1) 输出提醒文案（cron 存档/投递）；
    2) 右下角弹出横幅提醒（自绘窗口：梁圣.jpg 配图 + 倒计时文案 + 静音，
       25 秒自动消失、点击即关；不经过系统通知，不受专注助手影响）。
  其余时间输出为空 → cron 静默（不发消息）。
- 本任务随 Hermes 进程生命周期运行（调度器在 Hermes 进程内）：
  Hermes 未运行时不会触发。
- --force: 无视时间窗口强制触发（仅用于测试）。

个性化配置见下方「个性化配置区」：改文案、标题、静音、配图、通知方式都在那里。
"""
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))

# ==================== 个性化配置区（改这里即可） ====================
BANNER_TITLE = "梁文峰临近提醒"
BANNER_TEXT_TEMPLATE = "⏰ 距离梁文峰时间还有 {minutes} 分钟，建议停下收个尾。"
SILENT = True                                            # True=静音（横幅本来无声；toast 模式用）
TOAST_IMAGE = r"D:\liangwen-mode\梁圣.jpg"               # 提醒配图（即将到来的梁文峰）
NOTIFY_STYLE = "banner"  # "banner"=自绘横幅(可靠) | "toast"=系统通知 | "both"=两者都弹
BANNER_SECONDS = 25      # 横幅停留秒数
# ===================================================================


def in_reminder_window(now: datetime) -> bool:
    """北京时间分钟数是否落在 [08:50, 09:00) 或 [13:50, 14:00)。"""
    hm = now.hour * 60 + now.minute
    return (8 * 60 + 50) <= hm < 9 * 60 or (13 * 60 + 50) <= hm < 14 * 60


def minutes_until_boundary(now: datetime) -> int:
    """距下一个模式切换点（09:00 或 14:00）的分钟数（向上取整，至少 1）。"""
    target = (
        now.replace(hour=9, minute=0, second=0, microsecond=0)
        if now.hour < 9
        else now.replace(hour=14, minute=0, second=0, microsecond=0)
    )
    delta_s = (target - now).total_seconds()
    return max(1, int(delta_s / 60 + 0.999))


def _run_ps1(ps: str) -> None:
    """把 PS 脚本写入临时文件（utf-8-sig 保证 PS5.1 正确读中文）并执行。"""
    fd, path = tempfile.mkstemp(suffix=".ps1")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
            f.write(ps)
        subprocess.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", path],
            capture_output=True, timeout=60,
        )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def show_banner(text: str) -> None:
    """右下角横幅：配图+标题+文案，静音；可拖动、点击即关、25秒自动消失；
    位置自动记忆（D:\\liangwen-mode\\banner_pos.txt），默认在工作区（任务栏上方）右下角。"""
    img = TOAST_IMAGE.replace("\\", "\\\\")
    pos_file = r"D:\liangwen-mode\banner_pos.txt"
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms\n"
        "Add-Type -AssemblyName System.Drawing\n"
        "$script:form = New-Object System.Windows.Forms.Form\n"
        f"$script:form.Text = '{BANNER_TITLE}'\n"
        "$script:form.FormBorderStyle = [System.Windows.Forms.FormBorderStyle]::None\n"
        "$script:form.StartPosition = 'Manual'\n"
        "$script:form.TopMost = $true\n"
        "$script:form.ShowInTaskbar = $false\n"
        "$script:form.BackColor = [System.Drawing.Color]::White\n"
        "$script:form.Width = 320\n"
        "$script:form.Height = 300\n"
        f"$posFile = '{pos_file}'\n"
        "# 读取上次位置；没有则默认右下角（WorkingArea 已排除任务栏）\n"
        "$placed = $false\n"
        "if (Test-Path $posFile) {\n"
        "    $parts = ((Get-Content $posFile -Raw).Trim()) -split ','\n"
        "    if ($parts.Count -eq 2) {\n"
        "        $x = [int]$parts[0]; $y = [int]$parts[1]\n"
        "        if ($x -ge 0 -and $y -ge 0) {\n"
        "            $script:form.Location = New-Object System.Drawing.Point($x, $y); $placed = $true\n"
        "        }\n"
        "    }\n"
        "}\n"
        "if (-not $placed) {\n"
        "    $screen = [System.Windows.Forms.Screen]::PrimaryScreen.WorkingArea\n"
        "    $script:form.Location = New-Object System.Drawing.Point($screen.Width - $script:form.Width - 20, $screen.Height - $script:form.Height - 20)\n"
        "}\n"
        "$title = New-Object System.Windows.Forms.Label\n"
        f"$title.Text = '{BANNER_TITLE}'\n"
        "$title.Font = New-Object System.Drawing.Font('Microsoft YaHei', 11, [System.Drawing.FontStyle]::Bold)\n"
        "$title.Location = New-Object System.Drawing.Point(12, 10)\n"
        "$title.Size = New-Object System.Drawing.Size(296, 24)\n"
        "$script:form.Controls.Add($title)\n"
        "$pic = New-Object System.Windows.Forms.PictureBox\n"
        f"$pic.Image = [System.Drawing.Image]::FromFile('{img}')\n"
        "$pic.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::Zoom\n"
        "$pic.Location = New-Object System.Drawing.Point(12, 40)\n"
        "$pic.Size = New-Object System.Drawing.Size(296, 180)\n"
        "$script:form.Controls.Add($pic)\n"
        "$lbl = New-Object System.Windows.Forms.Label\n"
        f"$lbl.Text = '{text}'\n"
        "$lbl.Font = New-Object System.Drawing.Font('Microsoft YaHei', 10)\n"
        "$lbl.Location = New-Object System.Drawing.Point(12, 228)\n"
        "$lbl.Size = New-Object System.Drawing.Size(296, 60)\n"
        "$lbl.TextAlign = [System.Drawing.ContentAlignment]::MiddleLeft\n"
        "$script:form.Controls.Add($lbl)\n"
        "# 拖动支持（窗口和所有子控件都可拖；位移>4px 视为拖动，不算点击）\n"
        "function Add-Drag {\n"
        "    param($ctrl)\n"
        "    $ctrl.Add_MouseDown({ param($s, $e) if ($e.Button -eq [System.Windows.Forms.MouseButtons]::Left) { $script:dragging = $true; $script:moved = $false; $script:dx = $e.X; $script:dy = $e.Y } })\n"
        "    $ctrl.Add_MouseMove({ param($s, $e) if ($script:dragging) { if ([Math]::Abs($e.X - $script:dx) -gt 4 -or [Math]::Abs($e.Y - $script:dy) -gt 4) { $script:moved = $true }; $script:form.Location = New-Object System.Drawing.Point(($script:form.Left + $e.X - $script:dx), ($script:form.Top + $e.Y - $script:dy)) } })\n"
        "    $ctrl.Add_MouseUp({ param($s, $e) $script:dragging = $false })\n"
        "    $ctrl.Add_Click({ if (-not $script:moved) { $script:form.Close() } })\n"
        "}\n"
        "$script:dragging = $false; $script:moved = $false\n"
        "Add-Drag $script:form; Add-Drag $title; Add-Drag $pic; Add-Drag $lbl\n"
        f"$timer = New-Object System.Windows.Forms.Timer; $timer.Interval = {BANNER_SECONDS * 1000}\n"
        "$timer.Add_Tick({ $script:form.Close() }); $timer.Start()\n"
        "# 关闭时记忆位置\n"
        "$script:form.Add_FormClosed({ param($s, $e) \"$($script:form.Location.X),$($script:form.Location.Y)\" | Out-File $posFile -Encoding UTF8 })\n"
        "[System.Windows.Forms.Application]::Run($script:form)\n"
        "if ($pic.Image) { $pic.Image.Dispose() }\n"
    )
    _run_ps1(ps)


def show_toast(text: str) -> None:
    """系统通知（备用）：静音 + hero 配图；可能被专注助手收进通知中心。"""
    image_uri = "file:///" + TOAST_IMAGE.replace("\\", "/").replace(" ", "%20")
    xml = (
        '<toast scenario="reminder">'
        '<visual><binding template="ToastGeneric">'
        f"<text>{BANNER_TITLE}</text>"
        f"<text>{text}</text>"
        f'<image placement="hero" src="{image_uri}"/>'
        "</binding></visual>"
        + ('<audio silent="true"/>' if SILENT else "")
        + "</toast>"
    )
    ps = (
        "$ErrorActionPreference='Stop'\n"
        "[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime] | Out-Null\n"
        "[Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime] | Out-Null\n"
        "$xml = New-Object Windows.Data.Xml.Dom.XmlDocument\n"
        f"$xml.LoadXml('{xml}')\n"
        "[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier('梁文峰临近提醒').Show($xml)\n"
    )
    _run_ps1(ps)


def main() -> int:
    force = "--force" in sys.argv
    now = datetime.now(BEIJING_TZ)
    if not (force or in_reminder_window(now)):
        return 0  # 窗口外：静默（空输出 = cron 不发送）
    minutes = minutes_until_boundary(now)
    text = BANNER_TEXT_TEMPLATE.format(minutes=minutes)
    print(text)  # 供 cron 存档/投递
    try:
        if NOTIFY_STYLE in ("banner", "both"):
            show_banner(text)
        if NOTIFY_STYLE in ("toast", "both"):
            show_toast(text)
        print(f"[提醒已显示: {NOTIFY_STYLE}]", file=sys.stderr)
    except Exception as e:
        print(f"[提醒显示失败: {e}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    main()
