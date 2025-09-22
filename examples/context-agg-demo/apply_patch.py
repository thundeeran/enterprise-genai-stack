# examples/context-agg-demo/apply_patch.py
import re
from pathlib import Path

DIFF_BLOCK = re.compile(r"```diff(.*?)```", re.DOTALL)

def extract_diff(text: str) -> str:
    m = DIFF_BLOCK.search(text)
    return m.group(1).strip() if m else ""

def save_patch(diff_text: str, out_path: str = "proposed.patch"):
    Path(out_path).write_text(diff_text, encoding="utf-8")
    return out_path

if __name__ == "__main__":
    from context_aggregation import aggregate_context
    from prompt_and_llm import build_prompt, call_llm
    ctx = aggregate_context("JIRA-101", "auth/login.py")
    prompts = build_prompt(ctx)
    completion = call_llm(prompts["system"], prompts["user"])
    diff_text = extract_diff(completion)
    if not diff_text:
        raise SystemExit("No diff found in LLM output.")
    patch_path = save_patch(diff_text)
    print(f"Saved patch to {patch_path} (review before applying).")
