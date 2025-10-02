from datetime import datetime, timedelta, date
from typing import Dict, List, Optional
import json
import os
import requests
from app.models.leave import LeaveType, LeaveStatus
from app.config import settings  # Import your settings

class HRAIService:
    """AI Service for HR conversational queries"""
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY  # Use settings instead of os.getenv
        print("GROQ_API_KEY loaded:", "Yes" if self.groq_api_key else "No")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def parse_hr_query(
        self,
        text: str,
        chat_history: List[Dict] = None,
        hr_context: Dict = None
    ) -> Dict:
        """Parse HR natural language query and determine intent"""
        
        if chat_history is None:
            chat_history = []
        if hr_context is None:
            hr_context = {}
        
        today = datetime.now().date()
        
        system_prompt = f"""You are an AI assistant for HR personnel managing employee leaves.

Today's date: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})
Available departments: Frontend, Backend, HR, Design

Your job is to parse HR queries and extract:

1. INTENT (must be one of):
   - QUERY_LEAVES: Show/list leave requests
   - CHECK_BALANCES: Check leave balances
   - ANALYTICS: Analytics, trends, statistics
   - APPROVE_REJECT: Approve or reject leave
   - TEAM_STATUS: Who's available/on leave
   - GENERAL: General question

2. FILTERS (when applicable):
   - department: Frontend, Backend, HR, Design
   - employee_name: specific employee
   - date_filter:
     * type: TODAY, THIS_WEEK, THIS_MONTH, LAST_MONTH, DATE_RANGE, SPECIFIC_DATE
     * start_date: YYYY-MM-DD (for DATE_RANGE)
     * end_date: YYYY-MM-DD (for DATE_RANGE)
   - status: PENDING, APPROVED, REJECTED
   - leave_type: SICK, CASUAL, ANNUAL, MATERNITY, PATERNITY, UNPAID

3. ACTION PARAMETERS (for approvals):
   - action: APPROVE or REJECT
   - leave_id: if mentioned
   - employee_name: if leave_id not provided
   - rejection_reason: if rejecting

4. ANALYTICS TYPE (if intent is ANALYTICS):
   - OVERVIEW, TRENDS, DEPARTMENT, PENDING

EXAMPLES:
- "Show me all leaves today" → intent: QUERY_LEAVES, date_filter: TODAY
- "Who's on leave in Backend this week?" → intent: QUERY_LEAVES, department: Backend, date_filter: THIS_WEEK
- "Approve John's leave" → intent: APPROVE_REJECT, action: APPROVE, employee_name: John
- "Show leave trends" → intent: ANALYTICS, analytics_type: TRENDS
- "Check Sarah's leave balance" → intent: CHECK_BALANCES, employee_name: Sarah

DATE PARSING:
- "today" = {today.strftime('%Y-%m-%d')}
- "tomorrow" = {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
- "this week" = THIS_WEEK
- "last Monday" = calculate date
- "October 5" = convert to {today.year}-10-05

Respond ONLY with valid JSON:
{{
    "intent": "QUERY_LEAVES",
    "department": "Backend" or null,
    "employee_name": "John Doe" or null,
    "date_filter": {{
        "type": "THIS_WEEK",
        "start_date": "2024-10-01" or null,
        "end_date": "2024-10-07" or null
    }} or null,
    "status": "PENDING" or null,
    "leave_type": "SICK" or null,
    "action": "APPROVE" or null,
    "leave_id": 123 or null,
    "rejection_reason": "reason" or null,
    "analytics_type": "TRENDS" or null,
    "suggested_actions": ["action1", "action2"]
}}"""

        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent chat history
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
                
                # Convert date strings to date objects if present
                if parsed.get("date_filter") and parsed["date_filter"].get("start_date"):
                    parsed["date_filter"]["start_date"] = datetime.strptime(
                        parsed["date_filter"]["start_date"], "%Y-%m-%d"
                    ).date()
                
                if parsed.get("date_filter") and parsed["date_filter"].get("end_date"):
                    parsed["date_filter"]["end_date"] = datetime.strptime(
                        parsed["date_filter"]["end_date"], "%Y-%m-%d"
                    ).date()
                
                return parsed
            
            else:
                print(f"Groq API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error calling Groq API: {e}")
        
        # Fallback to simple parsing
        return self._fallback_parse(text)
    
    def _fallback_parse(self, text: str) -> Dict:
        """Simple rule-based fallback parser"""
        text_lower = text.lower()
        
        result = {
            "intent": "GENERAL",
            "department": None,
            "employee_name": None,
            "date_filter": None,
            "status": None,
            "leave_type": None,
            "suggested_actions": []
        }
        
        # Detect intent
        if any(word in text_lower for word in ["show", "list", "who", "leaves", "taking leave"]):
            result["intent"] = "QUERY_LEAVES"
        elif any(word in text_lower for word in ["balance", "remaining", "available days"]):
            result["intent"] = "CHECK_BALANCES"
        elif any(word in text_lower for word in ["approve", "accept", "ok", "confirm"]):
            result["intent"] = "APPROVE_REJECT"
            result["action"] = "APPROVE"
        elif any(word in text_lower for word in ["reject", "deny", "decline"]):
            result["intent"] = "APPROVE_REJECT"
            result["action"] = "REJECT"
        elif any(word in text_lower for word in ["trend", "analytics", "statistics", "stats"]):
            result["intent"] = "ANALYTICS"
            result["analytics_type"] = "OVERVIEW"
        elif any(word in text_lower for word in ["available", "working", "in office"]):
            result["intent"] = "TEAM_STATUS"
        
        # Detect department
        if "frontend" in text_lower:
            result["department"] = "Frontend"
        elif "backend" in text_lower:
            result["department"] = "Backend"
        elif "hr" in text_lower and result["intent"] != "GENERAL":
            result["department"] = "HR"
        elif "design" in text_lower:
            result["department"] = "Design"
        
        # Detect date filter
        if "today" in text_lower or "now" in text_lower:
            result["date_filter"] = {"type": "TODAY"}
        elif "this week" in text_lower:
            result["date_filter"] = {"type": "THIS_WEEK"}
        elif "this month" in text_lower:
            result["date_filter"] = {"type": "THIS_MONTH"}
        elif "last month" in text_lower:
            result["date_filter"] = {"type": "LAST_MONTH"}
        
        # Detect status
        if "pending" in text_lower:
            result["status"] = "PENDING"
        elif "approved" in text_lower:
            result["status"] = "APPROVED"
        
        return result
    
    def generate_hr_response(
        self,
        parsed: Dict,
        data: Dict,
        context: Dict = None
    ) -> str:
        """Generate natural HR response using AI"""
        
        if context is None:
            context = {}
        
        intent = parsed.get("intent")
        
        system_prompt = """You are a professional HR assistant helping HR personnel with leave management.

Generate clear, concise, and actionable responses.

TONE:
- Professional but friendly
- Data-focused and precise
- Action-oriented
- Use appropriate emojis sparingly (📊 📅 ✅ ⚠️)

RESPONSE STRUCTURE:
1. Acknowledge the query
2. Present key findings (be specific with numbers)
3. Highlight important insights
4. Suggest next actions if relevant

Keep responses concise but informative - max 4-5 sentences unless complex data."""

        # Build context-aware prompt
        user_prompt = f"""
INTENT: {intent}
PARSED QUERY: {json.dumps(parsed, indent=2, default=str)}

DATA RETURNED:
{json.dumps(data, indent=2, default=str)}

Generate a natural, helpful response for the HR person.

GUIDELINES:
- If showing leaves: Summarize count, mention key patterns
- If balances: Highlight low balances or concerning utilization
- If analytics: Point out trends and anomalies
- If approval action: Confirm action and next steps
- If team status: Give availability overview

Be specific with numbers and names."""

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
            print(f"AI response generation failed: {e}")
        
        # Fallback to structured response
        return self._generate_fallback_response(parsed, data)
    
    def _generate_fallback_response(self, parsed: Dict, data: Dict) -> str:
        """Generate structured fallback response"""
        intent = parsed.get("intent")
        
        if intent == "QUERY_LEAVES":
            count = data.get("count", 0)
            if count == 0:
                return "📋 No leaves found matching your criteria."
            
            dept = parsed.get("department", "all departments")
            date_info = parsed.get("date_filter", {}).get("type", "")
            return f"📋 Found {count} leave(s) for {dept} {date_info.lower().replace('_', ' ')}. Check the details below."
        
        elif intent == "CHECK_BALANCES":
            count = data.get("count", 0)
            return f"💼 Retrieved leave balance information for {count} employee(s)."
        
        elif intent == "ANALYTICS":
            return "📊 Here's the leave analytics data. Review the trends and patterns."
        
        elif intent == "APPROVE_REJECT":
            if data.get("success"):
                action = data.get("action", "processed")
                employee = data.get("leave", {}).get("employee")
                return f"✅ Successfully {action}d leave request for {employee}."
            else:
                return f"❌ {data.get('message', 'Action could not be completed.')}"
        
        elif intent == "TEAM_STATUS":
            total = data.get("total", 0)
            on_leave = data.get("on_leave", 0)
            available = data.get("available", 0)
            return f"👥 Team Status: {available}/{total} available, {on_leave} on leave today."
        
        return "I've processed your request. Please review the data below."
    
    def generate_insight_summary(self, analytics_data: Dict) -> str:
        """Generate AI-powered insights from analytics data"""
        
        system_prompt = """You are an HR analytics expert. Analyze leave data and provide actionable insights.

Focus on:
- Patterns and trends
- Potential concerns (high leave concentration, low balances)
- Department comparisons
- Recommendations

Keep it concise - 3-4 key insights max."""

        user_prompt = f"""
ANALYTICS DATA:
{json.dumps(analytics_data, indent=2, default=str)}

Provide key insights and recommendations:"""

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
                    "temperature": 0.5,
                    "max_tokens": 250
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            print(f"Insight generation failed: {e}")
        
        return "Analytics data retrieved. Review the charts for detailed patterns."