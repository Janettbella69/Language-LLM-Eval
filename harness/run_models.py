#!/usr/bin/env python3
"""跑评测:cases/*.jsonl × models.yaml 里 enabled 的模型 → results/outputs/<model>.jsonl

用法:
    pip install openai pyyaml   # 清华镜像已配
    export DEEPSEEK_API_KEY=... # 按 models.yaml 启用的模型逐个 export
    python harness/run_models.py [--cases cases/seed_cases.jsonl] [--only deepseek,kimi]

- 只跑 reviewed: true 的 case(未审校的 case 不产生正式数据);--include-unreviewed 可覆盖(冒烟测试用)
- 断点续跑:已有输出的 (model, case_id) 自动跳过
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

import yaml
from openai import OpenAI

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "results" / "outputs"


def load_dotenv(path: Path) -> None:
    """读取项目根 .env;已存在的环境变量优先,不被覆盖。"""
    if not path.exists():
        return
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        k, v = k.strip(), v.strip().strip('"').strip("'")
        if k and v and k not in os.environ:
            os.environ[k] = v


def load_cases(path: Path, include_unreviewed: bool) -> list[dict]:
    cases = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not include_unreviewed:
        skipped = [c["id"] for c in cases if not c.get("reviewed")]
        cases = [c for c in cases if c.get("reviewed")]
        if skipped:
            print(f"[skip] {len(skipped)} 条未审校 case 不跑(--include-unreviewed 可覆盖): {', '.join(skipped)}")
    return cases


def load_models(only: set[str] | None) -> tuple[list[dict], dict]:
    cfg = yaml.safe_load((ROOT / "harness" / "models.yaml").read_text(encoding="utf-8"))
    models = [m for m in cfg["models"] if m.get("enabled")]
    if only:
        models = [m for m in models if m["name"] in only]
    for m in models:
        if not os.environ.get(m["api_key_env"]):
            sys.exit(f"[error] {m['name']} 已启用但环境变量 {m['api_key_env']} 未设置")
    return models, cfg["defaults"]


def existing_ids(out_path: Path) -> set[str]:
    if not out_path.exists():
        return set()
    return {json.loads(l)["case_id"] for l in out_path.read_text(encoding="utf-8").splitlines() if l.strip()}


def call_model(client: OpenAI, model_id: str, prompt: str, defaults: dict) -> str:
    resp = client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": prompt}],
        temperature=defaults["temperature"],
        max_tokens=defaults["max_tokens"],
    )
    return resp.choices[0].message.content or ""


def main() -> None:
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default="cases/seed_cases.jsonl")
    ap.add_argument("--only", help="逗号分隔的模型名,只跑这些")
    ap.add_argument("--include-unreviewed", action="store_true")
    args = ap.parse_args()

    cases = load_cases(ROOT / args.cases, args.include_unreviewed)
    models, defaults = load_models(set(args.only.split(",")) if args.only else None)
    if not cases or not models:
        sys.exit("[error] 没有可跑的 case 或模型(检查 reviewed 状态 / models.yaml 的 enabled)")

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"计划: {len(models)} 模型 × {len(cases)} case")

    for m in models:
        client = OpenAI(api_key=os.environ[m["api_key_env"]], base_url=m["base_url"])
        out_path = OUT_DIR / f"{m['name']}.jsonl"
        done = existing_ids(out_path)
        todo = [c for c in cases if c["id"] not in done]
        print(f"\n== {m['name']} ({m['model']}): {len(todo)} 待跑, {len(done)} 已有 ==")
        with out_path.open("a", encoding="utf-8") as f:
            for i, c in enumerate(todo, 1):
                for attempt in range(defaults["n_retries"]):
                    try:
                        text = call_model(client, m["model"], c["prompt"], defaults)
                        break
                    except Exception as e:
                        wait = 2 ** (attempt + 1)
                        print(f"  [retry {attempt + 1}] {c['id']}: {e} — {wait}s 后重试")
                        time.sleep(wait)
                else:
                    print(f"  [FAIL] {c['id']} 重试耗尽,跳过")
                    continue
                f.write(json.dumps({
                    "case_id": c["id"], "model": m["name"], "model_id": m["model"],
                    "output": text,
                }, ensure_ascii=False) + "\n")
                f.flush()
                print(f"  [{i}/{len(todo)}] {c['id']} ok ({len(text)} chars)")

    print("\n完成。输出在 results/outputs/,下一步:人工标注(盲标,顺序随机化)。")


if __name__ == "__main__":
    main()
