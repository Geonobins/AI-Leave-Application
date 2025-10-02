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

For MANAGERS/HR:
- Can approve/reject leaves
- "pending requests" means LEAVES AWAITING THEIR APPROVAL
- Can view team status and department data

Determine the INTENT and extract relevant information:

INTENTS:
1. REQUEST_LEAVE - User wants to request leave
2. APPROVE_REJECT - Approve or reject someone's leave (MANAGERS/HR ONLY)
3. QUERY_LEAVES - Query leave records
4. CHECK_BALANCE - Check leave balances
5. TEAM_STATUS - Check team availability (MANAGERS/HR ONLY)
6. ANALYTICS - View analytics (HR ONLY)
7. GENERAL - General question or greeting

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
    "intent": "QUERY_LEAVES",
    "leave_type": null,
    "start_date": null,
    "end_date": null,
    "reason": null,
    "is_complete": false,
    "needs_clarification": false,
    "action": null,
    "leave_id": null,
    "employee_name": "{user_context['full_name']}",
    "date_filter": null,
    "department": null,
    "status": "PENDING",
    "suggested_actions": ["Check my leaves", "View all pending"]
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
                parsed = json.loads(result["choices"][0]["message"]["content"])
                
                # Convert date strings to date objects
                if parsed.get("start_date"):
                    try:
                        parsed["start_date"] = datetime.strptime(
                            parsed["start_date"], "%Y-%m-%d"
                        ).date()
                    except:
                        pass
                
                if parsed.get("end_date"):
                    try:
                        parsed["end_date"] = datetime.strptime(
                            parsed["end_date"], "%Y-%m-%d"
                        ).date()
                    except:
                        pass
                
                # Handle date_filter dates
                if parsed.get("date_filter"):
                    if parsed["date_filter"].get("start_date"):
                        try:
                            parsed["date_filter"]["start_date"] = datetime.strptime(
                                parsed["date_filter"]["start_date"], "%Y-%m-%d"
                            ).date()
                        except:
                            pass
                    
                    if parsed["date_filter"].get("end_date"):
                        try:
                            parsed["date_filter"]["end_date"] = datetime.strptime(
                                parsed["date_filter"]["end_date"], "%Y-%m-%d"
                            ).date()
                        except:
                            pass
                
                # Convert leave_type string to enum
                if parsed.get("leave_type"):
                    try:
                        parsed["leave_type"] = LeaveType[parsed["leave_type"]]
                    except KeyError:
                        parsed["leave_type"] = None
                
                # Auto-populate employee_name for employees querying their own data
                if parsed["intent"] in ["QUERY_LEAVES", "CHECK_BALANCE"] and not parsed.get("employee_name"):
                    if not user_context["is_manager"] or parsed.get("status") == "PENDING":
                        parsed["employee_name"] = user_context["full_name"]
                
                # Validate completeness for leave requests
                if parsed["intent"] == "REQUEST_LEAVE":
                    parsed = self._check_leave_completeness(parsed)
                
                # Add role-appropriate suggested actions
                if not parsed.get("suggested_actions"):
                    parsed["suggested_actions"] = self._get_role_suggested_actions(user_context, parsed["intent"])
                
                return parsed
            
            else:
                print(f"Groq API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error calling Groq API: {e}")
        
        # Fallback parser with role awareness
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
            else:
                return ["Check my leaves", "Request leave", "View balance"]
        
        elif user_context["is_hr"]:
            # HR actions
            if intent == "APPROVE_REJECT":
                return ["View all pending", "Process approvals", "Team status"]
            elif intent == "QUERY_LEAVES":
                return ["Department report", "View analytics", "Pending approvals"]
            else:
                return ["Pending approvals", "Team status", "View analytics"]
        
        else:
            # Manager actions
            if intent == "APPROVE_REJECT":
                return ["View pending approvals", "Team status", "Approve all"]
            elif intent == "QUERY_LEAVES":
                return ["Team leaves", "Pending approvals", "Balance report"]
            else:
                return ["Pending approvals", "Team status", "View my team"]
    
    def _check_leave_completeness(self, parsed: Dict) -> Dict:
        """Check if leave request has all required fields"""
        missing = []
        
        if not parsed.get("leave_type"):
            missing.append("leave_type")
            parsed["clarification_question"] = "What type of leave do you need? (Sick, Casual, Annual, etc.)"
            parsed["needs_clarification"] = True
        elif not parsed.get("start_date"):
            missing.append("start_date")
            parsed["clarification_question"] = "When would you like to start your leave? (e.g., tomorrow, Oct 5)"
            parsed["needs_clarification"] = True
        elif not parsed.get("end_date"):
            missing.append("end_date")
            # Auto-set end_date to start_date for single day
            if parsed.get("start_date"):
                parsed["end_date"] = parsed["start_date"]
                parsed["clarification_question"] = f"Your leave is set for {parsed['start_date'].strftime('%B %d')}. Is this just for one day?"
                parsed["needs_clarification"] = True
        
        parsed["missing_fields"] = missing
        
        if parsed.get("leave_type") and parsed.get("start_date") and parsed.get("end_date"):
            parsed["is_complete"] = True
            parsed["needs_clarification"] = False
        else:
            parsed["is_complete"] = False
        
        return parsed
    
    def _fallback_parse(self, text: str, user_context: Dict) -> Dict:
        """Simple rule-based fallback parser"""
        text_lower = text.lower()
        
        result = {
            "intent": "GENERAL",
            "leave_type": None,
            "start_date": None,
            "end_date": None,
            "reason": None,
            "is_complete": False,
            "needs_clarification": False,
            "missing_fields": [],
            "status": None,
            "date_filter": None
        }
        
        # Detect intent for pending approvals
        if any(word in text_lower for word in ["pending", "approval", "approve", "need approval"]):
            result["intent"] = "QUERY_LEAVES"
            result["status"] = LeaveStatus.PENDING
        
        # Detect intent for general leave queries
        elif any(word in text_lower for word in ["who's on leave", "show leaves", "leave list", "who is absent", "leaves"]):
            result["intent"] = "QUERY_LEAVES"
            
            if "today" in text_lower:
                result["date_filter"] = {"type": "TODAY"}
            elif "this week" in text_lower:
                result["date_filter"] = {"type": "THIS_WEEK"}
        
        return result
    
    def generate_response(
        self,
        intent: str,
        parsed: Dict,
        data: Dict,
        user_context: Dict
    ) -> str:
        """Generate contextual response based on intent and data"""
        
        system_prompt = f"""You are a helpful leave management assistant.

User: {user_context['full_name']} ({user_context['role']} - {user_context['position']})

Generate natural, conversational responses.

INTENT: {intent}

TONE GUIDELINES:
- Friendly and professional
- Clear and actionable
- Adapt to the situation:
  * REQUEST_LEAVE: Be supportive, confirm details, guide next steps
  * APPROVE_REJECT: Be clear about the action taken
  * QUERY_LEAVES: Present data clearly with key insights
  * CHECK_BALANCE: Show numbers clearly
  * TEAM_STATUS: Give overview with important highlights
  * ANALYTICS: Focus on insights and trends

Keep responses 2-3 sentences for simple queries, longer for complex data."""

        user_prompt = f"""
PARSED DATA:
{json.dumps(parsed, indent=2, default=str)}

RESULT DATA:
{json.dumps(data, indent=2, default=str)}

Generate a helpful response for the user:"""

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
                    "max_tokens": 200
                },
                timeout=8
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                return ai_response.strip()
                
        except Exception as e:
            print(f"Response generation failed: {e}")
        
        # Fallback responses
        return self._generate_fallback_response(intent, parsed, data, user_context)
    
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
                
                response = f"Got it! Your {leave_type.value.lower() if leave_type else 'leave'} request for {duration} day(s) "
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
                    response += "\nReply with a number to select, or 'submit' to finalize your leave request."
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
                response += "Everyone is available!"
            
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
        
        else:
            return "How can I help you with leave management today? You can request leave, check balances, view team status, or ask me anything related to leaves."
    
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