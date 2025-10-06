# Headless Agent Security Demo

This is a standalone, runnable demonstration of the security concepts described in the "When AI Acts Alone" article.

## What This Demonstrates

- **Scoped Authorization**: Agents can only access authorized repositories
- **Action Permissions**: Different agents have different capabilities
- **Audit Logging**: Every action is logged with tamper-evident signatures
- **Policy Enforcement**: Restricted files and unauthorized actions are blocked
- **Identity Management**: Each agent has a unique identity and permissions

## Quick Start

```bash
# Run the demo (no dependencies needed - uses Python standard library)
python3 headless_agent_security_demo.py
```

## What You'll See

The demo creates three agents with different permission levels:
- `agent-101`: Full permissions (create, update, access multiple repos)
- `agent-102`: Limited permissions (create, update, but restricted repos)
- `agent-103`: Minimal permissions (create only, public repos only)

It then runs security tests to show:
1. ✅ Authorized operations succeed
2. ❌ Unauthorized repo access is blocked
3. ❌ Restricted file access is blocked  
4. ❌ Action permission violations are blocked
5. ✅ Multi-agent operations work within bounds

## Output Files

- `headless_agent_audit.json`: Complete audit trail of all agent actions
- Console output showing real-time security enforcement

## Key Security Features

| Feature | Implementation |
|---------|----------------|
| **Access Control** | Repository-scoped authorization lists |
| **Auditability** | Immutable, signed audit events |
| **Accountability** | Agent identity tracking |
| **Tamper Resistance** | SHA-256 signatures on audit events |
| **Policy Enforcement** | File restrictions and action limits |

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  Headless Agent │───▶│ Security Policy  │───▶│  Audit Logger   │
│                 │    │                  │    │                 │
│ - Agent ID      │    │ - Repo Access    │    │ - Event Trail   │
│ - Actions       │    │ - File Rules     │    │ - Signatures    │
│ - Workspace     │    │ - Permissions    │    │ - Integrity     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

This demonstrates how autonomous agents can operate safely within enterprise environments through proper security boundaries and governance.
