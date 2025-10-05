from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import json
import requests
from app.models.leave import LeaveType, LeaveStatus
from app.config import settings

class UnifiedAIService:
    """Unified AI Service for all leave management conversations"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def parse_conversation(
        self,
        text: str,
        chat_history: List[Dict],
        user_context: Dict
    ) -> Dict:
        """
        Parse any leave management conversation and determine intent.
        Works for all user roles (Employee, Manager, HR)
        """
        
        today = datetime.now().date()
        
        system_prompt = f"""You are an intelligent assistant for leave management system.

USER CONTEXT (CRITICAL FOR INTENT DETECTION):
- Role: {user_context['role']}
- Department: {user_context['department']}
- Position: {user_context['position']}
- Is Manager: {user_context['is_manager']}
- Is HR: {user_context['is_hr']}
- User Name: {user_context['full_name']}

Today's date: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})

ROLE-BASED INTENT RULES:

For EMPLOYEES (non-managers):
- Cannot approve/reject leaves
- "pending requests" means THEIR OWN pending leaves
- "need approval" means THEIR OWN leaves awaiting manager approval
- Cannot view team status or analytics
- Can query policies (QUERY_POLICY)

For MANAGERS/HR:
- Can approve/reject leaves
- "pending requests" means LEAVES AWAITING THEIR APPROVAL
- Can view team status and department data
- Can query policies (QUERY_POLICY)

Determine the INTENT and extract relevant information:

INTENTS:
1. REQUEST_LEAVE - User wants to request leave
2. APPROVE_REJECT - Approve or reject someone's leave (MANAGERS/HR ONLY)
3. QUERY_LEAVES - Query leave records
4. CHECK_BALANCE - Check leave balances
5. TEAM_STATUS - Check team availability (MANAGERS/HR ONLY)
6. ANALYTICS - View analytics (HR ONLY)
7. QUERY_POLICY - Ask about company policies (ALL USERS)
8. GENERAL - General question or greeting

NEW INTENT - QUERY_POLICY:
- "what is the leave policy"
- "summarize leave policy"
- "tell me about sick leave policy"
- "what are the rules for annual leave"
- "how many days notice do I need"
- "can I take leave in December"
- "what's the policy on maternity leave"
- Any question about policies, rules, guidelines, requirements

FOR QUERY_POLICY, extract:
- policy_query: the actual question about the policy
- policy_type: LEAVE, SICK, ANNUAL, CASUAL, MATERNITY, PATERNITY, GENERAL

SPECIAL ROLE-BASED CASES:

For {user_context['full_name']} (Role: {user_context['role']}):

IF USER IS EMPLOYEE (non-manager):
- "pending requests I should approve" → QUERY_LEAVES with status: PENDING, employee_name: "{user_context['full_name']}"
- "need my approval" → QUERY_LEAVES with status: PENDING, employee_name: "{user_context['full_name']}"
- "awaiting approval" → QUERY_LEAVES with status: PENDING, employee_name: "{user_context['full_name']}"
- "what needs approval" → QUERY_LEAVES with status: PENDING, employee_name: "{user_context['full_name']}"

IF USER IS MANAGER/HR:
- "pending requests I should approve" → APPROVE_REJECT with action: CHECK_PENDING
- "need my approval" → APPROVE_REJECT with action: CHECK_PENDING
- "awaiting approval" → APPROVE_REJECT with action: CHECK_PENDING

FOR REQUEST_LEAVE, extract:
- leave_type: SICK, CASUAL, ANNUAL, MATERNITY, PATERNITY, UNPAID
- start_date: YYYY-MM-DD
- end_date: YYYY-MM-DD
- reason: brief description
- is_complete: true if all required fields present
- needs_clarification: true if missing info
- clarification_question: what to ask next

FOR APPROVE_REJECT, extract:
- action: APPROVE, REJECT, or CHECK_PENDING
- leave_id: if mentioned
- employee_name: if no leave_id
- comments: approval/rejection comments
- status: PENDING (when checking approvals)

CRITICAL PARSING RULES:
1. NEVER assume leave_type - it must be explicitly stated by user
2. NEVER mark is_complete=true if leave_type is missing
3. ALWAYS set needs_clarification=true if ANY required field is missing
4. Required fields for REQUEST_LEAVE: leave_type, start_date, end_date

LEAVE TYPE DETECTION (must be explicitly mentioned):
- "sick leave" / "sick" → SICK
- "casual leave" / "casual" → CASUAL  
- "annual leave" / "vacation" / "annual" → ANNUAL
- "maternity" → MATERNITY
- "paternity" → PATERNITY
- If NONE of these words appear → leave_type: null

If leave_type is null:
{{
    "is_complete": false,
    "needs_clarification": true,
    "clarification_question": "What type of leave do you need? (Sick, Casual, Annual, etc.)"
}}

NEVER default to CASUAL or any other type if not explicitly mentioned.

FOR QUERY_LEAVES, extract:
- date_filter: {{"type": "TODAY", "THIS_WEEK", "THIS_MONTH", "DATE_RANGE", "SPECIFIC_DATE"}} or null
- department: Frontend, Backend, HR, Design
- employee_name: specific employee
- status: PENDING, APPROVED, REJECTED
- leave_type: specific type

DATE PARSING RULES:
- "tomorrow" = {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
- "next Monday" = calculate next Monday's date
- "3 days" = 3 days starting tomorrow unless specified
- "this week" = THIS_WEEK filter
- "today" = TODAY filter

SUGGESTED ACTIONS:
- For employees: ["Check my leaves", "Request leave", "View balance"]
- For managers: ["View pending approvals", "Check team status", "Approve leaves"]
- For HR: ["View analytics", "Department report", "Process leaves"]

Respond ONLY with valid JSON:
{{
    "intent": "QUERY_POLICY",
    "policy_query": "what is the leave policy",
    "policy_type": "LEAVE",
    "leave_type": null,
    "start_date": null,
    "end_date": null,
    "reason": null,
    "is_complete": false,
    "needs_clarification": false,
    "action": null,
    "leave_id": null,
    "employee_name": null,
    "date_filter": null,
    "department": null,
    "status": null,
    "suggested_actions": ["Request leave", "Check balance", "View my leaves"]
}}"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add chat history (last 5 messages)
        for msg in chat_history[-5:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")
            })
        
        messages.append({"role": "user", "content": text})
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": messages,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # FIX: Handle cases where API returns string instead of JSON
                content = result["choices"][0]["message"]["content"]
                
                # Try to parse as JSON, fallback if it's a string or invalid JSON
                try:
                    if isinstance(content, str):
                        parsed = json.loads(content)
                    else:
                        parsed = content
                        
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"JSON parsing failed, using fallback parser: {e}")
                    print(f"Raw content: {content}")
                    return self._fallback_parse(text, user_context)
                
                # Ensure parsed is a dictionary
                if not isinstance(parsed, dict):
                    print(f"Parsed content is not a dictionary: {type(parsed)}")
                    return self._fallback_parse(text, user_context)
                
                # Convert date strings to date objects with error handling
                if parsed.get("start_date"):
                    try:
                        if isinstance(parsed["start_date"], str):
                            parsed["start_date"] = datetime.strptime(
                                parsed["start_date"], "%Y-%m-%d"
                            ).date()
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing start_date: {e}")
                        parsed["start_date"] = None
                
                if parsed.get("end_date"):
                    try:
                        if isinstance(parsed["end_date"], str):
                            parsed["end_date"] = datetime.strptime(
                                parsed["end_date"], "%Y-%m-%d"
                            ).date()
                    except (ValueError, TypeError) as e:
                        print(f"Error parsing end_date: {e}")
                        parsed["end_date"] = None
                
                # Handle date_filter dates with error handling
                if parsed.get("date_filter") and isinstance(parsed["date_filter"], dict):
                    date_filter = parsed["date_filter"]
                    
                    if date_filter.get("start_date") and isinstance(date_filter["start_date"], str):
                        try:
                            date_filter["start_date"] = datetime.strptime(
                                date_filter["start_date"], "%Y-%m-%d"
                            ).date()
                        except (ValueError, TypeError) as e:
                            print(f"Error parsing date_filter start_date: {e}")
                            date_filter["start_date"] = None
                    
                    if date_filter.get("end_date") and isinstance(date_filter["end_date"], str):
                        try:
                            date_filter["end_date"] = datetime.strptime(
                                date_filter["end_date"], "%Y-%m-%d"
                            ).date()
                        except (ValueError, TypeError) as e:
                            print(f"Error parsing date_filter end_date: {e}")
                            date_filter["end_date"] = None
                
                # Convert leave_type string to enum with error handling
                if parsed.get("leave_type"):
                    try:
                        if isinstance(parsed["leave_type"], str):
                            parsed["leave_type"] = LeaveType[parsed["leave_type"].upper()]
                    except (KeyError, AttributeError) as e:
                        print(f"Error converting leave_type: {e}")
                        parsed["leave_type"] = None
                
                # Auto-populate employee_name for employees querying their own data
                current_intent = parsed.get("intent")
                if current_intent in ["QUERY_LEAVES", "CHECK_BALANCE"] and not parsed.get("employee_name"):
                    if not user_context["is_manager"] or parsed.get("status") == "PENDING":
                        parsed["employee_name"] = user_context["full_name"]
                
                # Validate completeness for leave requests
                if current_intent == "REQUEST_LEAVE":
                    parsed = self._check_leave_completeness(parsed)
                
                # Add role-appropriate suggested actions
                if not parsed.get("suggested_actions"):
                    parsed["suggested_actions"] = self._get_role_suggested_actions(
                        user_context, 
                        current_intent or "GENERAL"
                    )
                
                # Ensure intent is always set and valid
                if not parsed.get("intent"):
                    parsed["intent"] = "GENERAL"
                
                # Validate intent is one of the expected values
                valid_intents = ["REQUEST_LEAVE", "APPROVE_REJECT", "QUERY_LEAVES", 
                               "CHECK_BALANCE", "TEAM_STATUS", "ANALYTICS", "QUERY_POLICY", "GENERAL"]
                if parsed["intent"] not in valid_intents:
                    print(f"Invalid intent detected: {parsed['intent']}, defaulting to GENERAL")
                    parsed["intent"] = "GENERAL"
                    
                return parsed
            
            else:
                print(f"Groq API Error: {response.status_code} - {response.text}")
                return self._fallback_parse(text, user_context)
                
        except requests.exceptions.Timeout:
            print("Groq API timeout, using fallback parser")
            return self._fallback_parse(text, user_context)
            
        except requests.exceptions.RequestException as e:
            print(f"Groq API request failed: {e}")
            return self._fallback_parse(text, user_context)
            
        except KeyError as e:
            print(f"Key error in API response: {e}")
            return self._fallback_parse(text, user_context)
            
        except Exception as e:
            print(f"Unexpected error in parse_conversation: {e}")
            return self._fallback_parse(text, user_context)

    def _get_role_suggested_actions(self, user_context: Dict, intent: str) -> List[str]:
        """Get role-appropriate suggested actions"""
        
        if not user_context["is_manager"]:
            # Employee actions
            if intent == "QUERY_LEAVES":
                return ["Check my leaves", "View balance", "Request leave"]
            elif intent == "CHECK_BALANCE":
                return ["Request leave", "View my leaves"]
            elif intent == "REQUEST_LEAVE":
                return ["Check balance", "View my leaves"]
            elif intent == "QUERY_POLICY":
                return ["Request leave", "Check balance", "View my leaves"]
            else:
                return ["Check my leaves", "Request leave", "View balance"]
        
        elif user_context["is_hr"]:
            # HR actions
            if intent == "APPROVE_REJECT":
                return ["View all pending", "Process approvals", "Team status"]
            elif intent == "QUERY_LEAVES":
                return ["Department report", "View analytics", "Pending approvals"]
            elif intent == "QUERY_POLICY":
                return ["View analytics", "Pending approvals", "Team status"]
            else:
                return ["Pending approvals", "Team status", "View analytics"]
        
        else:
            # Manager actions
            if intent == "APPROVE_REJECT":
                return ["View pending approvals", "Team status", "Approve all"]
            elif intent == "QUERY_LEAVES":
                return ["Team leaves", "Pending approvals", "Balance report"]
            elif intent == "QUERY_POLICY":
                return ["Pending approvals", "Team status", "View my team"]
            else:
                return ["Pending approvals", "Team status", "View my team"]
    
    def _check_leave_completeness(self, parsed: Dict) -> Dict:
        """Check if leave request has all required fields"""
        missing = []
        
        # Check leave_type first
        if not parsed.get("leave_type"):
            missing.append("leave_type")
            parsed["clarification_question"] = "What type of leave do you need? (Sick, Casual, Annual, etc.)"
            parsed["needs_clarification"] = True
            parsed["is_complete"] = False
            parsed["missing_fields"] = missing
            return parsed  # Return early - don't check other fields yet
        
        # Only check dates if leave_type exists
        if not parsed.get("start_date"):
            missing.append("start_date")
            parsed["clarification_question"] = "When would you like to start your leave?"
            parsed["needs_clarification"] = True
            parsed["is_complete"] = False
        elif not parsed.get("end_date"):
            # Auto-set end_date to start_date for single day (this is fine)
            parsed["end_date"] = parsed["start_date"]
        
        parsed["missing_fields"] = missing
        
        # Only mark complete if ALL required fields present
        if parsed.get("leave_type") and parsed.get("start_date") and parsed.get("end_date"):
            parsed["is_complete"] = True
            parsed["needs_clarification"] = False
        else:
            parsed["is_complete"] = False
            parsed["needs_clarification"] = True
        
        return parsed
    
    def _fallback_parse(self, text: str, user_context: Dict) -> Dict:
        """Enhanced rule-based fallback parser with policy query support"""
        text_lower = text.lower().strip()
        
        # Default result structure
        result = {
            "intent": "GENERAL",
            "policy_query": None,
            "policy_type": None,
            "leave_type": None,
            "start_date": None,
            "end_date": None,
            "reason": None,
            "is_complete": False,
            "needs_clarification": False,
            "missing_fields": [],
            "status": None,
            "date_filter": None,
            "employee_name": user_context["full_name"] if not user_context["is_manager"] else None,
            "action": None,
            "suggested_actions": self._get_role_suggested_actions(user_context, "GENERAL")
        }
        
        # NEW: Check for policy queries
        policy_keywords = ["policy", "rule", "guideline", "requirement", "how many", 
                          "allowed", "notice period", "blackout", "documentation"]
        
        if any(keyword in text_lower for keyword in policy_keywords):
            # Check if it's specifically about policies, not leave requests
            if not any(word in text_lower for word in ["request", "apply for", "take leave", "book"]):
                result["intent"] = "QUERY_POLICY"
                result["policy_query"] = text
                
                # Detect policy type
                if "sick" in text_lower:
                    result["policy_type"] = "SICK"
                elif "annual" in text_lower or "vacation" in text_lower:
                    result["policy_type"] = "ANNUAL"
                elif "casual" in text_lower:
                    result["policy_type"] = "CASUAL"
                elif "maternity" in text_lower:
                    result["policy_type"] = "MATERNITY"
                elif "paternity" in text_lower:
                    result["policy_type"] = "PATERNITY"
                else:
                    result["policy_type"] = "LEAVE"
                
                result["suggested_actions"] = ["Request leave", "Check balance", "View my leaves"]
                return result
        
        # Intent: "Who is on leave today?"
        if any(phrase in text_lower for phrase in ["who is on leave", "who's on leave", "who is absent", "anyone on leave"]):
            result["intent"] = "QUERY_LEAVES"
            result["date_filter"] = {"type": "TODAY"}
            result["status"] = "APPROVED"  # Only show approved leaves
            
            if "today" in text_lower:
                result["date_filter"] = {"type": "TODAY"}
            elif "this week" in text_lower:
                result["date_filter"] = {"type": "THIS_WEEK"}
            elif "tomorrow" in text_lower:
                tomorrow = datetime.now().date() + timedelta(days=1)
                result["date_filter"] = {"type": "SPECIFIC_DATE", "date": tomorrow.isoformat()}
        
        # Intent: Pending approvals
        elif any(word in text_lower for word in ["pending", "approval", "approve", "need approval", "awaiting"]):
            if user_context["is_manager"]:
                result["intent"] = "APPROVE_REJECT"
                result["action"] = "CHECK_PENDING"
                result["suggested_actions"] = ["View pending approvals", "Approve leaves", "Check team status"]
            else:
                result["intent"] = "QUERY_LEAVES"
                result["status"] = "PENDING"
                result["employee_name"] = user_context["full_name"]
                result["suggested_actions"] = ["Check my leaves", "View balance", "Request leave"]
        
        # Intent: Leave requests
        elif any(word in text_lower for word in ["request leave", "apply for leave", "take leave", "need leave"]):
            result["intent"] = "REQUEST_LEAVE"
            result["needs_clarification"] = True
            result["suggested_actions"] = ["Check balance", "View my leaves"]
            
            # Try to extract leave type
            if "sick" in text_lower:
                result["leave_type"] = LeaveType.SICK
            elif "casual" in text_lower:
                result["leave_type"] = LeaveType.CASUAL
            elif "annual" in text_lower or "vacation" in text_lower:
                result["leave_type"] = LeaveType.ANNUAL
        
        # Intent: Balance check
        elif any(word in text_lower for word in ["balance", "available days", "leave days"]):
            result["intent"] = "CHECK_BALANCE"
            result["suggested_actions"] = ["Request leave", "View my leaves"]
        
        # Intent: Team status (managers only)
        elif any(word in text_lower for word in ["team status", "team availability", "my team"]) and user_context["is_manager"]:
            result["intent"] = "TEAM_STATUS"
            result["suggested_actions"] = ["Pending approvals", "View analytics", "Check balances"]
        
        # Intent: General leave queries
        elif any(word in text_lower for word in ["show leaves", "leave list", "leaves", "leave history"]):
            result["intent"] = "QUERY_LEAVES"
            result["suggested_actions"] = ["Check balance", "Request leave"]
            
            if "my" in text_lower and not user_context["is_manager"]:
                result["employee_name"] = user_context["full_name"]
        
        return result
    
    def generate_response(
        self,
        intent: str,
        parsed: Dict,
        data: Dict,
        user_context: Dict
    ) -> str:
        """Generate contextual response with policy compliance awareness"""
        
        # Check if policy compliance data exists
        policy_compliance = data.get("policy_compliance")
        has_violations = policy_compliance and not policy_compliance.get("compliant")
        has_warnings = policy_compliance and policy_compliance.get("warnings")
        
        system_prompt = f"""You are a helpful leave management assistant with policy enforcement capabilities.

User: {user_context['full_name']} ({user_context['role']} - {user_context['position']})

Generate natural, conversational responses.

INTENT: {intent}

POLICY COMPLIANCE STATUS:
- Has Violations: {has_violations}
- Has Warnings: {has_warnings}

TONE GUIDELINES:
- Friendly and professional
- Clear and actionable
- When policy violations exist: Be firm but empathetic, explain the policy clearly
- When warnings exist: Inform user but don't block the action
- For QUERY_POLICY: Summarize policy information clearly, cite specific rules
- Adapt to the situation:
  * REQUEST_LEAVE: Check policy compliance first, guide user to comply
  * APPROVE_REJECT: Enforce policy violations strictly
  * QUERY_POLICY: Explain policies clearly and concisely
  * Other intents: Standard helpful tone

Keep responses 2-3 sentences for simple queries, longer for complex data or policy explanations."""

        user_prompt = f"""
PARSED DATA:
{json.dumps(parsed, indent=2, default=str)}

RESULT DATA:
{json.dumps(data, indent=2, default=str)}

Generate a helpful response that:
1. Addresses the user's request
2. Clearly explains any policy violations or warnings
3. Guides user on next steps
4. Maintains professional but friendly tone"""

        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.groq_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    "temperature": 0.7,
                    "max_tokens": 300
                },
                timeout=8
            )
            
            if response.status_code == 200:
                result = response.json()
                ai_response = result["choices"][0]["message"]["content"]
                return ai_response.strip()
            else:
                print(f"Groq API response error: {response.status_code}")
                return self._generate_fallback_response_with_policy(
                    intent, parsed, data, user_context, policy_compliance
                )
                
        except Exception as e:
            print(f"Response generation failed: {e}")
            return self._generate_fallback_response_with_policy(
                intent, parsed, data, user_context, policy_compliance
            )

    def _generate_fallback_response_with_policy(
        self,
        intent: str,
        parsed: Dict,
        data: Dict,
        user_context: Dict,
        policy_compliance: Dict = None
    ) -> str:
        """Enhanced fallback with policy awareness"""
        
        # Check policy compliance
        if policy_compliance:
            violations = policy_compliance.get("violations", [])
            warnings = policy_compliance.get("warnings", [])
            
            if violations and intent in ["REQUEST_LEAVE", "APPROVE_REJECT"]:
                response = "Policy Violation Detected\n\n"
                response += "Your request cannot be processed due to the following policy violations:\n\n"
                for i, violation in enumerate(violations, 1):
                    response += f"{i}. {violation}\n"
                
                # Show relevant policies
                relevant = policy_compliance.get("relevant_policies", [])
                if relevant:
                    response += "\nRelevant Policy:\n"
                    response += f"- {relevant[0]['section_title']}\n"
                    response += f"  {relevant[0]['content'][:200]}...\n"
                
                response += "\nPlease revise your request to comply with company policy."
                return response
            
            if warnings:
                warning_text = "\n\nNote: " + "; ".join(warnings)
            else:
                warning_text = ""
        else:
            warning_text = ""
        
        # Use existing fallback logic
        base_response = self._generate_fallback_response(intent, parsed, data, user_context)
        
        return base_response + warning_text
    
    def _generate_fallback_response(
        self,
        intent: str,
        parsed: Dict,
        data: Dict,
        user_context: Dict
    ) -> str:
        """Generate structured fallback responses"""
        
        if intent == "REQUEST_LEAVE":
            if data.get("needs_clarification"):
                return parsed.get("clarification_question", "Please provide more details about your leave request.")
            
            if data.get("is_complete"):
                leave_data = data.get("leave_data", {})
                duration = (leave_data.get("end_date") - leave_data.get("start_date")).days + 1 if leave_data.get("end_date") and leave_data.get("start_date") else 1
                leave_type = leave_data.get("leave_type")
                
                response = f"Your {leave_type.value.lower() if leave_type else 'leave'} request for {duration} day(s) "
                response += f"from {leave_data.get('start_date')} to {leave_data.get('end_date')}.\n\n"
                
                # Add balance info
                balance = data.get("leave_balance")
                if balance:
                    response += f"Your balance: {balance['available']}/{balance['total']} days available.\n\n"
                
                # Add responsible person suggestions
                suggested = data.get("suggested_responsible_persons", [])
                if suggested:
                    response += "Suggested colleagues to handle your responsibilities:\n"
                    for i, person in enumerate(suggested[:3], 1):
                        response += f"{i}. {person['name']} ({person['position']}) - {person['reason']}\n"
                    response += "\nReply with a number to select, or 'submit' to proceed without assignment."
                else:
                    response += "Type 'submit' to finalize your leave request."
                
                # Add impact warning
                impact = data.get("team_impact", {})
                if impact.get("level") in ["MEDIUM", "HIGH"]:
                    response += f"\n\nNote: {', '.join(impact.get('factors', []))}"
                
                return response
            
            return "I'm here to help you request leave. What type of leave do you need?"
        
        elif intent == "APPROVE_REJECT":
            if data.get("success"):
                action = data.get("action", "processed")
                leave_info = data.get("leave", {})
                return f"Successfully {action} leave request for {leave_info.get('employee')} ({leave_info.get('dates')})."
            else:
                return data.get("message", "Unable to process the approval/rejection.")
        
        elif intent == "QUERY_LEAVES":
            count = data.get("count", 0)
            if count == 0:
                return "No leaves found matching your criteria."
            
            leaves = data.get("leaves", [])
            response = f"Found {count} leave record(s):\n\n"
            
            for leave in leaves[:5]:  # Show first 5
                response += f"- {leave['employee_name']} ({leave['department']}): "
                response += f"{leave['leave_type']} from {leave['start_date']} to {leave['end_date']} "
                response += f"[{leave['status']}]\n"
            
            if count > 5:
                response += f"\n... and {count - 5} more"
            
            return response
        
        elif intent == "CHECK_BALANCE":
            balances = data.get("balances", [])
            if not balances:
                return "No balance information found."
            
            if len(balances) == 1 and balances[0]["employee_name"] == user_context["full_name"]:
                # User checking their own balance
                response = "Your leave balance:\n\n"
                for bal in balances:
                    response += f"{bal['leave_type']}: {bal['available']}/{bal['total']} days available "
                    response += f"({bal['used']} used)\n"
            else:
                # Manager/HR checking team balances
                response = f"Leave balances for {data.get('count')} employee(s):\n\n"
                for bal in balances[:10]:
                    response += f"- {bal['employee_name']}: {bal['leave_type']} - "
                    response += f"{bal['available']}/{bal['total']} available\n"
            
            return response
        
        elif intent == "TEAM_STATUS":
            total = data.get("total", 0)
            on_leave = data.get("on_leave", 0)
            available = data.get("available", 0)
            
            response = f"Team Status: {available}/{total} available, {on_leave} on leave\n\n"
            
            team_status = data.get("team_status", [])
            on_leave_list = [t for t in team_status if t["status"] == "On Leave"]
            
            if on_leave_list:
                response += "Currently on leave:\n"
                for member in on_leave_list[:5]:
                    response += f"- {member['employee_name']} ({member['position']}) - {member.get('leave_type', 'N/A')}\n"
            else:
                response += "Everyone is available."
            
            return response
        
        elif intent == "ANALYTICS":
            response = "Analytics Overview:\n\n"
            
            monthly = data.get("monthly_distribution", [])
            if monthly:
                response += "Monthly distribution available. "
            
            dept_stats = data.get("department_stats", [])
            if dept_stats:
                response += f"Data for {len(dept_stats)} departments. "
            
            return response + "Check the detailed data below."
        
        elif intent == "QUERY_POLICY":
            policies = data.get("policies", [])
            
            if not policies:
                return data.get("message", "I couldn't find specific policy information. Please contact HR.")
            
            response = f"Here's what I found about your question:\n\n"
            
            for i, policy in enumerate(policies[:2], 1):  # Show top 2
                response += f"Policy: {policy['section_title']}\n"
                response += f"{policy['content'][:300]}...\n"
                response += f"(From: {policy['policy_name']} - {policy['relevance']} relevant)\n\n"
            
            if len(policies) > 2:
                response += f"... and {len(policies) - 2} more relevant sections found.\n\n"
            
            response += "Would you like to know more about any specific aspect?"
            return response
        
        else:
            return "How can I help you with leave management today? You can request leave, check balances, view team status, ask about policies, or ask me anything related to leaves."
    
    def calculate_impact_score(self, leave_data: Dict, team_data: List) -> Dict:
        """Calculate team impact score for a leave request"""
        score = 0
        factors = []
        
        # Check overlapping leaves
        overlapping = len([t for t in team_data if t.get("on_leave")])
        if overlapping > 0:
            score += overlapping * 20
            factors.append(f"{overlapping} team member(s) already on leave")
        
        # Check duration
        if leave_data.get("start_date") and leave_data.get("end_date"):
            duration = (leave_data["end_date"] - leave_data["start_date"]).days + 1
            if duration > 5:
                score += 30
                factors.append("Extended duration (>5 days)")
            elif duration > 10:
                score += 50
                factors.append("Long duration (>10 days)")
        
        # Check if it's a busy period (e.g., month-end)
        if leave_data.get("start_date"):
            day = leave_data["start_date"].day
            if day >= 25 or day <= 5:
                score += 15
                factors.append("Month-end/start period")
        
        score = min(score, 100)
        
        if score < 40:
            level = "LOW"
        elif score < 70:
            level = "MEDIUM"
        else:
            level = "HIGH"
        
        return {
            "score": score,
            "level": level,
            "factors": factors
        }