#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
梁文谷 / 梁文峰 时间模式判定器（北京时间）

规则（半开区间 [start, end)：含起点、不含终点）：
    梁文谷·普通 : [00:00, 09:00)  [12:00, 14:00)  [18:00, 24:00)
    梁文峰·极简 : [09:00, 12:00)  [14:00, 18:00)
    附加提醒    : [08:50, 09:00)  [13:50, 14:00)   ← 仍属普通模式，回答末尾追加提醒
    未提供时间  : 默认梁文峰（极简）
    用户明确要求详细回答：以用户要求为准（由提示词层执行）

用法：
    python time_mode.py                # 未提供时间 → 默认梁文峰
    python time_mode.py --now          # 取当前北京时间判定
    python time_mode.py --time 13:55   # 指定时间判定（HH:MM 或 HH:MM:SS）
    python time_mode.py --selftest     # 运行边界测试
"""
from __future__ import annotations

import argparse
import re
import sys
from datetime import datetime, timedelta, timezone

BEIJING_TZ = timezone(timedelta(hours=8))

NORMAL = "梁文谷（普通）"
MINIMAL = "梁文峰（极简）"
REMINDER = "⚠️ 快到梁文峰时间了，建议停下。"

NORMAL_WINDOWS = (("00:00", "09:00"), ("12:00", "14:00"), ("18:00", "24:00"))
MINIMAL_WINDOWS = (("09:00", "12:00"), ("14:00", "18:00"))
REMINDER_WINDOWS = (("08:50", "09:00"), ("13:50", "14:00"))


def _to_seconds(hhmm: str) -> int:
    """HH:MM -> 当日秒数（24:00 视为 86400，即次日 00:00，用作区间终点）。"""
    return int(hhmm[:2]) * 3600 + int(hhmm[3:5]) * 60


def _parse(time_str: str) -> int:
    """解析 HH:MM 或 HH:MM:SS，返回当日秒数；非法输入抛 ValueError。"""
    m = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", time_str.strip())
    if not m:
        raise ValueError(f"无法解析时间 {time_str!r}，格式应为 HH:MM 或 HH:MM:SS")
    h, mi, s = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    if h > 23 or mi > 59 or s > 59:
        raise ValueError(f"时间超出范围 {time_str!r}（小时 0-23，分秒 0-59）")
    return h * 3600 + mi * 60 + s


def _inside(t: int, windows) -> bool:
    return any(
        _to_seconds(lo) <= t < _to_seconds(hi)
        for lo, hi in windows
    )


def get_mode(time_str: str | None = None) -> tuple[str, bool]:
    """
    判定模式。返回 (模式, 是否附加提醒)。

    time_str 为北京时间字符串；None（未提供时间）→ 默认梁文峰（极简）。
    提醒窗口 [08:50,09:00) [13:50,14:00) 落在普通模式内，故仅在普通模式附加。
    """
    if time_str is None:
        return MINIMAL, False
    t = _parse(time_str)
    if _inside(t, MINIMAL_WINDOWS):
        return MINIMAL, False
    return NORMAL, _inside(t, REMINDER_WINDOWS)


def now_beijing() -> str:
    """当前北京时间 HH:MM:SS（UTC+8 纯算术换算，不依赖系统时区库）。"""
    return datetime.now(BEIJING_TZ).strftime("%H:%M:%S")


def _selftest() -> int:
    cases = [
        # (输入, 期望模式, 期望提醒)
        (None,        MINIMAL, False),   # 未提供时间 → 默认极简
        ("00:00",     NORMAL,  False),   # 普通起点
        ("00:00:00",  NORMAL,  False),
        ("08:49:59",  NORMAL,  False),   # 提醒窗口前 1 秒
        ("08:50:00",  NORMAL,  True),    # 提醒窗口起点
        ("08:59:59",  NORMAL,  True),    # 提醒窗口终点前 1 秒
        ("09:00:00",  MINIMAL, False),   # 极简起点（边界归属：极简）
        ("09:00:01",  MINIMAL, False),
        ("11:59:59",  MINIMAL, False),   # 极简终点前 1 秒
        ("12:00:00",  NORMAL,  False),   # 普通恢复
        ("13:49:59",  NORMAL,  False),   # 第二提醒窗口前 1 秒
        ("13:50:00",  NORMAL,  True),
        ("13:59:59",  NORMAL,  True),
        ("14:00:00",  MINIMAL, False),   # 第二段极简起点
        ("17:59:59",  MINIMAL, False),
        ("18:00:00",  NORMAL,  False),   # 傍晚普通起点
        ("23:59:59",  NORMAL,  False),   # 当天最后一秒
    ]
    invalid = ("24:00", "25:00", "9:99", "12:60", "abc", "13:5")
    failed = 0

    for inp, exp_mode, exp_rem in cases:
        mode, rem = get_mode(inp)
        ok = mode == exp_mode and rem == exp_rem
        print(f"{'PASS' if ok else 'FAIL'}  input={inp!r:<12} -> {mode}，提醒={rem}")
        failed += 0 if ok else 1

    for bad in invalid:
        try:
            get_mode(bad)
            print(f"FAIL  应拒绝非法输入 {bad!r}")
            failed += 1
        except ValueError:
            print(f"PASS  拒绝非法输入 {bad!r}")

    total = len(cases) + len(invalid)
    print(f"\n共 {total} 组用例，失败 {failed} 组")
    return 1 if failed else 0


def main() -> int:
    ap = argparse.ArgumentParser(description="梁文谷/梁文峰 时间模式判定器（北京时间）")
    ap.add_argument("--now", action="store_true", help="使用当前北京时间")
    ap.add_argument("--time", metavar="HH:MM[:SS]", help="指定北京时间")
    ap.add_argument("--selftest", action="store_true", help="运行边界测试")
    args = ap.parse_args()

    if args.selftest:
        return _selftest()

    if args.now:
        ts = now_beijing()
        mode, rem = get_mode(ts)
        print(f"当前北京时间: {ts} (+08:00)")
        print(f"模式: {mode}")
        print(REMINDER if rem else "提醒: 无")
    elif args.time:
        try:
            mode, rem = get_mode(args.time)
        except ValueError as e:
            print(f"错误: {e}", file=sys.stderr)
            return 2
        print(f"指定时间: {args.time}")
        print(f"模式: {mode}")
        print(REMINDER if rem else "提醒: 无")
    else:
        mode, rem = get_mode(None)
        print("未提供时间 → 默认规则")
        print(f"模式: {mode}")
        print(REMINDER if rem else "提醒: 无")
    return 0


if __name__ == "__main__":
    sys.exit(main())
