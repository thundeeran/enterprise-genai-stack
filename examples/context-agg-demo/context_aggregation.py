# examples/context-agg-demo/context_aggregation.py
"""
Context Aggregation Demo - Simulates collecting signals from multiple sources
to provide comprehensive context for AI-driven code fixes.

This demonstrates the concept from the LinkedIn post: instead of feeding AI
raw text from a single file, we aggregate multiple signals to give it a
360° view of the problem.
"""

from dataclasses import dataclass
from typing import Dict, List, Any
import json


@dataclass
class ContextBundle:
    """Aggregated context from multiple enterprise sources"""
    jira: Dict[str, Any]
    file_path: str
    file_content: str
    history: List[Dict[str, Any]]
    failures: List[Dict[str, Any]]
    pipeline: Dict[str, Any]
    policies: List[str]


def get_jira_context(ticket_id: str) -> Dict[str, Any]:
    """Simulate fetching JIRA ticket details"""
    # In real implementation, this would call JIRA API
    jira_data = {
        "JIRA-101": {
            "id": "JIRA-101",
            "title": "Password reset login fails with 500 error",
            "description": "Users cannot log in after password reset. The reset token validation is missing, causing authentication failures.",
            "priority": "High",
            "assignee": "dev-team",
            "labels": ["security", "auth", "bug"]
        }
    }
    return jira_data.get(ticket_id, {})


def get_file_content(file_path: str) -> str:
    """Simulate fetching current file content"""
    # In real implementation, this would read from git or filesystem
    sample_files = {
        "auth/login.py": '''def login(user, password, reset_token=None):
    """Authenticate user with optional password reset token"""
    if reset_token:
        # TODO: validate reset token
        pass
    
    if not check_password(user, password):
        raise AuthError("Invalid credentials")
    
    return issue_session(user)

def check_password(user, password):
    """Verify user password against stored hash"""
    return user.password_hash == hash_password(password)

def issue_session(user):
    """Create authenticated session for user"""
    return {"session_id": generate_session_id(), "user_id": user.id}
'''
    }
    return sample_files.get(file_path, "# File not found")


def get_repo_history(file_path: str, limit: int = 3) -> List[Dict[str, Any]]:
    """Simulate fetching recent git history for the file"""
    # In real implementation, this would call git log
    history_data = {
        "auth/login.py": [
            {
                "commit": "a1b2c3d",
                "author": "alice@company.com",
                "message": "Add password reset token parameter",
                "timestamp": "2025-09-20T14:30:00Z",
                "diff_snippet": '''@@ -1,4 +1,6 @@
-def login(user, password):
+def login(user, password, reset_token=None):
     """Authenticate user"""
+    if reset_token:
+        # TODO: validate reset token
+        pass
     if not check_password(user, password):'''
            },
            {
                "commit": "e4f5g6h",
                "author": "bob@company.com", 
                "message": "Refactor authentication error handling",
                "timestamp": "2025-09-19T09:15:00Z",
                "diff_snippet": '''@@ -5,7 +5,7 @@
     if not check_password(user, password):
-        return None
+        raise AuthError("Invalid credentials")
     
     return issue_session(user)'''
            }
        ]
    }
    return history_data.get(file_path, [])[:limit]


def get_test_failures(file_path: str) -> List[Dict[str, Any]]:
    """Simulate fetching recent test failures related to the file"""
    # In real implementation, this would parse CI/CD test results
    failure_data = {
        "auth/login.py": [
            {
                "test": "test_login_with_reset_token",
                "assertion": "Expected status 200, got 500",
                "error_message": "AuthError: Invalid reset token",
                "test_snippet": '''def test_login_with_reset_token():
    user = create_test_user()
    reset_token = generate_reset_token(user)
    
    response = login(user, "new_password", reset_token)
    assert response.status_code == 200  # FAILING HERE
    assert response.user_id == user.id''',
                "target_snippet": '''if reset_token:
    # TODO: validate reset token
    pass  # This is where validation should happen'''
            },
            {
                "test": "test_reset_token_validation",
                "assertion": "Expected verify_reset_token to be called",
                "error_message": "Mock not called",
                "test_snippet": '''def test_reset_token_validation():
    with patch('auth.verify_reset_token') as mock_verify:
        mock_verify.return_value = True
        login(user, "password", "token123")
        mock_verify.assert_called_once()  # FAILING HERE''',
                "target_snippet": '''if reset_token:
    # TODO: validate reset token
    pass  # Missing actual validation call'''
            }
        ]
    }
    return failure_data.get(file_path, [])


def get_pipeline_context(file_path: str) -> Dict[str, Any]:
    """Simulate fetching CI/CD pipeline information"""
    # In real implementation, this would call Jenkins/GitHub Actions/etc API
    pipeline_data = {
        "auth/login.py": {
            "build_id": "build-456",
            "status": "failed",
            "stage": "test",
            "error_logs": '''FAILED tests/test_auth.py::test_login_with_reset_token - AssertionError: Expected status 200, got 500
FAILED tests/test_auth.py::test_reset_token_validation - AssertionError: Mock not called
=== 2 failed, 15 passed in 12.34s ===

Error details:
  File "auth/login.py", line 3, in login
    pass  # TODO: validate reset token
AuthError: Invalid reset token''',
            "duration": "12.34s",
            "failed_tests": 2,
            "passed_tests": 15
        }
    }
    return pipeline_data.get(file_path, {})


def get_security_policies() -> List[str]:
    """Simulate fetching relevant security policies"""
    # In real implementation, this would query policy management system
    return [
        "All authentication tokens must be validated before use",
        "Password reset tokens must expire within 24 hours",
        "Authentication failures must not leak sensitive information",
        "All security-related changes require code review approval",
        "Secrets and tokens must never be logged in plain text"
    ]


def aggregate_context(ticket_id: str, file_path: str) -> ContextBundle:
    """
    Main function: Aggregate context from multiple enterprise sources
    
    This simulates the real-world process of collecting signals from:
    - JIRA (business context, requirements)
    - Git history (code evolution, patterns)
    - Test failures (specific failure modes)
    - CI/CD pipelines (build context, error logs)
    - Security policies (compliance requirements)
    """
    
    print(f"🔄 Aggregating context for {ticket_id} -> {file_path}")
    
    # Collect signals from different sources
    jira = get_jira_context(ticket_id)
    file_content = get_file_content(file_path)
    history = get_repo_history(file_path)
    failures = get_test_failures(file_path)
    pipeline = get_pipeline_context(file_path)
    policies = get_security_policies()
    
    print(f"✅ Context aggregated:")
    print(f"   - JIRA: {jira.get('title', 'N/A')}")
    print(f"   - History: {len(history)} commits")
    print(f"   - Failures: {len(failures)} test failures")
    print(f"   - Pipeline: {pipeline.get('status', 'N/A')}")
    print(f"   - Policies: {len(policies)} rules")
    
    return ContextBundle(
        jira=jira,
        file_path=file_path,
        file_content=file_content,
        history=history,
        failures=failures,
        pipeline=pipeline,
        policies=policies
    )


if __name__ == "__main__":
    # Demo the context aggregation
    ctx = aggregate_context("JIRA-101", "auth/login.py")
    
    print("\n" + "="*60)
    print("CONTEXT AGGREGATION DEMO")
    print("="*60)
    
    print(f"\n📋 JIRA Context:")
    print(f"   {ctx.jira['id']}: {ctx.jira['title']}")
    print(f"   Priority: {ctx.jira['priority']}")
    
    print(f"\n📁 File Context:")
    print(f"   Path: {ctx.file_path}")
    print(f"   Content: {len(ctx.file_content)} characters")
    
    print(f"\n📚 History Context:")
    for commit in ctx.history:
        print(f"   - {commit['commit'][:7]} by {commit['author']}: {commit['message']}")
    
    print(f"\n❌ Failure Context:")
    for failure in ctx.failures:
        print(f"   - {failure['test']}: {failure['assertion']}")
    
    print(f"\n🔧 Pipeline Context:")
    print(f"   Build: {ctx.pipeline['build_id']} ({ctx.pipeline['status']})")
    print(f"   Tests: {ctx.pipeline['failed_tests']} failed, {ctx.pipeline['passed_tests']} passed")
    
    print(f"\n🔒 Policy Context:")
    for policy in ctx.policies[:3]:  # Show first 3
        print(f"   - {policy}")
    
    print(f"\n💡 This aggregated context provides the AI with:")
    print(f"   ✓ Business requirements (JIRA)")
    print(f"   ✓ Code patterns and history (Git)")
    print(f"   ✓ Specific failure modes (Tests)")
    print(f"   ✓ Build environment (CI/CD)")
    print(f"   ✓ Compliance constraints (Policies)")
    print(f"\n   Instead of guessing, the AI can make informed decisions!")