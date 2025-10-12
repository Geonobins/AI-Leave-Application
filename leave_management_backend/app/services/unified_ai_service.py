from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import json
import requests
import time
from functools import wraps
from app.models.leave import LeaveType, LeaveStatus
from app.config import settings

def retry_with_backoff(max_retries=3, base_delay=2):
    """Decorator for exponential backoff retry logic"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except requests.exceptions.RequestException as e:
                    if attempt == max_retries - 1:
                        raise
                    
                    # Check if it's a rate limit error
                    if hasattr(e, 'response') and e.response is not None:
                        if e.response.status_code == 429:
                            # Extract wait time from error message
                            try:
                                error_data = e.response.json()
                                error_msg = error_data.get('error', {}).get('message', '')
                                if 'Please try again in' in error_msg:
                                    # Parse wait time from message
                                    wait_time = float(error_msg.split('Please try again in ')[1].split('s')[0])
                                    print(f"Rate limited. Waiting {wait_time}s before retry...")
                                    time.sleep(wait_time + 0.5)  # Add buffer
                                    continue
                            except:
                                pass
                    
                    # Exponential backoff
                    wait_time = base_delay * (2 ** attempt)
                    print(f"Request failed (attempt {attempt + 1}/{max_retries}). Retrying in {wait_time}s...")
                    time.sleep(wait_time)
            
            return None
        return wrapper
    return decorator


class UnifiedAIService:
    """Unified AI Service with enhanced error handling, rate limit management, and context preservation"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self._last_request_time = 0
        self._min_request_interval = 1.0  # Minimum 1 second between requests
    
    def _rate_limit_wait(self):
        """Implement client-side rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self._last_request_time
        
        if time_since_last < self._min_request_interval:
            wait_time = self._min_request_interval - time_since_last
            time.sleep(wait_time)
        
        self._last_request_time = time.time()
    
    @retry_with_backoff(max_retries=3, base_delay=2)
    def _make_groq_request(self, messages: List[Dict], temperature: float = 0.1, 
                          max_tokens: int = 500, response_format: Dict = None) -> Optional[Dict]:
        """Make a request to Groq API with retry logic"""
        self._rate_limit_wait()
        
        payload = {
            "model": "llama-3.1-8b-instant",
            "messages": messages,
            "temperature": temperature,
            "max_tokens": max_tokens
        }
        
        if response_format:
            payload["response_format"] = response_format
        
        response = requests.post(
            self.api_url,
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json"
            },
            json=payload,
            timeout=15
        )
        
        if response.status_code == 200:
            return response.json()
        elif response.status_code == 429:
            # Rate limit error - let retry decorator handle it
            raise requests.exceptions.RequestException(response=response)
        else:
            print(f"Groq API Error: {response.status_code} - {response.text}")
            return None
    
    def parse_conversation(
        self,
        text: str,
        chat_history: List[Dict],
        user_context: Dict
    ) -> Dict:
        """Parse leave management conversation with context preservation"""
        
        today = datetime.now().date()
        
        # Extract previously collected data from chat history
        previous_data = self._extract_previous_context(chat_history)
        
        # OPTIMIZED: Condensed system prompt to reduce token usage
        system_prompt = f"""AI assistant for leave management. Today: {today.strftime('%Y-%m-%d')}

USER: {user_context['role']} - {user_context['full_name']} (Manager: {user_context['is_manager']}, HR: {user_context['is_hr']})

PREVIOUSLY COLLECTED: {json.dumps(previous_data, default=str) if previous_data else "None"}
CRITICAL: If user provides NEW information, MERGE with previously collected data. Don't lose context!

Example flow:
- User: "I need leave next Monday" → Collect: start_date=next_monday
- User: "sick leave" → MERGE: leave_type=SICK + start_date=next_monday (preserved!)

INTENTS:
1. REQUEST_LEAVE - Request leave (requires: leave_type, start_date, end_date)
2. APPROVE_REJECT - Approve/reject (Managers/HR only)
3. QUERY_LEAVES - Query leave records
4. CHECK_BALANCE - Check balances
5. TEAM_STATUS - Team availability (Managers/HR)
6. ANALYTICS - Analytics (HR only)
7. QUERY_POLICY - Policy questions (all users)
8. GENERAL - General/greeting

ROLE RULES:
- Employees: Can only view own data, request leaves
- Managers: Can approve leaves, view team data
- HR: Full access to all data

LEAVE TYPES: SICK, CASUAL, ANNUAL, MATERNITY, PATERNITY, UNPAID

CRITICAL PARSING RULES:
- NEVER assume leave_type - must be explicit
- For REQUEST_LEAVE: needs_clarification=true if ANY required field missing AFTER merging with previous context
- Employees: "pending" means THEIR pending leaves
- Managers: "pending" means leaves AWAITING approval
- PRESERVE previously collected data - only ask for what's still missing!

DATE PARSING:
- "tomorrow" = {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
- "today" = {today.strftime('%Y-%m-%d')}
- "next Monday" = {self._get_next_weekday(0).strftime('%Y-%m-%d')}
- "next Tuesday" = {self._get_next_weekday(1).strftime('%Y-%m-%d')}
- "next Wednesday" = {self._get_next_weekday(2).strftime('%Y-%m-%d')}
- "next Thursday" = {self._get_next_weekday(3).strftime('%Y-%m-%d')}
- "next Friday" = {self._get_next_weekday(4).strftime('%Y-%m-%d')}
- "this week" = THIS_WEEK filter

Response JSON:
{{
    "intent": "REQUEST_LEAVE|APPROVE_REJECT|QUERY_LEAVES|CHECK_BALANCE|TEAM_STATUS|ANALYTICS|QUERY_POLICY|GENERAL",
    "leave_type": null,
    "start_date": null,
    "end_date": null,
    "reason": null,
    "is_complete": false,
    "needs_clarification": false,
    "clarification_question": null,
    "action": null,
    "leave_id": null,
    "employee_name": null,
    "status": null,
    "department": null,
    "date_filter": null,
    "policy_query": null,
    "policy_type": null,
    "ui_state": {{
        "component": "GREETING|TYPE_SELECTOR|DATE_PICKER|TEXT_INPUT|PERSON_SELECTOR|CONFIRMATION_CARD|STATUS_CARD|LEAVE_LIST|BALANCE_CARD|POLICY_CARD",
        "stage": "GREETING|TYPE_SELECTION|DATE_SELECTION|REASON_INPUT|RESPONSIBLE_PERSON|CONFIRMATION|FINAL_REVIEW|VIEWING",
        "awaiting_input": null,
        "show_calendar": false,
        "show_type_options": false,
        "show_quick_actions": false,
        "collected_data": {{}}
    }},
    "suggested_actions": []
}}"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Only include last 3 messages to reduce tokens
        for msg in chat_history[-3:]:
            messages.append({
                "role": msg.get("role", "user"),
                "content": msg.get("content", "")[:200]  # Truncate long messages
            })
        
        messages.append({"role": "user", "content": text[:300]})  # Limit user input
        
        is_first_message = len(chat_history) == 0 or (len(chat_history) == 1 and "welcome" in chat_history[0].get("content", "").lower())
        
        try:
            result = self._make_groq_request(
                messages=messages,
                temperature=0.1,
                max_tokens=400,  # Reduced from default
                response_format={"type": "json_object"}
            )
            
            if not result:
                print("No response from Groq API, using fallback")
                # Merge with previous context before fallback
                fallback_result = self._fallback_parse(text, user_context)
                return self._merge_with_previous_context(fallback_result, previous_data)
            
            content = result["choices"][0]["message"]["content"]
            
            try:
                parsed = json.loads(content) if isinstance(content, str) else content
            except json.JSONDecodeError as e:
                print(f"JSON parsing failed: {e}")
                fallback_result = self._fallback_parse(text, user_context)
                return self._merge_with_previous_context(fallback_result, previous_data)
            
            if not isinstance(parsed, dict):
                fallback_result = self._fallback_parse(text, user_context)
                return self._merge_with_previous_context(fallback_result, previous_data)
            
            # Merge with previously collected data
            parsed = self._merge_with_previous_context(parsed, previous_data)
            
            # Process dates and leave types
            parsed = self._process_parsed_data(parsed, user_context, is_first_message, text)
            
            return parsed
                
        except Exception as e:
            print(f"Parse conversation error: {e}")
            fallback_result = self._fallback_parse(text, user_context)
            # Extract previous context even in error case
            previous_data = self._extract_previous_context(chat_history)
            return self._merge_with_previous_context(fallback_result, previous_data)
    
    def _get_next_weekday(self, target_day: int) -> date:
        """Get the date of next occurrence of weekday (0=Monday, 6=Sunday)"""
        today = datetime.now().date()
        days_ahead = target_day - today.weekday()
        if days_ahead <= 0:  # Target day already happened this week
            days_ahead += 7
        return today + timedelta(days=days_ahead)
    
    def _extract_previous_context(self, chat_history: List[Dict]) -> Dict:
        """Extract previously collected data from chat history"""
        previous_data = {}
        
        # Look through recent assistant messages for collected data
        for msg in reversed(chat_history[-5:]):  # Check last 5 messages
            if msg.get("role") == "assistant" and msg.get("data"):
                leave_data = msg["data"].get("leave_data", {})
                
                # Extract fields that were previously collected
                if leave_data.get("leave_type") and not previous_data.get("leave_type"):
                    leave_type = leave_data["leave_type"]
                    # Handle both string and enum
                    if isinstance(leave_type, str):
                        previous_data["leave_type"] = leave_type
                    else:
                        previous_data["leave_type"] = leave_type
                
                if leave_data.get("start_date") and not previous_data.get("start_date"):
                    previous_data["start_date"] = leave_data["start_date"]
                
                if leave_data.get("end_date") and not previous_data.get("end_date"):
                    previous_data["end_date"] = leave_data["end_date"]
                
                if leave_data.get("reason") and not previous_data.get("reason"):
                    previous_data["reason"] = leave_data["reason"]
                
                if leave_data.get("responsible_person") and not previous_data.get("responsible_person"):
                    previous_data["responsible_person"] = leave_data["responsible_person"]
        
        return previous_data
    
    def _merge_with_previous_context(self, parsed: Dict, previous_data: Dict) -> Dict:
        """Merge newly parsed data with previously collected context"""
        if not previous_data:
            return parsed
        
        # Only merge if we're still in REQUEST_LEAVE flow
        if parsed.get("intent") != "REQUEST_LEAVE":
            return parsed
        
        # Merge fields: new data takes precedence, but use previous if new is missing
        if not parsed.get("leave_type") and previous_data.get("leave_type"):
            parsed["leave_type"] = previous_data["leave_type"]
            print(f"✓ Restored leave_type from context: {previous_data['leave_type']}")
        
        if not parsed.get("start_date") and previous_data.get("start_date"):
            # Handle both string and date objects
            if isinstance(previous_data["start_date"], str):
                try:
                    parsed["start_date"] = datetime.strptime(previous_data["start_date"], "%Y-%m-%d").date()
                except:
                    parsed["start_date"] = previous_data["start_date"]
            else:
                parsed["start_date"] = previous_data["start_date"]
            print(f"✓ Restored start_date from context: {parsed['start_date']}")
        
        if not parsed.get("end_date") and previous_data.get("end_date"):
            # Handle both string and date objects
            if isinstance(previous_data["end_date"], str):
                try:
                    parsed["end_date"] = datetime.strptime(previous_data["end_date"], "%Y-%m-%d").date()
                except:
                    parsed["end_date"] = previous_data["end_date"]
            else:
                parsed["end_date"] = previous_data["end_date"]
            print(f"✓ Restored end_date from context: {parsed['end_date']}")
        
        if not parsed.get("reason") and previous_data.get("reason"):
            parsed["reason"] = previous_data["reason"]
            print(f"✓ Restored reason from context")
        
        if not parsed.get("responsible_person") and previous_data.get("responsible_person"):
            parsed["responsible_person"] = previous_data["responsible_person"]
            print(f"✓ Restored responsible_person from context")
        
        return parsed
    
    def _process_parsed_data(self, parsed: Dict, user_context: Dict, 
                            is_first_message: bool, text: str) -> Dict:
        """Process and validate parsed data"""
        
        # Convert date strings to date objects
        for date_field in ['start_date', 'end_date']:
            if parsed.get(date_field) and isinstance(parsed[date_field], str):
                try:
                    parsed[date_field] = datetime.strptime(
                        parsed[date_field], "%Y-%m-%d"
                    ).date()
                except:
                    parsed[date_field] = None
        
        # Handle date_filter dates
        if parsed.get("date_filter") and isinstance(parsed["date_filter"], dict):
            for date_field in ['start_date', 'end_date']:
                date_val = parsed["date_filter"].get(date_field)
                if date_val and isinstance(date_val, str):
                    try:
                        parsed["date_filter"][date_field] = datetime.strptime(
                            date_val, "%Y-%m-%d"
                        ).date()
                    except:
                        parsed["date_filter"][date_field] = None
        
        # Convert leave_type to enum
        if parsed.get("leave_type") and isinstance(parsed["leave_type"], str):
            try:
                parsed["leave_type"] = LeaveType[parsed["leave_type"].upper()]
            except KeyError:
                parsed["leave_type"] = None
        
        # Auto-populate employee_name for non-managers
        intent = parsed.get("intent")
        if intent in ["QUERY_LEAVES", "CHECK_BALANCE"] and not parsed.get("employee_name"):
            if not user_context["is_manager"] or parsed.get("status") == "PENDING":
                parsed["employee_name"] = user_context["full_name"]
        
        # Determine UI state
        if not parsed.get("ui_state"):
            parsed["ui_state"] = self._determine_ui_state(
                parsed, intent, text.lower(), is_first_message
            )
        
        # Check completeness for leave requests
        if intent == "REQUEST_LEAVE":
            parsed = self._check_leave_completeness(parsed)
        
        # Add suggested actions
        if not parsed.get("suggested_actions"):
            parsed["suggested_actions"] = self._get_role_suggested_actions(
                user_context, intent or "GENERAL"
            )
        
        # Validate intent
        valid_intents = ["REQUEST_LEAVE", "APPROVE_REJECT", "QUERY_LEAVES", 
                        "CHECK_BALANCE", "TEAM_STATUS", "ANALYTICS", "QUERY_POLICY", "GENERAL"]
        if not parsed.get("intent") or parsed["intent"] not in valid_intents:
            parsed["intent"] = "GENERAL"
        
        return parsed

    def _determine_ui_state(self, parsed: Dict, intent: str, text_lower: str, is_first_message: bool) -> Dict:
        """Determine which UI component to show based on conversation state"""
        
        # Handle greeting/initial message
        if is_first_message or intent == "GENERAL":
            return {
                "component": "GREETING",
                "stage": "GREETING",
                "awaiting_input": None,
                "show_calendar": False,
                "show_type_options": False,
                "show_quick_actions": True,
                "collected_data": {}
            }
        
        # Handle leave request flow
        if intent == "REQUEST_LEAVE":
            collected = {
                "leave_type": parsed.get("leave_type").value if parsed.get("leave_type") else None,
                "start_date": parsed.get("start_date").isoformat() if parsed.get("start_date") else None,
                "end_date": parsed.get("end_date").isoformat() if parsed.get("end_date") else None,
                "reason": parsed.get("reason")
            }
            
            # Remove None values
            collected = {k: v for k, v in collected.items() if v is not None}
            
            # Determine stage based on what's missing
            if not parsed.get("leave_type"):
                return {
                    "component": "TYPE_SELECTOR",
                    "stage": "TYPE_SELECTION",
                    "awaiting_input": "leave_type",
                    "show_calendar": False,
                    "show_type_options": True,
                    "show_quick_actions": False,
                    "collected_data": collected
                }
            
            elif not parsed.get("start_date") or not parsed.get("end_date"):
                return {
                    "component": "DATE_PICKER",
                    "stage": "DATE_SELECTION",
                    "awaiting_input": "dates",
                    "show_calendar": True,
                    "show_type_options": False,
                    "show_quick_actions": False,
                    "collected_data": collected
                }
            
            elif parsed.get("is_complete") and not parsed.get("responsible_person"):
                return {
                    "component": "PERSON_SELECTOR",
                    "stage": "RESPONSIBLE_PERSON",
                    "awaiting_input": "responsible_person",
                    "show_calendar": False,
                    "show_type_options": False,
                    "show_quick_actions": False,
                    "collected_data": collected
                }
            
            elif parsed.get("is_complete"):
                return {
                    "component": "CONFIRMATION_CARD",
                    "stage": "CONFIRMATION",
                    "awaiting_input": "confirmation",
                    "show_calendar": False,
                    "show_type_options": False,
                    "show_quick_actions": False,
                    "collected_data": collected
                }
            
            else:
                # Need more info
                return {
                    "component": "TEXT_INPUT",
                    "stage": "REASON_INPUT",
                    "awaiting_input": "reason",
                    "show_calendar": False,
                    "show_type_options": False,
                    "show_quick_actions": False,
                    "collected_data": collected
                }
        
        # Handle query leaves
        elif intent == "QUERY_LEAVES":
            return {
                "component": "LEAVE_LIST",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_filters": True,
                "show_status_badges": True,
                "collected_data": {}
            }
        
        # Handle balance check
        elif intent == "CHECK_BALANCE":
            return {
                "component": "BALANCE_CARD",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_breakdown": True,
                "collected_data": {}
            }
        
        # Handle policy query
        elif intent == "QUERY_POLICY":
            return {
                "component": "POLICY_CARD",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_references": True,
                "collected_data": {"policy_type": parsed.get("policy_type")}
            }
        
        # Handle approval/rejection
        elif intent == "APPROVE_REJECT":
            if parsed.get("action") == "CHECK_PENDING":
                return {
                    "component": "LEAVE_LIST",
                    "stage": "VIEWING",
                    "awaiting_input": None,
                    "show_filters": True,
                    "show_status_badges": True,
                    "show_action_buttons": True,
                    "collected_data": {"filter": "PENDING"}
                }
            else:
                return {
                    "component": "STATUS_CARD",
                    "stage": "COMPLETED",
                    "awaiting_input": None,
                    "show_success": parsed.get("action") == "APPROVE",
                    "collected_data": {}
                }
        
        # Handle team status
        elif intent == "TEAM_STATUS":
            return {
                "component": "TEAM_STATUS_CARD",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_availability": True,
                "collected_data": {}
            }
        
        # Default fallback
        return {
            "component": "TEXT_INPUT",
            "stage": "GENERAL",
            "awaiting_input": None,
            "show_calendar": False,
            "show_type_options": False,
            "show_quick_actions": True,
            "collected_data": {}
        }

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
        """Check if leave request has all required fields and update UI state"""
        missing = []
        
        # Check leave_type first
        if not parsed.get("leave_type"):
            missing.append("leave_type")
            parsed["clarification_question"] = "What type of leave do you need? (Sick, Casual, Annual, etc.)"
            parsed["needs_clarification"] = True
            parsed["is_complete"] = False
            parsed["missing_fields"] = missing
            parsed["ui_state"] = {
                "component": "TYPE_SELECTOR",
                "stage": "TYPE_SELECTION",
                "awaiting_input": "leave_type",
                "show_calendar": False,
                "show_type_options": True,
                "show_quick_actions": False,
                "collected_data": {}
            }
            return parsed  # Return early - don't check other fields yet
        
        # Collect data so far
        collected_data = {
            "leave_type": parsed.get("leave_type").value if parsed.get("leave_type") else None,
            "start_date": parsed.get("start_date").isoformat() if parsed.get("start_date") else None,
            "end_date": parsed.get("end_date").isoformat() if parsed.get("end_date") else None,
            "reason": parsed.get("reason")
        }
        
        # Only check dates if leave_type exists
        if not parsed.get("start_date"):
            missing.append("start_date")
            parsed["clarification_question"] = "When would you like to start your leave?"
            parsed["needs_clarification"] = True
            parsed["is_complete"] = False
            parsed["ui_state"] = {
                "component": "DATE_PICKER",
                "stage": "DATE_SELECTION",
                "awaiting_input": "dates",
                "show_calendar": True,
                "show_type_options": False,
                "show_quick_actions": False,
                "collected_data": {k: v for k, v in collected_data.items() if v is not None}
            }
        elif not parsed.get("end_date"):
            # Auto-set end_date to start_date for single day (this is fine)
            parsed["end_date"] = parsed["start_date"]
        
        parsed["missing_fields"] = missing
        
        # Only mark complete if ALL required fields present
        if parsed.get("leave_type") and parsed.get("start_date") and parsed.get("end_date"):
            parsed["is_complete"] = True
            parsed["needs_clarification"] = False
            parsed["ui_state"] = {
                "component": "CONFIRMATION_CARD",
                "stage": "CONFIRMATION",
                "awaiting_input": "confirmation",
                "show_calendar": False,
                "show_type_options": False,
                "show_quick_actions": False,
                "collected_data": {k: v for k, v in collected_data.items() if v is not None}
            }
        else:
            parsed["is_complete"] = False
            parsed["needs_clarification"] = True
        
        return parsed
    
    def _fallback_parse(self, text: str, user_context: Dict) -> Dict:
        """Enhanced rule-based fallback parser with policy query support and UI state"""
        text_lower = text.lower().strip()
        
        # Detect if first message
        is_greeting = any(word in text_lower for word in ["hi", "hello", "hey", "welcome", "start"])
        
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
            "suggested_actions": self._get_role_suggested_actions(user_context, "GENERAL"),
            "ui_state": {
                "component": "GREETING" if is_greeting else "TEXT_INPUT",
                "stage": "GREETING" if is_greeting else "GENERAL",
                "awaiting_input": None,
                "show_calendar": False,
                "show_type_options": False,
                "show_quick_actions": True,
                "collected_data": {}
            }
        }
        
        # Check for policy queries
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
                result["ui_state"] = {
                    "component": "POLICY_CARD",
                    "stage": "VIEWING",
                    "awaiting_input": None,
                    "show_references": True,
                    "collected_data": {"policy_type": result["policy_type"]}
                }
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
            
            result["ui_state"] = {
                "component": "LEAVE_LIST",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_filters": True,
                "show_status_badges": True,
                "collected_data": {}
            }
        
        # Intent: Pending approvals
        elif any(word in text_lower for word in ["pending", "approval", "approve", "need approval", "awaiting"]):
            if user_context["is_manager"]:
                result["intent"] = "APPROVE_REJECT"
                result["action"] = "CHECK_PENDING"
                result["suggested_actions"] = ["View pending approvals", "Approve leaves", "Check team status"]
                result["ui_state"] = {
                    "component": "LEAVE_LIST",
                    "stage": "VIEWING",
                    "awaiting_input": None,
                    "show_filters": True,
                    "show_status_badges": True,
                    "show_action_buttons": True,
                    "collected_data": {"filter": "PENDING"}
                }
            else:
                result["intent"] = "QUERY_LEAVES"
                result["status"] = "PENDING"
                result["employee_name"] = user_context["full_name"]
                result["suggested_actions"] = ["Check my leaves", "View balance", "Request leave"]
                result["ui_state"] = {
                    "component": "LEAVE_LIST",
                    "stage": "VIEWING",
                    "awaiting_input": None,
                    "show_filters": True,
                    "show_status_badges": True,
                    "collected_data": {}
                }
        
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
            
            # Try to extract dates
            if "tomorrow" in text_lower:
                result["start_date"] = datetime.now().date() + timedelta(days=1)
                result["end_date"] = result["start_date"]
            elif "today" in text_lower:
                result["start_date"] = datetime.now().date()
                result["end_date"] = result["start_date"]
            elif "next monday" in text_lower:
                result["start_date"] = self._get_next_weekday(0)
                result["end_date"] = result["start_date"]
            elif "next tuesday" in text_lower:
                result["start_date"] = self._get_next_weekday(1)
                result["end_date"] = result["start_date"]
            elif "next wednesday" in text_lower:
                result["start_date"] = self._get_next_weekday(2)
                result["end_date"] = result["start_date"]
            elif "next thursday" in text_lower:
                result["start_date"] = self._get_next_weekday(3)
                result["end_date"] = result["start_date"]
            elif "next friday" in text_lower:
                result["start_date"] = self._get_next_weekday(4)
                result["end_date"] = result["start_date"]
            
            # Set UI state
            if result["leave_type"]:
                if result["start_date"]:
                    # Both type and date collected
                    result["ui_state"] = {
                        "component": "CONFIRMATION_CARD",
                        "stage": "CONFIRMATION",
                        "awaiting_input": "confirmation",
                        "show_calendar": False,
                        "show_type_options": False,
                        "show_quick_actions": False,
                        "collected_data": {
                            "leave_type": result["leave_type"].value,
                            "start_date": result["start_date"].isoformat(),
                            "end_date": result["end_date"].isoformat()
                        }
                    }
                else:
                    # Only type collected, need dates
                    result["ui_state"] = {
                        "component": "DATE_PICKER",
                        "stage": "DATE_SELECTION",
                        "awaiting_input": "dates",
                        "show_calendar": True,
                        "show_type_options": False,
                        "show_quick_actions": False,
                        "collected_data": {"leave_type": result["leave_type"].value}
                    }
            else:
                # Need type selection
                result["ui_state"] = {
                    "component": "TYPE_SELECTOR",
                    "stage": "TYPE_SELECTION",
                    "awaiting_input": "leave_type",
                    "show_calendar": False,
                    "show_type_options": True,
                    "show_quick_actions": False,
                    "collected_data": {}
                }
        
        # Intent: Balance check
        elif any(word in text_lower for word in ["balance", "available days", "leave days", "how many days"]):
            result["intent"] = "CHECK_BALANCE"
            result["suggested_actions"] = ["Request leave", "View my leaves"]
            result["ui_state"] = {
                "component": "BALANCE_CARD",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_breakdown": True,
                "collected_data": {}
            }
        
        # Intent: Team status (managers only)
        elif any(word in text_lower for word in ["team status", "team availability", "my team"]) and user_context["is_manager"]:
            result["intent"] = "TEAM_STATUS"
            result["suggested_actions"] = ["Pending approvals", "View analytics", "Check balances"]
            result["ui_state"] = {
                "component": "TEAM_STATUS_CARD",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_availability": True,
                "collected_data": {}
            }
        
        # Intent: General leave queries
        elif any(word in text_lower for word in ["show leaves", "leave list", "my leaves", "leave history"]):
            result["intent"] = "QUERY_LEAVES"
            result["suggested_actions"] = ["Check balance", "Request leave"]
            
            if "my" in text_lower and not user_context["is_manager"]:
                result["employee_name"] = user_context["full_name"]
            
            result["ui_state"] = {
                "component": "LEAVE_LIST",
                "stage": "VIEWING",
                "awaiting_input": None,
                "show_filters": True,
                "show_status_badges": True,
                "collected_data": {}
            }
        
        # Handle simple leave type mentions (for context continuation)
        elif text_lower in ["sick", "sick leave", "casual", "casual leave", "annual", "annual leave", "vacation"]:
            result["intent"] = "REQUEST_LEAVE"
            
            if "sick" in text_lower:
                result["leave_type"] = LeaveType.SICK
            elif "casual" in text_lower:
                result["leave_type"] = LeaveType.CASUAL
            elif "annual" in text_lower or "vacation" in text_lower:
                result["leave_type"] = LeaveType.ANNUAL
            
            result["needs_clarification"] = True
            result["missing_fields"] = ["start_date"]
            result["clarification_question"] = "When would you like to start your leave?"
            result["ui_state"] = {
                "component": "DATE_PICKER",
                "stage": "DATE_SELECTION",
                "awaiting_input": "dates",
                "show_calendar": True,
                "show_type_options": False,
                "show_quick_actions": False,
                "collected_data": {"leave_type": result["leave_type"].value if result["leave_type"] else None}
            }
        
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
        
        # OPTIMIZED: Much shorter prompt
        system_prompt = f"""Leave assistant for {user_context['full_name']} ({user_context['role']}).

INTENT: {intent}
Policy violations: {has_violations}

Be friendly, clear, and actionable. 2-3 sentences for simple queries."""

        # Simplified user prompt
        user_prompt = f"""Parsed: {json.dumps(parsed, default=str)[:500]}
Data: {json.dumps(data, default=str)[:500]}

Generate helpful response addressing the request and any policy issues."""

        try:
            result = self._make_groq_request(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=250  # Reduced
            )
            
            if result:
                return result["choices"][0]["message"]["content"].strip()
            else:
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
                response = "⚠️ Policy Violation Detected\n\n"
                response += "Your request cannot be processed due to the following policy violations:\n\n"
                for i, violation in enumerate(violations, 1):
                    response += f"{i}. {violation}\n"
                
                # Show relevant policies
                relevant = policy_compliance.get("relevant_policies", [])
                if relevant:
                    response += "\n📋 Relevant Policy:\n"
                    response += f"- {relevant[0]['section_title']}\n"
                    response += f"  {relevant[0]['content'][:200]}...\n"
                
                response += "\nPlease revise your request to comply with company policy."
                return response
            
            if warnings:
                warning_text = "\n\n⚠️ Note: " + "; ".join(warnings)
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
                
                response = f"✅ Your {leave_type.value.lower() if leave_type else 'leave'} request for {duration} day(s) "
                response += f"from {leave_data.get('start_date')} to {leave_data.get('end_date')}.\n\n"
                
                # Add balance info
                balance = data.get("leave_balance")
                if balance:
                    response += f"📊 Your balance: {balance['available']}/{balance['total']} days available.\n\n"
                
                # Add responsible person suggestions
                suggested = data.get("suggested_responsible_persons", [])
                if suggested:
                    response += "👥 Suggested colleagues to handle your responsibilities:\n"
                    for i, person in enumerate(suggested[:3], 1):
                        response += f"{i}. {person['name']} ({person['position']}) - {person['reason']}\n"
                    response += "\nReply with a number to select, or 'submit' to proceed without assignment."
                else:
                    response += "Type 'submit' to finalize your leave request."
                
                # Add impact warning
                impact = data.get("team_impact", {})
                if impact.get("level") in ["MEDIUM", "HIGH"]:
                    response += f"\n\n⚠️ Note: {', '.join(impact.get('factors', []))}"
                
                return response
            
            return "I'm here to help you request leave. What type of leave do you need?"
        
        elif intent == "APPROVE_REJECT":
            if data.get("success"):
                action = data.get("action", "processed")
                leave_info = data.get("leave", {})
                emoji = "✅" if action == "approved" else "❌"
                return f"{emoji} Successfully {action} leave request for {leave_info.get('employee')} ({leave_info.get('dates')})."
            else:
                return data.get("message", "Unable to process the approval/rejection.")
        
        elif intent == "QUERY_LEAVES":
            count = data.get("count", 0)
            if count == 0:
                return "No leaves found matching your criteria."
            
            leaves = data.get("leaves", [])
            response = f"📋 Found {count} leave record(s):\n\n"
            
            for leave in leaves[:5]:  # Show first 5
                status_emoji = {"PENDING": "⏳", "APPROVED": "✅", "REJECTED": "❌"}.get(leave['status'], "•")
                response += f"{status_emoji} {leave['employee_name']} ({leave['department']}): "
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
                response = "📊 Your leave balance:\n\n"
                for bal in balances:
                    response += f"• {bal['leave_type']}: {bal['available']}/{bal['total']} days available "
                    response += f"({bal['used']} used)\n"
            else:
                # Manager/HR checking team balances
                response = f"📊 Leave balances for {data.get('count')} employee(s):\n\n"
                for bal in balances[:10]:
                    response += f"• {bal['employee_name']}: {bal['leave_type']} - "
                    response += f"{bal['available']}/{bal['total']} available\n"
            
            return response
        
        elif intent == "TEAM_STATUS":
            total = data.get("total", 0)
            on_leave = data.get("on_leave", 0)
            available = data.get("available", 0)
            
            response = f"👥 Team Status: {available}/{total} available, {on_leave} on leave\n\n"
            
            team_status = data.get("team_status", [])
            on_leave_list = [t for t in team_status if t["status"] == "On Leave"]
            
            if on_leave_list:
                response += "Currently on leave:\n"
                for member in on_leave_list[:5]:
                    response += f"• {member['employee_name']} ({member['position']}) - {member.get('leave_type', 'N/A')}\n"
            else:
                response += "✅ Everyone is available."
            
            return response
        
        elif intent == "ANALYTICS":
            response = "📊 Analytics Overview:\n\n"
            
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
                return data.get("message", "I couldn't find specific policy information. Please contact HR for clarification.")
            
            response = f"📋 Here's what I found about your question:\n\n"
            
            for i, policy in enumerate(policies[:2], 1):  # Show top 2
                response += f"**{policy['section_title']}**\n"
                response += f"{policy['content'][:300]}...\n"
                response += f"_(From: {policy['policy_name']} - {policy['relevance']} relevant)_\n\n"
            
            if len(policies) > 2:
                response += f"... and {len(policies) - 2} more relevant sections found.\n\n"
            
            response += "Would you like to know more about any specific aspect?"
            return response
        
        else:
            return "👋 How can I help you with leave management today? You can request leave, check balances, view team status, ask about policies, or ask me anything related to leaves."
    
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