#!/usr/bin/env python3
"""
Headless Agent Security Demo
============================
A runnable demonstration of secure autonomous agents in the SDLC.

This example shows:
- Scoped authorization (repo boundaries)
- Audit logging (immutable trail)
- Agent identity management
- Policy enforcement
- Error handling and security violations

Usage:
    python headless_agent_demo.py
"""

import json
import datetime
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from enum import Enum

# =============================================================================
# Configuration and Types
# =============================================================================

class ActionType(Enum):
    FILE_CREATE = "file_create"
    FILE_UPDATE = "file_update"
    FILE_DELETE = "file_delete"
    REPO_ACCESS = "repo_access"
    POLICY_CHECK = "policy_check"

@dataclass
class AuditEvent:
    timestamp: str
    agent_id: str
    action: ActionType
    repo: str
    resource: str
    success: bool
    details: Dict
    signature: str = ""

    def __post_init__(self):
        # Create a tamper-evident signature
        content = f"{self.timestamp}{self.agent_id}{self.action.value}{self.repo}{self.resource}{self.success}"
        self.signature = hashlib.sha256(content.encode()).hexdigest()[:16]

# =============================================================================
# Security Policy Engine
# =============================================================================

class SecurityPolicy:
    """Defines what agents can and cannot do"""
    
    def __init__(self):
        # Repository access control
        self.authorized_repos = {
            "sd-agentic-lab": ["agent-101", "agent-102"],
            "secure-repo": ["agent-101"],
            "public-docs": ["agent-101", "agent-102", "agent-103"]
        }
        
        # File operation policies
        self.restricted_files = {
            "*.key", "*.pem", "secrets.yaml", ".env"
        }
        
        # Action policies
        self.allowed_actions = {
            "agent-101": [ActionType.FILE_CREATE, ActionType.FILE_UPDATE, ActionType.REPO_ACCESS],
            "agent-102": [ActionType.FILE_CREATE, ActionType.FILE_UPDATE],
            "agent-103": [ActionType.FILE_CREATE]
        }

    def can_access_repo(self, agent_id: str, repo: str) -> bool:
        """Check if agent can access repository"""
        return repo in self.authorized_repos and agent_id in self.authorized_repos[repo]

    def can_perform_action(self, agent_id: str, action: ActionType) -> bool:
        """Check if agent can perform specific action"""
        return action in self.allowed_actions.get(agent_id, [])

    def is_file_restricted(self, filename: str) -> bool:
        """Check if file is restricted"""
        return any(filename.endswith(pattern.replace("*", "")) for pattern in self.restricted_files)

# =============================================================================
# Audit System
# =============================================================================

class AuditLogger:
    """Immutable audit logging system"""
    
    def __init__(self, log_path: Path):
        self.log_path = log_path
        self.events: List[AuditEvent] = []
        self._load_existing_log()

    def _load_existing_log(self):
        """Load existing audit events"""
        if self.log_path.exists():
            try:
                data = json.loads(self.log_path.read_text())
                self.events = [AuditEvent(**event) for event in data]
            except (json.JSONDecodeError, TypeError):
                print(f"[WARNING] Could not load existing audit log: {self.log_path}")

    def log_event(self, event: AuditEvent):
        """Add event to audit trail"""
        self.events.append(event)
        self._persist_log()
        
        # Print to console for demo
        status = "✅ SUCCESS" if event.success else "❌ FAILED"
        print(f"[AUDIT] {status} | {event.agent_id} | {event.action.value} | {event.repo}/{event.resource}")

    def _persist_log(self):
        """Write audit log to disk"""
        data = [asdict(event) for event in self.events]
        # Convert enum to string for JSON serialization
        for event_data in data:
            event_data['action'] = event_data['action'].value
        
        self.log_path.write_text(json.dumps(data, indent=2))

    def get_events_for_agent(self, agent_id: str) -> List[AuditEvent]:
        """Get all events for specific agent"""
        return [event for event in self.events if event.agent_id == agent_id]

    def verify_integrity(self) -> bool:
        """Verify audit log hasn't been tampered with"""
        for event in self.events:
            content = f"{event.timestamp}{event.agent_id}{event.action.value}{event.repo}{event.resource}{event.success}"
            expected_sig = hashlib.sha256(content.encode()).hexdigest()[:16]
            if event.signature != expected_sig:
                print(f"[SECURITY] Audit integrity violation detected for event: {event.timestamp}")
                return False
        return True

# =============================================================================
# Headless Agent Implementation
# =============================================================================

class HeadlessAgent:
    """Autonomous agent with security-by-design"""
    
    def __init__(self, agent_id: str, workspace_dir: Path, policy: SecurityPolicy, audit_logger: AuditLogger):
        self.agent_id = agent_id
        self.workspace_dir = workspace_dir
        self.policy = policy
        self.audit = audit_logger
        
        print(f"[INIT] Agent {self.agent_id} initialized with workspace: {workspace_dir}")

    def _create_audit_event(self, action: ActionType, repo: str, resource: str, success: bool, details: Dict = None) -> AuditEvent:
        """Create standardized audit event"""
        return AuditEvent(
            timestamp=datetime.datetime.utcnow().isoformat(),
            agent_id=self.agent_id,
            action=action,
            repo=repo,
            resource=resource,
            success=success,
            details=details or {}
        )

    def verify_access(self, repo: str) -> bool:
        """Verify agent can access repository"""
        can_access = self.policy.can_access_repo(self.agent_id, repo)
        
        event = self._create_audit_event(
            ActionType.REPO_ACCESS,
            repo,
            "access_check",
            can_access,
            {"reason": "authorized" if can_access else "unauthorized"}
        )
        self.audit.log_event(event)
        
        if not can_access:
            raise PermissionError(f"[SECURITY] Agent {self.agent_id} unauthorized for repo: {repo}")
        
        return True

    def create_file(self, repo: str, file_path: str, content: str) -> str:
        """Create a new file with security checks"""
        # Security checks
        self.verify_access(repo)
        
        if not self.policy.can_perform_action(self.agent_id, ActionType.FILE_CREATE):
            raise PermissionError(f"[SECURITY] Agent {self.agent_id} not authorized for file creation")
        
        if self.policy.is_file_restricted(file_path):
            raise PermissionError(f"[SECURITY] File {file_path} is restricted")
        
        # Perform action
        try:
            full_path = self.workspace_dir / repo / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text(content)
            
            commit_id = f"commit-{int(datetime.datetime.utcnow().timestamp())}"
            
            event = self._create_audit_event(
                ActionType.FILE_CREATE,
                repo,
                file_path,
                True,
                {"commit_id": commit_id, "content_hash": hashlib.md5(content.encode()).hexdigest()}
            )
            self.audit.log_event(event)
            
            return commit_id
            
        except Exception as e:
            event = self._create_audit_event(
                ActionType.FILE_CREATE,
                repo,
                file_path,
                False,
                {"error": str(e)}
            )
            self.audit.log_event(event)
            raise

    def update_file(self, repo: str, file_path: str, content: str) -> str:
        """Update existing file with security checks"""
        # Security checks
        self.verify_access(repo)
        
        if not self.policy.can_perform_action(self.agent_id, ActionType.FILE_UPDATE):
            raise PermissionError(f"[SECURITY] Agent {self.agent_id} not authorized for file updates")
        
        # Perform action
        try:
            full_path = self.workspace_dir / repo / file_path
            
            # Check if file exists
            if not full_path.exists():
                raise FileNotFoundError(f"File {file_path} does not exist")
            
            # Backup original content
            original_content = full_path.read_text()
            full_path.write_text(content)
            
            commit_id = f"commit-{int(datetime.datetime.utcnow().timestamp())}"
            
            event = self._create_audit_event(
                ActionType.FILE_UPDATE,
                repo,
                file_path,
                True,
                {
                    "commit_id": commit_id,
                    "original_hash": hashlib.md5(original_content.encode()).hexdigest(),
                    "new_hash": hashlib.md5(content.encode()).hexdigest()
                }
            )
            self.audit.log_event(event)
            
            return commit_id
            
        except Exception as e:
            event = self._create_audit_event(
                ActionType.FILE_UPDATE,
                repo,
                file_path,
                False,
                {"error": str(e)}
            )
            self.audit.log_event(event)
            raise

    def get_activity_summary(self) -> Dict:
        """Get summary of agent's activities"""
        events = self.audit.get_events_for_agent(self.agent_id)
        
        summary = {
            "agent_id": self.agent_id,
            "total_actions": len(events),
            "successful_actions": len([e for e in events if e.success]),
            "failed_actions": len([e for e in events if not e.success]),
            "repos_accessed": list(set(e.repo for e in events)),
            "action_types": list(set(e.action.value for e in events))
        }
        
        return summary

# =============================================================================
# Demo Runner
# =============================================================================

def run_demo():
    """Run the headless agent security demonstration"""
    print("=" * 60)
    print("🤖 HEADLESS AGENT SECURITY DEMONSTRATION")
    print("=" * 60)
    
    # Setup
    with tempfile.TemporaryDirectory() as temp_dir:
        workspace = Path(temp_dir)
        audit_log = workspace / "agent_audit.json"
        
        # Initialize components
        policy = SecurityPolicy()
        audit_logger = AuditLogger(audit_log)
        
        # Create agents with different permissions
        agent_101 = HeadlessAgent("agent-101", workspace, policy, audit_logger)
        agent_102 = HeadlessAgent("agent-102", workspace, policy, audit_logger)
        agent_103 = HeadlessAgent("agent-103", workspace, policy, audit_logger)
        
        print("\n📋 SECURITY POLICY LOADED:")
        print(f"   Authorized repos: {list(policy.authorized_repos.keys())}")
        print(f"   Restricted files: {policy.restricted_files}")
        
        print("\n🧪 RUNNING SECURITY TESTS:")
        print("-" * 40)
        
        # Test 1: Authorized operations
        print("\n1️⃣  Testing authorized operations...")
        try:
            commit1 = agent_101.create_file("secure-repo", "config.yaml", "logging: enabled\npolicy: strict\n")
            print(f"   ✅ File created successfully: {commit1}")
            
            commit2 = agent_101.update_file("secure-repo", "config.yaml", "logging: enabled\npolicy: strict\nversion: 2.0\n")
            print(f"   ✅ File updated successfully: {commit2}")
            
        except Exception as e:
            print(f"   ❌ Unexpected error: {e}")
        
        # Test 2: Unauthorized repo access
        print("\n2️⃣  Testing unauthorized repo access...")
        try:
            agent_102.create_file("secure-repo", "hack.txt", "unauthorized access")
            print("   ❌ Security failure: unauthorized access allowed!")
        except PermissionError as e:
            print(f"   ✅ Security working: {e}")
        
        # Test 3: Restricted file access
        print("\n3️⃣  Testing restricted file access...")
        try:
            agent_101.create_file("sd-agentic-lab", "secrets.key", "secret-data")
            print("   ❌ Security failure: restricted file created!")
        except PermissionError as e:
            print(f"   ✅ Security working: {e}")
        
        # Test 4: Action permission limits
        print("\n4️⃣  Testing action permission limits...")
        try:
            agent_103.update_file("public-docs", "readme.md", "updated content")
            print("   ❌ Security failure: unauthorized action allowed!")
        except PermissionError as e:
            print(f"   ✅ Security working: {e}")
        
        # Test 5: Successful operations for different agents
        print("\n5️⃣  Testing multi-agent operations...")
        try:
            agent_102.create_file("sd-agentic-lab", "feature.py", "# New feature implementation\nprint('Hello World')")
            agent_103.create_file("public-docs", "guide.md", "# User Guide\nWelcome to our platform!")
            print("   ✅ Multi-agent operations successful")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Display results
        print("\n📊 AUDIT SUMMARY:")
        print("-" * 40)
        
        for agent_id in ["agent-101", "agent-102", "agent-103"]:
            summary = HeadlessAgent(agent_id, workspace, policy, audit_logger).get_activity_summary()
            print(f"\n🤖 {agent_id}:")
            print(f"   Total actions: {summary['total_actions']}")
            print(f"   Successful: {summary['successful_actions']}")
            print(f"   Failed: {summary['failed_actions']}")
            print(f"   Repos accessed: {summary['repos_accessed']}")
        
        # Verify audit integrity
        print(f"\n🔒 AUDIT INTEGRITY CHECK:")
        integrity_ok = audit_logger.verify_integrity()
        print(f"   {'✅ PASSED' if integrity_ok else '❌ FAILED'}")
        
        # Show audit log location
        print(f"\n📄 AUDIT LOG SAVED TO: {audit_log}")
        if audit_log.exists():
            print(f"   Log size: {len(audit_logger.events)} events")
        
        print("\n" + "=" * 60)
        print("🎯 DEMONSTRATION COMPLETE")
        print("=" * 60)
        
        # Keep audit log for inspection
        permanent_log = Path("headless_agent_audit.json")
        if audit_log.exists():
            permanent_log.write_text(audit_log.read_text())
            print(f"📋 Audit log copied to: {permanent_log.absolute()}")

if __name__ == "__main__":
    run_demo()
