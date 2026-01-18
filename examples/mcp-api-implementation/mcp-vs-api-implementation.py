"""
MCP vs API Integrations - DETAILED Code Implementation
=======================================================

CRITICAL QUESTION ANSWERED:
---------------------------
"If MCP still calls the same backend services, what's the real difference?"

The backend calls STILL HAPPEN. The difference is:
1. WHERE the orchestration happens (centralized proxy vs distributed agents)
2. WHO applies governance (proxy with consistent policy vs agent with client-side logic)
3. WHAT data flows to the agent (filtered minimum vs full raw data)
4. HOW connections are managed (pooled/cached vs per-agent connections)
5. WHEN audit/provenance is captured (built-in vs none)

This example makes these differences crystal clear.

Use Case: Loan Application Assessment
"""

import asyncio
import json
from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, timedelta
from enum import Enum
import uuid

# ============================================================================
# BACKEND SERVICES (Same for BOTH approaches)
# These are the actual data sources that BOTH approaches must call
# ============================================================================

print("=" * 90)
print("BACKEND SERVICES (Exist regardless of approach)")
print("=" * 90)
print("""
These backend services exist in your enterprise. BOTH approaches must get data from them.
The question is: WHO calls them, HOW, and WHAT gets returned to the agent?

┌─────────────────────────────────────────────────────────────────────────────────────┐
│                           ENTERPRISE BACKEND SERVICES                                │
├─────────────────────────────────────────────────────────────────────────────────────┤
│  🏦 Customer Service    │  Core banking customer profiles                           │
│  💰 Account Service     │  Account balances, transaction history                    │
│  📊 Credit Bureau API   │  External credit scores (Experian, Equifax, etc.)         │
│  🏠 Property Service    │  Real estate valuations, collateral data                  │
│  📜 Policy Service      │  Lending rules, compliance requirements                   │
└─────────────────────────────────────────────────────────────────────────────────────┘
""")


class BackendServices:
    """
    Simulates the actual backend services in the enterprise.
    These are IDENTICAL for both approaches - the data sources don't change.
    """
    
    call_log: List[Dict] = []  # Track all backend calls for comparison
    
    @classmethod
    def reset_log(cls):
        cls.call_log = []
    
    @classmethod
    async def customer_service_get_profile(cls, customer_id: str, caller: str) -> Dict:
        """Real backend service - returns FULL customer data"""
        cls.call_log.append({
            "service": "Customer Service",
            "operation": f"GET /customers/{customer_id}",
            "caller": caller,
            "data_size": "2.1 KB",
            "includes_sensitive": True
        })
        await asyncio.sleep(0.08)
        
        # Backend ALWAYS returns full data - it doesn't know the purpose
        return {
            "customer_id": customer_id,
            "name": "John Smith",
            "email": "john.smith@email.com",
            "phone": "+1-555-0123",
            "address": "123 Main St, Anytown, USA 12345",
            "date_of_birth": "1985-03-15",
            "employment_status": "employed",
            "employer": "TechCorp Inc.",
            "annual_income": 85000.00,
            "ssn": "123-45-6789",                    # 🔴 SENSITIVE
            "internal_credit_flag": "A+",            # 🔴 INTERNAL
            "internal_notes": "VIP - handle with care",  # 🔴 INTERNAL
            "marketing_preferences": {...},          # Unnecessary for loan
            "last_login": "2024-01-15T10:30:00Z",   # Unnecessary for loan
        }
    
    @classmethod
    async def account_service_get_history(cls, customer_id: str, caller: str) -> Dict:
        """Real backend service - returns FULL account history"""
        cls.call_log.append({
            "service": "Account Service", 
            "operation": f"GET /accounts/{customer_id}/history",
            "caller": caller,
            "data_size": "847 KB",  # Large due to transactions!
            "includes_sensitive": True
        })
        await asyncio.sleep(0.12)
        
        return {
            "account_id": "ACC-001",
            "customer_id": customer_id,
            "balance": 15420.50,
            "avg_monthly_balance": 12500.00,
            "overdraft_count": 1,
            "account_age_months": 36,
            "account_type": "checking",
            "routing_number": "021000021",           # 🔴 SENSITIVE
            "account_number": "1234567890",          # 🔴 SENSITIVE
            "transactions": [                        # 🔴 MASSIVE - 1000 transactions!
                {"id": f"TXN-{i}", "date": "2024-01-01", "amount": 100.00, 
                 "merchant": "Store", "category": "retail"}
                for i in range(1000)
            ],
            "pending_transactions": [...],
            "recurring_payments": [...],
        }
    
    @classmethod
    async def credit_bureau_get_score(cls, customer_id: str, caller: str) -> Dict:
        """External credit bureau API - returns full credit report"""
        cls.call_log.append({
            "service": "Credit Bureau (External)",
            "operation": f"POST /v2/credit-report/{customer_id}",
            "caller": caller,
            "data_size": "156 KB",
            "includes_sensitive": True,
            "cost": "$0.50"  # External APIs often have per-call costs
        })
        await asyncio.sleep(0.25)  # External APIs are slower
        
        return {
            "customer_id": customer_id,
            "score": 720,
            "rating": "Good",
            "score_factors": [
                "Length of credit history: Positive",
                "Payment history: Positive", 
                "Credit utilization: Moderate"
            ],
            "full_credit_report": {                  # 🔴 DETAILED REPORT
                "trade_lines": [...],                # All credit accounts
                "inquiries": [...],                  # All credit checks
                "public_records": [...],             # Bankruptcies, liens
                "collections": [...],                # Collection accounts
            },
            "previous_scores": [...],                # Historical scores
            "dispute_history": [...],                # 🔴 SENSITIVE
        }
    
    @classmethod
    async def property_service_get_valuation(cls, property_id: str, caller: str) -> Dict:
        """Property valuation service"""
        cls.call_log.append({
            "service": "Property Service",
            "operation": f"GET /properties/{property_id}/valuation",
            "caller": caller,
            "data_size": "12 KB",
            "includes_sensitive": False
        })
        await asyncio.sleep(0.10)
        
        return {
            "property_id": property_id,
            "estimated_value": 350000.00,
            "last_appraisal_date": "2024-06-15",
            "property_type": "single_family",
            "address": "456 Oak Avenue, Somewhere, USA",
            "square_footage": 2200,
            "lot_size": 0.25,
            "year_built": 1998,
            "comparable_sales": [...],               # Not needed for decision
            "neighborhood_data": {...},              # Not needed for decision
        }
    
    @classmethod
    async def policy_service_get_lending_rules(cls, caller: str) -> Dict:
        """Lending policy service"""
        cls.call_log.append({
            "service": "Policy Service",
            "operation": "GET /policies/lending/current",
            "caller": caller,
            "data_size": "3 KB",
            "includes_sensitive": False
        })
        await asyncio.sleep(0.05)
        
        return {
            "policy_id": "LEND-2024-Q1",
            "version": "2024.1.3",
            "effective_date": "2024-01-01",
            "min_credit_score": 650,
            "max_dti_ratio": 0.43,
            "min_account_age_months": 12,
            "max_loan_to_value": 0.80,
            "excluded_property_types": ["mobile_home", "timeshare"],
            "regional_adjustments": {...},           # Complex rules
            "exception_criteria": {...},             # Internal rules
        }


# ============================================================================
# APPROACH 1: TRADITIONAL API - Agent calls backends DIRECTLY
# ============================================================================

print("\n" + "=" * 90)
print("APPROACH 1: TRADITIONAL API INTEGRATION")
print("=" * 90)
print("""
In this approach:
• Agent makes 5 DIRECT calls to backend services
• Agent receives FULL, UNFILTERED data from each service
• Agent must handle: errors, timeouts, retries, stitching
• NO governance layer - agent sees everything
• NO audit trail - calls not tracked centrally
• Each agent manages its own connections

         ┌─────────┐
         │  Agent  │
         └────┬────┘
              │
    ┌─────────┼─────────┬─────────┬─────────┬─────────┐
    │         │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼         ▼
┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐
│Customer│ │Account│ │Credit │ │Property│ │Policy │
│Service│ │Service│ │Bureau │ │Service│ │Service│
└───────┘ └───────┘ └───────┘ └───────┘ └───────┘
    │         │         │         │         │
    ▼         ▼         ▼         ▼         ▼
  FULL      FULL      FULL      FULL      FULL
  DATA      DATA      DATA      DATA      DATA
    │         │         │         │         │
    └─────────┴─────────┴─────────┴─────────┘
                        │
                        ▼
              Agent receives ALL data
              (sensitive, unnecessary, massive)
""")


class TraditionalLoanAgent:
    """
    Traditional Agent: Calls each backend service directly.
    Must handle all orchestration, errors, and stitching itself.
    """
    
    def __init__(self, agent_id: str):
        self.agent_id = agent_id
        self.caller_name = f"TraditionalAgent:{agent_id}"
    
    async def assess_loan(self, applicant_id: str, property_id: str, 
                          requested_amount: float) -> Dict[str, Any]:
        
        print(f"\n🤖 Traditional Agent [{self.agent_id}]: Starting loan assessment")
        print(f"   Agent will make 5 DIRECT calls to backend services\n")
        
        start_time = datetime.now()
        data_received = []
        
        # ═══════════════════════════════════════════════════════════════════
        # Call 1: Customer Service (DIRECT - no governance)
        # ═══════════════════════════════════════════════════════════════════
        print("   📞 Call 1: GET Customer Profile (DIRECT to backend)")
        customer = await BackendServices.customer_service_get_profile(
            applicant_id, self.caller_name
        )
        data_received.append({
            "source": "Customer Service",
            "fields_received": len(customer),
            "sensitive_exposed": ["ssn", "internal_notes", "internal_credit_flag"],
            "data_size": "2.1 KB"
        })
        print(f"      ⚠️  Received {len(customer)} fields including SSN, internal notes")
        
        # ═══════════════════════════════════════════════════════════════════
        # Call 2: Account Service (DIRECT - receives 1000 transactions!)
        # ═══════════════════════════════════════════════════════════════════
        print("   📞 Call 2: GET Account History (DIRECT to backend)")
        account = await BackendServices.account_service_get_history(
            applicant_id, self.caller_name
        )
        data_received.append({
            "source": "Account Service",
            "fields_received": len(account),
            "transactions_received": len(account.get("transactions", [])),
            "sensitive_exposed": ["account_number", "routing_number"],
            "data_size": "847 KB"
        })
        print(f"      ⚠️  Received {len(account['transactions'])} transactions (847 KB!)")
        
        # ═══════════════════════════════════════════════════════════════════
        # Call 3: Credit Bureau (DIRECT - external, costs money)
        # ═══════════════════════════════════════════════════════════════════
        print("   📞 Call 3: GET Credit Score (DIRECT to external bureau)")
        credit = await BackendServices.credit_bureau_get_score(
            applicant_id, self.caller_name
        )
        data_received.append({
            "source": "Credit Bureau",
            "fields_received": len(credit),
            "full_report_included": True,
            "cost": "$0.50",
            "data_size": "156 KB"
        })
        print(f"      ⚠️  Received full credit report (156 KB) - cost $0.50")
        
        # ═══════════════════════════════════════════════════════════════════
        # Call 4: Property Service (DIRECT)
        # ═══════════════════════════════════════════════════════════════════
        print("   📞 Call 4: GET Property Valuation (DIRECT to backend)")
        property_data = await BackendServices.property_service_get_valuation(
            property_id, self.caller_name
        )
        data_received.append({
            "source": "Property Service",
            "fields_received": len(property_data),
            "data_size": "12 KB"
        })
        print(f"      ℹ️  Received {len(property_data)} fields")
        
        # ═══════════════════════════════════════════════════════════════════
        # Call 5: Policy Service (DIRECT)
        # ═══════════════════════════════════════════════════════════════════
        print("   📞 Call 5: GET Lending Policy (DIRECT to backend)")
        policy = await BackendServices.policy_service_get_lending_rules(self.caller_name)
        data_received.append({
            "source": "Policy Service", 
            "fields_received": len(policy),
            "data_size": "3 KB"
        })
        print(f"      ℹ️  Received {len(policy)} fields")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        # ═══════════════════════════════════════════════════════════════════
        # Agent must now STITCH data together (client-side)
        # ═══════════════════════════════════════════════════════════════════
        print("\n   ⚙️  Agent stitching data client-side...")
        print("      ❌ No governance applied")
        print("      ❌ No data filtering")
        print("      ❌ No audit trail")
        print("      ❌ Agent saw SSN, account numbers, full credit report")
        
        # Calculate metrics (agent does this with RAW data)
        dti_ratio = (requested_amount / 360) / (customer["annual_income"] / 12)
        ltv_ratio = requested_amount / property_data["estimated_value"]
        
        decision = "APPROVED" if (
            credit["score"] >= policy["min_credit_score"] and
            dti_ratio <= policy["max_dti_ratio"] and
            account["account_age_months"] >= policy["min_account_age_months"] and
            ltv_ratio <= policy["max_loan_to_value"]
        ) else "DENIED"
        
        total_data_kb = sum(float(d["data_size"].replace(" KB", "")) for d in data_received)
        
        return {
            "approach": "TRADITIONAL API",
            "decision": decision,
            "metrics": {
                "backend_calls": 5,
                "total_data_received": f"{total_data_kb:.1f} KB",
                "elapsed_seconds": elapsed,
            },
            "data_exposure": {
                "ssn_exposed": True,
                "account_numbers_exposed": True,
                "full_credit_report_exposed": True,
                "transactions_loaded": 1000,
                "internal_notes_exposed": True,
            },
            "governance": {
                "identity_verified": False,
                "policy_enforced_by": "agent (client-side)",
                "audit_trail": None,
                "provenance": None,
                "data_filtered": False,
            }
        }


# ============================================================================
# APPROACH 2: MCP CONTEXT MESH - Proxy calls backends ON BEHALF of agent
# ============================================================================

print("\n" + "=" * 90)
print("APPROACH 2: MCP CONTEXT MESH")  
print("=" * 90)
print("""
In this approach:
• Agent makes 1 INTENT REQUEST to MCP Proxy
• MCP Proxy calls the SAME 5 backend services internally
• MCP applies governance BEFORE returning data to agent
• Agent receives FILTERED, GOVERNED context envelope
• Full audit trail captured centrally
• Connection pooling, caching, optimization at proxy level

         ┌─────────┐
         │  Agent  │
         └────┬────┘
              │
              │ ONE intent request:
              │ "I need context for loan_assessment"
              │
              ▼
    ┌─────────────────────────────────────────────────────────────────────┐
    │                        MCP PROXY SERVER                              │
    │  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐                 │
    │  │   Identity   │ │    Policy    │ │   Context    │                 │
    │  │   Service    │ │    Engine    │ │    Router    │                 │
    │  └──────────────┘ └──────────────┘ └──────────────┘                 │
    │         │                │                │                          │
    │         ▼                ▼                ▼                          │
    │  ┌─────────────────────────────────────────────────────────────┐    │
    │  │              INTERNAL CALLS (same backends)                  │    │
    │  │   But now with: pooling, caching, filtering, governance      │    │
    │  └─────────────────────────────────────────────────────────────┘    │
    │              │         │         │         │         │              │
    │              ▼         ▼         ▼         ▼         ▼              │
    │         ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐ ┌───────┐         │
    │         │Customer│ │Account│ │Credit │ │Property│ │Policy │         │
    │         │Service│ │Service│ │Bureau │ │Service│ │Service│         │
    │         └───────┘ └───────┘ └───────┘ └───────┘ └───────┘         │
    │              │         │         │         │         │              │
    │              ▼         ▼         ▼         ▼         ▼              │
    │           FULL      FULL      FULL      FULL      FULL             │
    │           DATA      DATA      DATA      DATA      DATA             │
    │              │         │         │         │         │              │
    │              └─────────┴─────────┴─────────┴─────────┘              │
    │                                  │                                   │
    │                                  ▼                                   │
    │  ┌─────────────────────────────────────────────────────────────┐    │
    │  │              FILTER & TRANSFORM LAYER                        │    │
    │  │   • Remove sensitive fields (SSN, account numbers)           │    │
    │  │   • Extract only needed data (no 1000 transactions)          │    │
    │  │   • Apply policy constraints                                 │    │
    │  │   • Add provenance metadata                                  │    │
    │  │   • Create audit record                                      │    │
    │  └─────────────────────────────────────────────────────────────┘    │
    │                                  │                                   │
    │                                  ▼                                   │
    │                    GOVERNED CONTEXT ENVELOPE                         │
    │                    (filtered, minimal, audited)                      │
    └──────────────────────────────────┬──────────────────────────────────┘
                                       │
                                       ▼
                              Agent receives ONLY:
                              • Fields needed for loan decision
                              • No SSN, no account numbers
                              • No 1000 transactions
                              • With provenance & constraints

KEY INSIGHT:
============
The backend calls STILL HAPPEN (inside the proxy).
The difference is:
1. Agent doesn't see raw data - only governed envelope
2. Proxy applies consistent policy - not each agent
3. Proxy can cache/pool connections - agents can't
4. Audit trail is centralized - not distributed
5. Sensitive data never leaves the proxy perimeter
""")


@dataclass
class ContextProvenance:
    """Tracks where context came from"""
    request_id: str
    timestamp: str
    sources: List[Dict]
    identity: Dict
    policy_decision: str
    data_filtered: bool
    original_size_kb: float
    filtered_size_kb: float

@dataclass 
class ContextConstraints:
    """Constraints that travel with context"""
    ttl_seconds: int
    permitted_actions: List[str]
    redacted_fields: List[str]
    data_classification: str

@dataclass
class GovernedContextEnvelope:
    """What the agent actually receives"""
    payload: Dict[str, Any]
    provenance: ContextProvenance
    constraints: ContextConstraints


class MCPProxyServer:
    """
    MCP Proxy Server - The Context Control Plane
    
    This is the key architectural component. It:
    1. Receives intent requests from agents
    2. Validates identity and evaluates policy
    3. Calls backend services INTERNALLY (same services!)
    4. Filters and transforms data based on policy
    5. Returns governed context envelope to agent
    6. Maintains audit trail
    """
    
    def __init__(self):
        self.connection_pool = {}  # Reusable connections to backends
        self.cache = {}            # Response caching
        self.audit_log = []        # Centralized audit trail
    
    async def request_context(
        self,
        intent: str,
        parameters: Dict,
        agent_token: str
    ) -> GovernedContextEnvelope:
        
        request_id = str(uuid.uuid4())[:8]
        print(f"\n   🛡️  MCP Proxy: Received context request [{request_id}]")
        print(f"      Intent: {intent}")
        print(f"      Agent: {agent_token}")
        
        start_time = datetime.now()
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 1: IDENTITY VALIDATION (happens BEFORE any backend calls)
        # ═══════════════════════════════════════════════════════════════════
        print("\n      ┌─ STEP 1: IDENTITY VALIDATION ─────────────────────────────")
        print("      │  🪪 Validating agent JWT token...")
        print("      │  🪪 Extracting claims and delegations...")
        print("      │  🪪 Verifying agent is authorized for 'loan_assessment'")
        
        identity = {
            "agent_id": agent_token,
            "principal": "loan-processing-system",
            "delegations": ["credit-decisions"],
            "purpose": intent,
            "validated_at": datetime.now().isoformat()
        }
        print(f"      │  ✅ Identity verified: {identity['agent_id']}")
        print("      └───────────────────────────────────────────────────────────")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 2: POLICY EVALUATION (determines what data agent can receive)
        # ═══════════════════════════════════════════════════════════════════
        print("\n      ┌─ STEP 2: POLICY EVALUATION ───────────────────────────────")
        print("      │  📜 Loading policy for intent: loan_assessment")
        print("      │  📜 Evaluating agent permissions...")
        print("      │  📜 Determining allowed fields per data source...")
        
        # Policy defines EXACTLY what the agent is allowed to see
        allowed_fields = {
            "customer": ["name", "employment_status", "annual_income"],
            "account": ["balance", "avg_monthly_balance", "overdraft_count", "account_age_months"],
            "credit": ["score", "rating"],
            "property": ["estimated_value", "property_type"],
            "policy": ["min_credit_score", "max_dti_ratio", "min_account_age_months", "max_loan_to_value"]
        }
        
        redacted_fields = [
            "ssn", "internal_notes", "internal_credit_flag",      # Customer
            "account_number", "routing_number", "transactions",   # Account
            "full_credit_report", "dispute_history",              # Credit
        ]
        
        print(f"      │  📜 Allowed fields: {sum(len(v) for v in allowed_fields.values())} total")
        print(f"      │  📜 Redacted fields: {len(redacted_fields)} sensitive fields will be removed")
        print("      │  ✅ Policy decision: ALLOW with filtering")
        print("      └───────────────────────────────────────────────────────────")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 3: BACKEND CALLS (same services, but INTERNAL to proxy)
        # ═══════════════════════════════════════════════════════════════════
        print("\n      ┌─ STEP 3: BACKEND DATA RETRIEVAL ──────────────────────────")
        print("      │  🔀 Context Router: Orchestrating parallel backend calls")
        print("      │  📡 Using connection pool (not creating new connections)")
        print("      │")
        
        caller_name = f"MCPProxy:{request_id}"
        
        # These are the SAME backend calls, but made by the proxy, not the agent
        print("      │  📞 [INTERNAL] GET Customer Profile")
        customer_raw = await BackendServices.customer_service_get_profile(
            parameters["applicant_id"], caller_name
        )
        print(f"      │     → Received {len(customer_raw)} fields from backend")
        
        print("      │  📞 [INTERNAL] GET Account History")
        account_raw = await BackendServices.account_service_get_history(
            parameters["applicant_id"], caller_name
        )
        print(f"      │     → Received {len(account_raw)} fields + {len(account_raw['transactions'])} transactions")
        
        print("      │  📞 [INTERNAL] GET Credit Score")
        credit_raw = await BackendServices.credit_bureau_get_score(
            parameters["applicant_id"], caller_name
        )
        print(f"      │     → Received {len(credit_raw)} fields + full report")
        
        print("      │  📞 [INTERNAL] GET Property Valuation")
        property_raw = await BackendServices.property_service_get_valuation(
            parameters["property_id"], caller_name
        )
        print(f"      │     → Received {len(property_raw)} fields")
        
        print("      │  📞 [INTERNAL] GET Lending Policy")
        policy_raw = await BackendServices.policy_service_get_lending_rules(caller_name)
        print(f"      │     → Received {len(policy_raw)} fields")
        
        print("      │")
        print("      │  ✅ All backend calls complete (5 internal calls)")
        print("      └───────────────────────────────────────────────────────────")
        
        original_size_kb = 2.1 + 847 + 156 + 12 + 3  # Total raw data
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 4: FILTER & TRANSFORM (this is where MCP adds value)
        # ═══════════════════════════════════════════════════════════════════
        print("\n      ┌─ STEP 4: FILTER & TRANSFORM ──────────────────────────────")
        print("      │  ✂️  Filtering data based on policy...")
        print("      │")
        print("      │  Customer: Keeping 3 fields, removing 9 (incl. SSN)")
        print("      │  Account:  Keeping 4 fields, removing 1000 transactions!")
        print("      │  Credit:   Keeping 2 fields, removing full report")
        print("      │  Property: Keeping 2 fields")
        print("      │  Policy:   Keeping 4 fields")
        
        # Apply filtering - agent will ONLY see these fields
        filtered_payload = {
            "customer": {
                "name": customer_raw["name"],
                "employment_status": customer_raw["employment_status"],
                "annual_income": customer_raw["annual_income"],
                # SSN: REMOVED
                # internal_notes: REMOVED
                # internal_credit_flag: REMOVED
            },
            "account": {
                "balance": account_raw["balance"],
                "avg_monthly_balance": account_raw["avg_monthly_balance"],
                "overdraft_count": account_raw["overdraft_count"],
                "account_age_months": account_raw["account_age_months"],
                # account_number: REMOVED
                # routing_number: REMOVED  
                # transactions (1000 items): REMOVED - only summary kept
            },
            "credit": {
                "score": credit_raw["score"],
                "rating": credit_raw["rating"],
                # full_credit_report: REMOVED
                # dispute_history: REMOVED
            },
            "property": {
                "estimated_value": property_raw["estimated_value"],
                "property_type": property_raw["property_type"],
            },
            "policy": {
                "min_credit_score": policy_raw["min_credit_score"],
                "max_dti_ratio": policy_raw["max_dti_ratio"],
                "min_account_age_months": policy_raw["min_account_age_months"],
                "max_loan_to_value": policy_raw["max_loan_to_value"],
            }
        }
        
        # Calculate filtered size (much smaller!)
        filtered_size_kb = 0.8  # Just the fields we kept
        
        print("      │")
        print(f"      │  📊 Data reduction: {original_size_kb:.1f} KB → {filtered_size_kb:.1f} KB")
        print(f"      │  📊 Reduction ratio: {(1 - filtered_size_kb/original_size_kb)*100:.1f}% smaller")
        print("      │  ✅ Sensitive data removed before returning to agent")
        print("      └───────────────────────────────────────────────────────────")
        
        # ═══════════════════════════════════════════════════════════════════
        # STEP 5: BUILD GOVERNED ENVELOPE (with provenance)
        # ═══════════════════════════════════════════════════════════════════
        print("\n      ┌─ STEP 5: BUILD GOVERNED ENVELOPE ─────────────────────────")
        print("      │  📦 Creating context envelope with:")
        print("      │     • Filtered payload")
        print("      │     • Provenance (source tracking)")
        print("      │     • Constraints (TTL, permissions)")
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        provenance = ContextProvenance(
            request_id=request_id,
            timestamp=datetime.now().isoformat(),
            sources=[
                {"service": "customer-service", "freshness": "real-time", "filtered": True},
                {"service": "account-service", "freshness": "real-time", "filtered": True},
                {"service": "credit-bureau", "freshness": "24h", "filtered": True},
                {"service": "property-service", "freshness": "30d", "filtered": True},
                {"service": "policy-service", "freshness": "real-time", "filtered": True},
            ],
            identity=identity,
            policy_decision="ALLOW with filtering",
            data_filtered=True,
            original_size_kb=original_size_kb,
            filtered_size_kb=filtered_size_kb
        )
        
        constraints = ContextConstraints(
            ttl_seconds=300,
            permitted_actions=["assess", "recommend"],
            redacted_fields=redacted_fields,
            data_classification="confidential"
        )
        
        # Audit logging (centralized!)
        self.audit_log.append({
            "request_id": request_id,
            "timestamp": provenance.timestamp,
            "agent": agent_token,
            "intent": intent,
            "sources_accessed": [s["service"] for s in provenance.sources],
            "policy_decision": "ALLOW",
            "data_filtered": True,
            "redacted_fields": redacted_fields,
        })
        
        print("      │  ✅ Audit record created")
        print(f"      │  ✅ Request ID: {request_id}")
        print("      └───────────────────────────────────────────────────────────")
        
        return GovernedContextEnvelope(
            payload=filtered_payload,
            provenance=provenance,
            constraints=constraints
        )


class MCPLoanAgent:
    """
    MCP-based Agent: Declares intent, receives governed context.
    Does NOT call backend services directly.
    """
    
    def __init__(self, agent_id: str, mcp_proxy: MCPProxyServer):
        self.agent_id = agent_id
        self.mcp = mcp_proxy
    
    async def assess_loan(self, applicant_id: str, property_id: str,
                          requested_amount: float) -> Dict[str, Any]:
        
        print(f"\n🤖 MCP Agent [{self.agent_id}]: Starting loan assessment")
        print(f"   Agent declares INTENT, does NOT call backends directly\n")
        
        start_time = datetime.now()
        
        # ═══════════════════════════════════════════════════════════════════
        # SINGLE CONTEXT REQUEST (not 5 API calls!)
        # ═══════════════════════════════════════════════════════════════════
        context = await self.mcp.request_context(
            intent="loan_assessment",
            parameters={
                "applicant_id": applicant_id,
                "property_id": property_id,
                "requested_amount": requested_amount,
            },
            agent_token=self.agent_id
        )
        
        elapsed = (datetime.now() - start_time).total_seconds()
        
        print(f"\n   ✅ Governed context envelope received")
        print(f"   ✅ Request ID: {context.provenance.request_id}")
        print(f"   ✅ Data filtered: {context.provenance.original_size_kb:.1f} KB → {context.provenance.filtered_size_kb:.1f} KB")
        print(f"   ✅ Redacted fields: {context.constraints.redacted_fields[:3]}... ({len(context.constraints.redacted_fields)} total)")
        print(f"   ✅ TTL: {context.constraints.ttl_seconds} seconds")
        
        # Agent reasons on GOVERNED context (no sensitive data!)
        payload = context.payload
        
        dti_ratio = (requested_amount / 360) / (payload["customer"]["annual_income"] / 12)
        ltv_ratio = requested_amount / payload["property"]["estimated_value"]
        
        policy = payload["policy"]
        decision = "APPROVED" if (
            payload["credit"]["score"] >= policy["min_credit_score"] and
            dti_ratio <= policy["max_dti_ratio"] and
            payload["account"]["account_age_months"] >= policy["min_account_age_months"] and
            ltv_ratio <= policy["max_loan_to_value"]
        ) else "DENIED"
        
        return {
            "approach": "MCP CONTEXT MESH",
            "decision": decision,
            "metrics": {
                "agent_requests": 1,
                "internal_backend_calls": 5,  # Still 5, but inside proxy
                "data_received_by_agent": f"{context.provenance.filtered_size_kb:.1f} KB",
                "data_filtered_out": f"{context.provenance.original_size_kb - context.provenance.filtered_size_kb:.1f} KB",
                "elapsed_seconds": elapsed,
            },
            "data_exposure": {
                "ssn_exposed": False,
                "account_numbers_exposed": False,
                "full_credit_report_exposed": False,
                "transactions_loaded": 0,  # Only summary!
                "internal_notes_exposed": False,
            },
            "governance": {
                "identity_verified": True,
                "policy_enforced_by": "MCP Proxy (server-side)",
                "audit_trail": context.provenance.request_id,
                "provenance": {
                    "sources": [s["service"] for s in context.provenance.sources],
                },
                "data_filtered": True,
                "redacted_fields": context.constraints.redacted_fields,
            }
        }


# ============================================================================
# RUN THE COMPARISON
# ============================================================================

async def run_comparison():
    """Execute both approaches and show the differences"""
    
    # Reset backend call log
    BackendServices.reset_log()
    
    print("\n" + "=" * 90)
    print("RUNNING COMPARISON")
    print("=" * 90)
    
    applicant_id = "CUST-12345"
    property_id = "PROP-789"
    requested_amount = 280000.00
    
    print(f"\nLoan Application Details:")
    print(f"  Applicant: {applicant_id}")
    print(f"  Property: {property_id}")
    print(f"  Amount: ${requested_amount:,.2f}")
    
    # ═══════════════════════════════════════════════════════════════════════
    # RUN TRADITIONAL APPROACH
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 90)
    print("EXECUTING: TRADITIONAL API APPROACH")
    print("─" * 90)
    
    BackendServices.reset_log()
    traditional_agent = TraditionalLoanAgent("agent-001")
    traditional_result = await traditional_agent.assess_loan(
        applicant_id, property_id, requested_amount
    )
    traditional_calls = BackendServices.call_log.copy()
    
    # ═══════════════════════════════════════════════════════════════════════
    # RUN MCP APPROACH
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "─" * 90)
    print("EXECUTING: MCP CONTEXT MESH APPROACH")
    print("─" * 90)
    
    BackendServices.reset_log()
    mcp_proxy = MCPProxyServer()
    mcp_agent = MCPLoanAgent("loan-agent-001", mcp_proxy)
    mcp_result = await mcp_agent.assess_loan(
        applicant_id, property_id, requested_amount
    )
    mcp_calls = BackendServices.call_log.copy()
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPARE BACKEND CALLS
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("BACKEND CALL ANALYSIS")
    print("=" * 90)
    
    print("\n┌─────────────────────────────────────────────────────────────────────────────────────┐")
    print("│                           WHO CALLED THE BACKENDS?                                   │")
    print("├─────────────────────────────────────────────────────────────────────────────────────┤")
    print("│                                                                                      │")
    print("│  TRADITIONAL APPROACH:                                                               │")
    for call in traditional_calls:
        print(f"│    • {call['service']:25} called by: {call['caller']:30} │")
    print("│                                                                                      │")
    print("│  MCP APPROACH:                                                                       │")
    for call in mcp_calls:
        print(f"│    • {call['service']:25} called by: {call['caller']:30} │")
    print("│                                                                                      │")
    print("│  ✅ SAME 5 backend calls in both cases!                                              │")
    print("│  ✅ The difference is WHERE and HOW they're orchestrated.                            │")
    print("│                                                                                      │")
    print("└─────────────────────────────────────────────────────────────────────────────────────┘")
    
    # ═══════════════════════════════════════════════════════════════════════
    # COMPARISON TABLE
    # ═══════════════════════════════════════════════════════════════════════
    print("\n" + "=" * 90)
    print("COMPARISON RESULTS")
    print("=" * 90)
    
    print("""
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                              SIDE-BY-SIDE COMPARISON                                      │
├───────────────────────────────────┬─────────────────────────┬────────────────────────────┤
│ METRIC                            │ TRADITIONAL API         │ MCP CONTEXT MESH           │
├───────────────────────────────────┼─────────────────────────┼────────────────────────────┤
│ Backend services called           │           5             │           5                │
│ WHO makes the calls?              │ Agent (directly)        │ MCP Proxy (internally)     │
│ Calls visible to agent?           │ Yes (all 5)             │ No (hidden in proxy)       │
├───────────────────────────────────┼─────────────────────────┼────────────────────────────┤
│ Data agent receives               │ 1,020 KB (raw)          │ 0.8 KB (filtered)          │
│ Data reduction                    │ 0%                      │ 99.9%                      │
├───────────────────────────────────┼─────────────────────────┼────────────────────────────┤
│ SSN exposed to agent?             │ ❌ YES                   │ ✅ NO                       │
│ Account numbers exposed?          │ ❌ YES                   │ ✅ NO                       │
│ 1000 transactions loaded?         │ ❌ YES                   │ ✅ NO (summary only)        │
│ Full credit report exposed?       │ ❌ YES                   │ ✅ NO                       │
├───────────────────────────────────┼─────────────────────────┼────────────────────────────┤
│ Identity verified?                │ ❌ NO                    │ ✅ YES                      │
│ Policy enforced where?            │ Client-side (agent)     │ Server-side (proxy)        │
│ Audit trail?                      │ ❌ NONE                  │ ✅ Centralized              │
│ Provenance tracked?               │ ❌ NO                    │ ✅ YES (5 sources)          │
├───────────────────────────────────┼─────────────────────────┼────────────────────────────┤
│ Connection management             │ Each agent              │ Pooled at proxy            │
│ Caching possible?                 │ Per-agent only          │ Shared across agents       │
│ Rate limiting                     │ Per-agent               │ Centralized                │
└───────────────────────────────────┴─────────────────────────┴────────────────────────────┘
    """)
    
    print("\n" + "=" * 90)
    print("KEY INSIGHT")
    print("=" * 90)
    print("""
┌──────────────────────────────────────────────────────────────────────────────────────────┐
│                                                                                          │
│   THE BACKEND CALLS ARE THE SAME.                                                        │
│   The difference is ARCHITECTURAL:                                                       │
│                                                                                          │
│   1. ORCHESTRATION LOCATION                                                              │
│      Traditional: Agent orchestrates (distributed, inconsistent)                         │
│      MCP: Proxy orchestrates (centralized, consistent)                                   │
│                                                                                          │
│   2. DATA EXPOSURE                                                                       │
│      Traditional: Agent sees ALL raw data (1,020 KB)                                     │
│      MCP: Agent sees FILTERED data (0.8 KB)                                              │
│                                                                                          │
│   3. GOVERNANCE ENFORCEMENT                                                              │
│      Traditional: Each agent applies policy (if at all)                                  │
│      MCP: Proxy enforces policy consistently for ALL agents                              │
│                                                                                          │
│   4. SECURITY PERIMETER                                                                  │
│      Traditional: Sensitive data flows to every agent                                    │
│      MCP: Sensitive data stays within proxy perimeter                                    │
│                                                                                          │
│   5. OBSERVABILITY                                                                       │
│      Traditional: No central audit, compliance nightmare                                 │
│      MCP: Centralized audit log, full provenance                                         │
│                                                                                          │
│   ════════════════════════════════════════════════════════════════════════════════════   │
│                                                                                          │
│   "MCP doesn't eliminate backend calls.                                                  │
│    MCP changes WHO makes them, WHAT data flows to agents,                                │
│    and HOW governance is enforced."                                                      │
│                                                                                          │
└──────────────────────────────────────────────────────────────────────────────────────────┘
    """)


if __name__ == "__main__":
    asyncio.run(run_comparison())