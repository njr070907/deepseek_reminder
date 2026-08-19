#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
梁文峰临近提醒（cron no_agent 看门狗脚本）

- 仅在当前北京时间落在 [08:50, 09:00) 或 [13:50, 14:00) 时触发：
    1) 输出提醒文案（cron 存档/投递）；
    2) 右下角弹出横幅提醒（配图 + 倒计时文案 + 静音）。
  其余时间输出为空 → cron 静默（不发消息）。
- 本任务随 Hermes 进程生命周期运行（调度器在 Hermes 进程内）：
  Hermes 未运行时不会触发。
- 横幅实现见 banner_ui.py（与 status_check.py 共用）；show_toast 为备用系统通知。
- --force: 无视时间窗口强制触发（仅用于测试）。

个性化配置见下方「个性化配置区」：改文案、标题、静音、配图、通知方式都在那里。
"""
import sys
from datetime import datetime, timedelta, timezone

from banner_ui import run_ps1, show_banner

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
    run_ps1(ps)


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
            show_banner(title=BANNER_TITLE, text=text, image=TOAST_IMAGE, seconds=BANNER_SECONDS)
        if NOTIFY_STYLE in ("toast", "both"):
            show_toast(text)
        print(f"[提醒已显示: {NOTIFY_STYLE}]", file=sys.stderr)
    except Exception as e:
        print(f"[提醒显示失败: {e}]", file=sys.stderr)
    return 0


if __name__ == "__main__":
    main()
