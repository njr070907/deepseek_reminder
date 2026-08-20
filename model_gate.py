#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
模型门槛：仅当 Hermes 当前配置的模型为 DeepSeek v4（pro/flash）时，时间模式产品才生效。

读取 Hermes config.yaml 的 model.default / model.provider 判断；
被 cron_reminder.py（定时提醒）与 status_check.py（一键查看）共用。

说明：以 config.yaml 的默认模型为准（cron/新会话都用它）；会话内临时换模型
以会话为准，但脚本侧无法感知，只能以配置为准。
"""
import os
import re

HERMES_CONFIG = r"C:\Users\lin_q\AppData\Local\hermes\config.yaml"


def read_model_config(config_path: str = HERMES_CONFIG) -> dict:
    """从 config.yaml 提取 model 段（default/provider）；文件缺失/异常返回空 dict。"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            lines = f.read().splitlines()
    except OSError:
        return {}
    model: dict = {}
    in_model = False
    for line in lines:
        if not in_model:
            if re.fullmatch(r"model:", line.strip()) and not line.startswith((" ", "\t")):
                in_model = True
            continue
        # 已进入 model 段：遇到下一个顶层键即退出
        if line and not line[0].isspace() and line.strip() != "model:":
            break
        m = re.fullmatch(r"\s{2}(default|provider):\s*(.+)", line)
        if m:
            model[m.group(1)] = m.group(2).strip().strip("'\"")
    return model


def is_deepseek_v4_active(config_path: str = HERMES_CONFIG) -> bool:
    """当前配置的模型是否为 DeepSeek 且为 v4 系列（pro/flash）。"""
    m = read_model_config(config_path)
    provider = m.get("provider", "").lower()
    default = m.get("default", "").lower()
    return "deepseek" in provider and "deepseek-v4" in default


if __name__ == "__main__":
    print("当前模型配置:", read_model_config())
    print("模型门槛（DeepSeek v4 生效）:", is_deepseek_v4_active())
