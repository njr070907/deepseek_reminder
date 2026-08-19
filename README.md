# 梁文谷/梁文峰 时间模式小产品

> **梁文谷/梁文峰 时间模式**是一个时间感知的应答风格切换小产品。它依据北京时间自动切换话风：普通模式（梁文谷）正常详尽地回复；极简模式（梁文峰）惜字如金，只保留必要结论，不复述、不扩展、不寒暄。切换前 10 分钟（08:50–09:00、13:50–14:00），回答末尾会提示"⚠️ 快到梁文峰时间了，建议停下"；用户明确要求详细回答时，一律以用户要求为准。
>
> 产品由四部分组成：**判定脚本**（纯函数实现，半开区间时间判定消除边界歧义，附带 23 组边界测试）；**提示词模板**（`{{beijing_time}}` 占位符，可接入任意模型或平台）；**Hermes 技能**（对话内自动按点切换话风）；**定时横幅提醒**（每天 08:50/13:50 北京时间、Hermes 运行时触发，右下角弹出带配图与倒计时文案的横幅，静音、可拖动、位置自动记忆）。
>
> 技术要点：北京时间采用 UTC+8 纯算术换算，不依赖系统时区库；提醒采用"看门狗"模式——只在规定窗口内输出，窗口外完全静默，绝不错时打扰。

> **Liangwen Time-Mode** is a time-aware reply-style switcher. Based on Beijing time, it automatically switches between two modes: **Normal (Liangwengu)** — full, detailed replies; and **Minimal (Liangwenfeng)** — concise replies that keep only the necessary conclusion: no repetition, no elaboration, no small talk. Ten minutes before each switch (08:50–09:00 and 13:50–14:00 Beijing time), replies get a trailing warning: "⚠️ Almost Liangwenfeng time — consider wrapping up." Explicit user requests for detailed answers always take priority.
>
> The product has four parts: a **judgment script** (pure-function, half-open interval time windows, 23 boundary test cases), a **prompt template** (with a `{{beijing_time}}` placeholder, usable with any model or platform), a **Hermes skill** (auto-applies the style in conversations), and a **scheduled banner reminder** (fires at 08:50/13:50 Beijing time while Hermes is running; shows a bottom-right banner with an image, countdown text, silent, draggable, with position memory).
>
> Technical highlights: Beijing time is computed via pure UTC+8 arithmetic (no system timezone database dependency); the reminder follows a watchdog pattern — it outputs only inside the designated windows and stays completely silent otherwise.

按北京时间自动切换回复风格：

| 模式 | 时间段（半开区间） |
|---|---|
| 梁文谷·普通 | [00:00, 09:00) / [12:00, 14:00) / [18:00, 24:00) |
| 梁文峰·极简 | [09:00, 12:00) / [14:00, 18:00) |
| 附加提醒（仍属普通模式） | [08:50, 09:00) / [13:50, 14:00)，末尾追加「⚠️ 快到梁文峰时间了，建议停下。」 |

优先级：用户明确要求详细 > 时间规则；未提供时间 → 默认极简。

## 文件

- `time_mode.py` — 判定脚本（核心逻辑 + 边界测试）
- `mode_prompt.md` — 提示词模板，`{{beijing_time}}` 为占位符

## 用法

```bash
# 未提供时间 → 默认梁文峰
python time_mode.py

# 取当前北京时间判定（UTC+8 纯算术换算，不依赖系统时区库）
python time_mode.py --now

# 指定时间判定
python time_mode.py --time 13:55
python time_mode.py --time 09:00:00

# 边界测试（18 组边界 + 6 组非法输入）
python time_mode.py --selftest
```

## 接入方式

本产品已做成 Hermes 技能 `liangwen-time-mode`（规则文件在 Hermes 数据目录，本目录为源文件）。技能生效后自动按北京时间切换话风，无需手动填时间。

手动使用（模板填充）：
1. 运行 `python time_mode.py --now` 取当前北京时间（或由你的宿主程序注入）。
2. 把 `mode_prompt.md` 中的 `{{beijing_time}}` 替换成该时间，作为系统提示词/角色设定使用。
3. 每次对话前重新注入时间即可；提醒窗口已内置于规则，无需额外定时任务。

## 定时提醒（cron）

- 任务：`梁文峰临近提醒`（每天 08:50/13:50 北京时间；Hermes 运行时才触发）
- 链路：Hermes cron → `cron_reminder_launcher.py`（hermes/scripts 桥梁）→ 本目录 `cron_reminder.py`
- 触发时：输出文案 + 右下角弹出横幅提醒（自绘窗口：`梁圣.jpg` 配图 + 倒计时文案 + 静音，25 秒自动消失；**可拖动、位置自动记忆**（`banner_pos.txt`）、点击即关；默认在工作区即任务栏上方，不遮挡任务栏）
- 个性化：改 `cron_reminder.py` 顶部「个性化配置区」（文案模板、标题、静音开关、配图路径、通知方式、横幅秒数）
- 查看任务/输出：`cronjob(action='list')`（当前无投递通道，输出仅存档）

## 一键查看当前模式（桌面按键）

- 桌面快捷方式「**deepseek_reminder**」（双击即弹）：判定当前北京时间 → 显示当前模式 + 对应图片
  - 梁文谷时间 → **小南梁.jpg**；梁文峰时间 → **梁圣.jpg**；提醒窗口内附「⚠️ 快到梁文峰时间了」
  - 横幅 20 秒自动消失，可拖动、位置自动记忆（与定时提醒共用同一位置）
- 相关文件：`status_check.py`（判定+弹窗）、`banner_ui.py`（横幅共用模块）、`make_shortcut.py`（重建快捷方式：`python make_shortcut.py`；图标来自 `图标.jpg`，自动转 `图标.ico`）
- 定时提醒与一键查看**共用同一横幅实现**，要改样式只动 `banner_ui.py` 一处

## 已知坑

- 本机 git-bash 的 `date` 会忽略 `TZ=Asia/Shanghai` 并回退为 UTC（无时区数据库）。
  判时间请用 `python time_mode.py --now` 或本机 Windows 本地时间（已是中国标准时间）。
- 脚本只认传入的北京时间；机器时钟若不准，以网络时间 API（如 timeapi.io）为准校准。
- 直连 GitHub 偶发不通（亚洲节点 20.205.243.166 常被干扰）：git 已配置走本地代理
  `http://127.0.0.1:7897`；若代理关闭导致推送失败，恢复直连用
  `git config --global --unset http.proxy`。
