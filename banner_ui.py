#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
横幅 UI 共用模块：右下角自绘横幅（配图 + 标题 + 文案，静音）。

- 可拖动、点击即关、N 秒自动消失；位置自动记忆（D:\\liangwen-mode\\banner_pos.txt）
- 不经过系统通知，不受专注助手影响
- 被 cron_reminder.py（定时提醒）与 status_check.py（一键查状态）共用

用法：
    from banner_ui import show_banner
    show_banner(title="标题", text="文案", image=r"D:\\...\\图.jpg", seconds=25)
"""
import os
import subprocess
import tempfile


def run_ps1(ps: str) -> None:
    """把 PS 脚本写入临时文件（utf-8-sig 保证 PS5.1 正确读中文）并执行。"""
    fd, path = tempfile.mkstemp(suffix=".ps1")
    try:
        with os.fdopen(fd, "w", encoding="utf-8-sig") as f:
            f.write(ps)
        subprocess.run(
            ["powershell", "-NoProfile", "-WindowStyle", "Hidden", "-ExecutionPolicy", "Bypass", "-File", path],
            capture_output=True, timeout=60, creationflags=0x08000000,  # CREATE_NO_WINDOW：禁止弹出控制台
        )
    finally:
        try:
            os.remove(path)
        except OSError:
            pass


def show_banner(title: str, text: str, image: str = "", seconds: int = 25) -> None:
    """右下角横幅：配图+标题+文案，静音；可拖动、点击即关、自动消失；
    位置自动记忆（banner_pos.txt），默认在工作区（任务栏上方）右下角。
    image 为空时只显示标题+文字（无图布局）。"""
    pos_file = r"D:\liangwen-mode\banner_pos.txt"
    t = title.replace("'", "''")
    x = text.replace("'", "''")
    img_block = ""
    if image:
        img = image.replace("\\", "\\\\")
        img_block = (
            "$pic = New-Object System.Windows.Forms.PictureBox\n"
            f"$pic.Image = [System.Drawing.Image]::FromFile('{img}')\n"
            "$pic.SizeMode = [System.Windows.Forms.PictureBoxSizeMode]::Zoom\n"
            "$pic.Location = New-Object System.Drawing.Point(12, 40)\n"
            "$pic.Size = New-Object System.Drawing.Size(296, 180)\n"
            "$script:form.Controls.Add($pic)\n"
        )
    lbl_y = 228 if image else 40
    lbl_h = 60 if image else 200
    ps = (
        "Add-Type -AssemblyName System.Windows.Forms\n"
        "Add-Type -AssemblyName System.Drawing\n"
        "$script:form = New-Object System.Windows.Forms.Form\n"
        f"$script:form.Text = '{t}'\n"
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
        f"$title.Text = '{t}'\n"
        "$title.Font = New-Object System.Drawing.Font('Microsoft YaHei', 11, [System.Drawing.FontStyle]::Bold)\n"
        "$title.Location = New-Object System.Drawing.Point(12, 10)\n"
        "$title.Size = New-Object System.Drawing.Size(268, 24)\n"
        "$script:form.Controls.Add($title)\n"
        + img_block
        + "$lbl = New-Object System.Windows.Forms.Label\n"
        + f"$lbl.Text = '{x}'\n"
        + "$lbl.Font = New-Object System.Drawing.Font('Microsoft YaHei', 10)\n"
        + f"$lbl.Location = New-Object System.Drawing.Point(12, {lbl_y})\n"
        + f"$lbl.Size = New-Object System.Drawing.Size(296, {lbl_h})\n"
        + "$lbl.TextAlign = [System.Drawing.ContentAlignment]::MiddleLeft\n"
        + "$script:form.Controls.Add($lbl)\n"
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
        "# 右上角关闭按钮（✕）\n"
        "$btn = New-Object System.Windows.Forms.Button\n"
        "$btn.Text = '✕'\n"
        "$btn.FlatStyle = [System.Windows.Forms.FlatStyle]::Flat\n"
        "$btn.FlatAppearance.BorderSize = 0\n"
        "$btn.Location = New-Object System.Drawing.Point(($script:form.Width - 34), 6)\n"
        "$btn.Size = New-Object System.Drawing.Size(28, 24)\n"
        "$btn.Cursor = [System.Windows.Forms.Cursors]::Hand\n"
        "$btn.Add_Click({ $script:form.Close() })\n"
        "$script:form.Controls.Add($btn)\n"
        f"$timer = New-Object System.Windows.Forms.Timer; $timer.Interval = {seconds * 1000}\n"
        "$timer.Add_Tick({ $script:form.Close() }); $timer.Start()\n"
        "# 关闭时记忆位置\n"
        "$script:form.Add_FormClosed({ param($s, $e) \"$($script:form.Location.X),$($script:form.Location.Y)\" | Out-File $posFile -Encoding UTF8 })\n"
        "[System.Windows.Forms.Application]::Run($script:form)\n"
        "if ($pic -and $pic.Image) { $pic.Image.Dispose() }\n"
    )
    run_ps1(ps)
