# CLAUDE.md — 项目工作约定

## 项目一句话

国产大模型德语能力评测:5 维框架 × ~50 case,专家人工 gold 标注 + LLM-judge 校准(分维度 TPR/TNR)。设计文档见 `docs/eval-design.md`,先读它再动手。

## 铁律(违反即返工)

1. **`reviewed: false` 的 case 不得进入正式跑测**——runner 默认强制此规则,`--include-unreviewed` 仅限冒烟测试,冒烟产物必须从 `results/outputs/` 删除(断点续跑会把冒烟结果当已完成跳过)。
2. **所有结论只来自实测数据**:文档/报告中不得出现演示用假数字;failure_hypothesis 字段是假设,不是结论,不得写进报告。
3. **人工标注(gold)与 case 德语审校必须由项目所有者本人完成**,AI 只能起草和归纳——这是「专家 gold」成立的前提。
4. `.env` 永不提交;代码里 key 只经环境变量引用。

## 环境

- Python 用 `.venv/`(基于 `/opt/homebrew/bin/python3.11` 创建;系统 /usr/bin/python3 是 3.9,别用)。
- pip 装包走**阿里云镜像**(`-i https://mirrors.aliyun.com/pypi/simple/`);清华镜像对本机持续 403。
- 跑测:`.venv/bin/python harness/run_models.py`;key 填在项目根 `.env`(参照 `.env.example`)。
- `harness/models.yaml` 中模型 id 是占位,跑前用各平台 `GET {base_url}/models` 核对当前旗舰型号。

## 当前状态与下一步

- 已完成:评测设计、15 条种子 case(全部待审校)、runner、related-work 调研,已推 GitHub(origin/main)。
- 闸门:种子 case 审校(所有者)→ 扩充至 ~50 → 正式跑测 → 盲标(随机序、隐藏模型名、一次性标完)→ judge 校准 → 报告。
- Judge 校准阶段计划加入 M-Prometheus 作为第二种 judge 配置对比。

## Git

- 远程:github.com/Janettbella69/Language-LLM-Eval(**public 仓库**——文档措辞保持中性、对外可读,内部工作背景不写入)。
- 提交信息用英文祈使句,说明「为什么」而非「改了什么」。
