# examples/context-agg-demo/prompt_and_llm.py
import textwrap
from typing import Dict, Any, List
from context_aggregation import aggregate_context

# --- Replace with your real LLM client (OpenAI/Anthropic/etc.) ---
def call_llm(system_prompt: str, user_prompt: str) -> str:
    # Return a minimal diff + rationale for deterministic downstream parsing.
    return textwrap.dedent("""\
    ```diff
    --- a/auth/login.py
    +++ b/auth/login.py
    @@
     def login(user, password, reset_token=None):
-        if reset_token:
-            # TODO: validate later
-            pass
+        if reset_token:
+            # Validate reset token per policy
+            if not verify_reset_token(reset_token, user):
+                raise AuthError("Invalid reset token")

         if not check_password(user, password):
             raise AuthError("Bad credentials")
         return issue_session(user)
    ```
    # Rationale
    - Adds verify_reset_token() to align with policy
    - Addresses failing assertion (expected 200 after reset)
    - Keeps change minimal; avoids logging secrets
    """)

# --- Small helpers to keep prompt compact ---
def clip(text: str, max_chars: int = 700) -> str:
    return (text[: max_chars - 3] + "...") if len(text) > max_chars else text

def compress_history(history: List[Dict[str, Any]], max_items: int = 2, max_snip: int = 600) -> str:
    rows = []
    for h in history[:max_items]:
        rows.append(textwrap.dedent(f"""\
        - Commit {h['commit']} by {h['author']}: {h['message']}
          Diff excerpt:
{indent_block(clip(h.get('diff_snippet', ''), max_snip), '            ')}
        """))
    return "\n".join(rows)

def format_failures(failures: List[Dict[str, Any]], max_snip: int = 600) -> str:
    out = []
    for f in failures:
        out.append(textwrap.dedent(f"""\
        • {f['test']}
          Assertion: {f['assertion']}
          Test excerpt:
{indent_block(clip(f.get('test_snippet', ''), max_snip), '            ')}
          Target excerpt:
{indent_block(clip(f.get('target_snippet', ''), max_snip), '            ')}
        """))
    return "\n".join(out)

def indent_block(s: str, pad: str = "    ") -> str:
    return "\n".join(pad + line for line in s.splitlines())

def build_prompt(ctx: Any) -> Dict[str, str]:
    system = textwrap.dedent("""\
    You are an enterprise-safe autonomous code agent.
    Follow policies, produce minimal diffs, and NEVER output secrets.
    Output MUST begin with a unified diff fenced in ```diff followed by a short '# Rationale'.
    """)

    user = textwrap.dedent(f"""\
    TASK: Propose a minimal code change to fix the failing login after password reset.

    ## Constraints
    - Respect enterprise policy snippets below
    - Do not log or expose secrets
    - Keep PR small and reviewable

    ## JIRA
    [{ctx.jira['id']}] {ctx.jira['title']}
    {ctx.jira['description']}

    ## File
    {ctx.file_path}

    ## Recent History (focused diffs)
    {compress_history(ctx.history)}

    ## Test Failures (assert + relevant code)
    {format_failures(ctx.failures)}

    ## CI Error Logs (excerpt)
    {indent_block(clip(ctx.pipeline.get('error_logs', ''), 900), '    ')}

    ## Policy Snippets
    {chr(10).join('- ' + p for p in ctx.policies)}

    ## Output format
    1) A single unified diff in a ```diff fenced block (no extra text before it)
    2) Then a short '# Rationale' explaining the fix and policy adherence
    """)

    return {"system": system, "user": user}

if __name__ == "__main__":
    ctx = aggregate_context("JIRA-101", "auth/login.py")
    prompts = build_prompt(ctx)
    completion = call_llm(prompts["system"], prompts["user"])
    print(completion)
