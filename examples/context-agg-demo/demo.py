#!/usr/bin/env python3
"""
Context Aggregation Demo - Complete End-to-End Workflow

This script demonstrates the complete context aggregation pipeline:
1. Aggregate context from multiple enterprise sources
2. Build AI prompt with comprehensive context
3. Generate code fix (simulated LLM response)
4. Extract and save the proposed patch

Run: python demo.py
"""

import sys
from pathlib import Path

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from context_aggregation import aggregate_context
from prompt_and_llm import build_prompt, call_llm
from apply_patch import extract_diff, save_patch


def main():
    """Run the complete context aggregation demo"""
    
    print("🚀 ENTERPRISE GENAI CONTEXT AGGREGATION DEMO")
    print("=" * 60)
    print()
    print("This demo shows how context aggregation transforms AI from")
    print("'spray-and-pray code edits' to 'precise, enterprise-safe automation'")
    print()
    
    # Step 1: Aggregate context from multiple sources
    print("STEP 1: Context Aggregation")
    print("-" * 30)
    
    ticket_id = "JIRA-101"
    file_path = "auth/login.py"
    
    ctx = aggregate_context(ticket_id, file_path)
    print()
    
    # Step 2: Build AI prompt with aggregated context
    print("STEP 2: Prompt Construction")
    print("-" * 30)
    
    prompts = build_prompt(ctx)
    
    print("✅ Built comprehensive prompt with:")
    print(f"   - System prompt: {len(prompts['system'])} characters")
    print(f"   - User prompt: {len(prompts['user'])} characters")
    print()
    
    # Show the complete user prompt with aggregated context
    print("📝 Complete User Prompt with Aggregated Context:")
    print("-" * 50)
    print(prompts['user'])
    print("-" * 50)
    print()
    
    # Step 3: Generate AI response (simulated)
    print("STEP 3: AI Code Generation")
    print("-" * 30)
    
    print("🤖 Calling LLM with aggregated context...")
    completion = call_llm(prompts["system"], prompts["user"])
    
    print("✅ LLM Response Generated:")
    print(f"   Length: {len(completion)} characters")
    print()
    
    # Show the AI response
    print("🔍 AI Response:")
    print("-" * 15)
    print(completion)
    print()
    
    # Step 4: Extract and save patch
    print("STEP 4: Patch Extraction")
    print("-" * 30)
    
    diff_text = extract_diff(completion)
    if not diff_text:
        print("❌ No diff found in LLM output")
        return 1
    
    patch_path = save_patch(diff_text, "context-demo.patch")
    print(f"✅ Saved patch to {patch_path}")
    print()
    
    # Step 5: Show the extracted diff
    print("📄 Extracted Diff:")
    print("-" * 18)
    print(diff_text)
    print()
    
    # Summary
    print("🎯 DEMO SUMMARY")
    print("=" * 60)
    print()
    print("Without context aggregation:")
    print("  ❌ AI would only see the TODO comment")
    print("  ❌ No understanding of business requirements")
    print("  ❌ No knowledge of test failures or CI errors")
    print("  ❌ No awareness of security policies")
    print("  ❌ Result: Generic, potentially unsafe fixes")
    print()
    print("With context aggregation:")
    print("  ✅ AI understands the JIRA ticket requirements")
    print("  ✅ AI sees the specific test failures and assertions")
    print("  ✅ AI knows about recent code changes and patterns")
    print("  ✅ AI follows enterprise security policies")
    print("  ✅ Result: Precise, compliant, reviewable fixes")
    print()
    print("💡 Key Insight:")
    print("   Context aggregation transforms AI from a 'script that guesses'")
    print("   into a 'context-aware teammate' that makes informed decisions.")
    print()
    print(f"📁 Files created:")
    print(f"   - {patch_path} (ready for review and git apply)")
    print()
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
