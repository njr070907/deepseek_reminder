#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
当前模式一键查看：显示当前是梁文谷还是梁文峰（图片+弹窗）。

- 判定当前北京时间 → 弹横幅：当前模式 + 对应图片 + 距下次切换时间
- 梁文谷时间 → 小南梁.jpg；梁文峰时间 → 梁圣.jpg
- 用法：双击桌面「当前模式」快捷方式，或命令行 `python status_check.py`
"""
import sys
from datetime import datetime, timedelta, timezone

from banner_ui import show_banner
from time_mode import MINIMAL, NORMAL, get_mode

BEIJING_TZ = timezone(timedelta(hours=8))
IMAGE_NORMAL = r"D:\liangwen-mode\小南梁.jpg"
IMAGE_MINIMAL = r"D:\liangwen-mode\梁圣.jpg"


def next_switch_text(now: datetime) -> str:
    """距下一个模式切换点（09:00/12:00/14:00/18:00/24:00）的时长描述。"""
    mins_now = now.hour * 60 + now.minute
    for b in (9 * 60, 12 * 60, 14 * 60, 18 * 60, 24 * 60):
        if mins_now < b:
            diff = b - mins_now
            if diff >= 60:
                return f"距下次切换还有 {diff // 60} 小时 {diff % 60} 分钟"
            return f"距下次切换还有 {diff} 分钟"
    return ""


def main() -> int:
    now = datetime.now(BEIJING_TZ)
    mode, remind = get_mode(now.strftime("%H:%M:%S"))
    nxt = next_switch_text(now)
    if mode == NORMAL:
        title, image = "当前模式", IMAGE_NORMAL
        text = f"现在是：梁文谷（普通）时间，正常回复。{nxt}。"
    else:
        title, image = "当前模式", IMAGE_MINIMAL
        text = f"现在是：梁文峰（极简）时间，能省则省。{nxt}。"
    if remind:
        text += " ⚠️ 快到梁文峰时间了，建议停下。"
    print(text)  # 终端也能看到
    show_banner(title=title, text=text, image=image, seconds=20)
    return 0


if __name__ == "__main__":
    sys.exit(main())
