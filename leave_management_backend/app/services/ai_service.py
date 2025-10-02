# ============================================================================
# FILE: app/services/ai_service.py (Groq - FREE Version)
# ============================================================================
from datetime import datetime, timedelta, date
from typing import Dict, Optional, List
from app.models.leave import LeaveType
from app.config import settings  # Import your settings
import json
import os
import requests

class AIService:
    
    def __init__(self):
        self.groq_api_key = settings.GROQ_API_KEY  # Use settings instead of os.getenv
        print("GROQ_API_KEY loaded:", "Yes" if self.groq_api_key else "No")
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def parse_leave_request_with_context(
        self,
        text: str, 
        chat_history: List[Dict] = None,
        user_context: Dict = None
    ) -> Dict:
        """Parse natural language leave request using Groq (FREE)"""
        if chat_history is None:
            chat_history = []
        if user_context is None:
            user_context = {}
        
        today = datetime.now().date()
        
        system_prompt = f"""You are a helpful assistant that extracts leave request information.

Today's date: {today.strftime('%Y-%m-%d')} ({today.strftime('%A')})

Extract:
1. leave_type: SICK, CASUAL, ANNUAL, MATERNITY, PATERNITY, or UNPAID
2. start_date: YYYY-MM-DD format
3. end_date: YYYY-MM-DD format
4. reason: brief description

Rules:
- "tomorrow" = {(today + timedelta(days=1)).strftime('%Y-%m-%d')}
- "next Monday" = calculate the date
- "3 days" = assume starting tomorrow unless specified
- Use previous context: {json.dumps(user_context)}

Respond ONLY with valid JSON:
{{
    "leave_type": "SICK" or null,
    "start_date": "2024-10-05" or null,
    "end_date": "2024-10-07" or null,
    "reason": "brief reason" or null
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
                    "model": "llama-3.1-8b-instant",  # FREE & Fast
                    "messages": messages,
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                extracted_data = json.loads(result["choices"][0]["message"]["content"])
                
                # Convert string dates to date objects
                if extracted_data.get("start_date"):
                    extracted_data["start_date"] = datetime.strptime(
                        extracted_data["start_date"], "%Y-%m-%d"
                    ).date()
                
                if extracted_data.get("end_date"):
                    extracted_data["end_date"] = datetime.strptime(
                        extracted_data["end_date"], "%Y-%m-%d"
                    ).date()
                
                # Convert leave_type to enum
                if extracted_data.get("leave_type"):
                    try:
                        extracted_data["leave_type"] = LeaveType[extracted_data["leave_type"]]
                    except KeyError:
                        extracted_data["leave_type"] = None
                
                extracted_data = self._check_completeness(extracted_data)
                return extracted_data
            else:
                print(f"Groq API Error: {response.status_code} - {response.text}")
                
        except Exception as e:
            print(f"Error calling Groq API: {e}")
        
        return self._fallback_parse(text, user_context)
    
    def _fallback_parse(self, text: str, user_context: Dict) -> Dict:
        """Fallback to simple parsing if API fails"""
        import re
        
        text_lower = text.lower()
        result = {
            "leave_type": user_context.get("leave_type"),
            "start_date": user_context.get("start_date"),
            "end_date": user_context.get("end_date"),
            "reason": user_context.get("reason"),
            "missing_fields": [],
            "needs_clarification": False,
            "clarification_question": None,
            "is_complete": False
        }
        
        # Extract leave type
        if not result["leave_type"]:
            if "sick" in text_lower or "ill" in text_lower or "unwell" in text_lower:
                result["leave_type"] = LeaveType.SICK
            elif "casual" in text_lower or "personal" in text_lower:
                result["leave_type"] = LeaveType.CASUAL
            elif "annual" in text_lower or "vacation" in text_lower:
                result["leave_type"] = LeaveType.ANNUAL
        
        # Extract dates
        today = datetime.now().date()
        if "tomorrow" in text_lower:
            result["start_date"] = today + timedelta(days=1)
            result["end_date"] = today + timedelta(days=1)
        elif "today" in text_lower:
            result["start_date"] = today
            result["end_date"] = today
        
        # Duration
        days_match = re.search(r'(\d+)\s*day', text_lower)
        if days_match:
            num_days = int(days_match.group(1))
            if not result["start_date"]:
                result["start_date"] = today + timedelta(days=1)
            result["end_date"] = result["start_date"] + timedelta(days=num_days - 1)
        
        result = self._check_completeness(result)
        return result
    
    def _check_completeness(self, result: Dict) -> Dict:
        """Check if all required fields are present"""
        missing = []
        
        if not result.get("leave_type"):
            missing.append("leave_type")
            result["clarification_question"] = "What type of leave do you need? (Sick, Casual, or Annual)"
            result["needs_clarification"] = True
        elif not result.get("start_date"):
            missing.append("start_date")
            result["clarification_question"] = "Which day would you like to start? (e.g., tomorrow, Monday, October 5)"
            result["needs_clarification"] = True
        elif not result.get("end_date"):
            missing.append("end_date")
            if result.get("start_date"):
                result["end_date"] = result["start_date"]
                result["clarification_question"] = f"Your leave is set for 1 day on {result['start_date'].strftime('%B %d')}. How many days do you need in total?"
                result["needs_clarification"] = True
        
        result["missing_fields"] = missing
        
        if result.get("leave_type") and result.get("start_date") and result.get("end_date"):
            result["is_complete"] = True
            result["needs_clarification"] = False
        
        return result
    
    def generate_conversational_response(
        self, 
        result: Dict, 
        suggested_persons: List[Dict] = None,
        user_context: Dict = None,
        chat_history: List[Dict] = None
    ) -> str:
        """Generate dynamic, contextual responses using AI"""
        
        if user_context is None:
            user_context = {}
        if chat_history is None:
            chat_history = []
        
        # Prepare context for AI
        context_info = {
            "extracted_data": result,
            "suggested_handover_persons": suggested_persons,
            "user_previous_requests": user_context.get("previous_requests", []),
            "user_leave_balance": user_context.get("leave_balance", {}),
            "team_availability": user_context.get("team_status", {})
        }
        
        system_prompt = """You are a friendly HR assistant helping employees with leave requests.

Based on the extracted data, generate a natural, conversational response.

TONE GUIDELINES:
- Friendly and empathetic
- Professional but warm
- Clear and helpful
- Adapt to the situation:
  * If request is complete: Be enthusiastic and confirm details
  * If missing information: Be gently guiding, ask clarifying questions
  * If there are issues: Be supportive and solution-oriented

SPECIAL SITUATIONS:
- If this is user's 3rd+ leave this month: "I notice you've had a few leaves recently, hope everything's okay!"
- If long duration: "That's a decent break! Hope you have a good rest."
- If sick leave: "Hope you feel better soon!"
- If overlapping with team leaves: "Just so you know, a couple of teammates are also off during this period."

RESPONSE STRUCTURE:
1. Acknowledge the request naturally
2. Summarize the understood details
3. If incomplete: Ask exactly ONE clear question
4. If complete: Confirm details and suggest next steps
5. Add appropriate emojis where natural

Keep responses concise but warm - max 2-3 sentences."""
        
        user_prompt = f"""
CONTEXT:
{json.dumps(context_info, indent=2, default=str)}

EXTRACTED LEAVE DATA:
- Complete: {result.get('is_complete', False)}
- Missing: {result.get('missing_fields', [])}
- Leave Type: {result.get('leave_type')}
- Start: {result.get('start_date')}
- End: {result.get('end_date')}
- Reason: {result.get('reason', 'Not specified')}

Please generate a natural response:"""
        
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
                    "temperature": 0.7,  # More creative
                    "max_tokens": 150
                },
                timeout=8
            )
            
            if response.status_code == 200:
                ai_response = response.json()["choices"][0]["message"]["content"]
                return ai_response.strip()
                
        except Exception as e:
            print(f"AI response generation failed: {e}")
        
        # Fallback to original static responses
        return self._static_fallback_response(result, suggested_persons)

    def _static_fallback_response(self, result: Dict, suggested_persons: List[Dict]) -> str:
        """Original static responses as fallback"""
        if result.get("is_complete"):
            duration = (result["end_date"] - result["start_date"]).days + 1
            leave_type = result['leave_type'].value.lower() if hasattr(result['leave_type'], 'value') else str(result['leave_type']).lower()
            
            response = f"✅ Got it! Your {leave_type} leave is set for {duration} day{'s' if duration > 1 else ''}:\n"
            response += f"📅 {result['start_date'].strftime('%b %d')} - {result['end_date'].strftime('%b %d')}\n"
            
            if suggested_persons:
                response += f"\n🤝 Suggested handover contacts:\n"
                for i, person in enumerate(suggested_persons[:3], 1):
                    response += f"{i}. {person['name']} ({person['position']})\n"
                response += "\nReply with a number or 'submit' to proceed!"
            else:
                response += "\nType 'submit' to finalize! 🚀"
            
            return response
        
        return result.get("clarification_question", "Could you tell me more about your leave request?")

    def generate_impact_analysis_message(self, impact_data: Dict, leave_data: Dict) -> str:
        """Generate contextual impact analysis using AI"""
        
        system_prompt = """You're an HR analyst explaining leave impact to employees.

Translate technical impact scores into helpful, non-alarming messages.

IMPACT LEVELS:
- LOW: "No major concerns"
- MEDIUM: "Some considerations"  
- HIGH: "Important to plan for"

TONE:
- Factual but supportive
- Solution-oriented, not restrictive
- Emphasize planning over problems

Include 1-2 practical suggestions if impact is MEDIUM/HIGH."""

        user_prompt = f"""
IMPACT ANALYSIS:
- Score: {impact_data['score']}/100
- Level: {impact_data['level']}
- Factors: {', '.join(impact_data['factors'])}

LEAVE DETAILS:
- Duration: {(leave_data['end_date'] - leave_data['start_date']).days + 1} days
- Type: {leave_data['leave_type']}

Generate a brief, helpful message about the team impact:"""

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
                    "temperature": 0.3,
                    "max_tokens": 100
                },
                timeout=5
            )
            
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"].strip()
                
        except Exception as e:
            print(f"Impact message generation failed: {e}")
        
        # Fallback
        level = impact_data['level']
        if level == "LOW":
            return "✅ No significant team impact expected. Good to go!"
        elif level == "MEDIUM": 
            return "⚠️ Some team coverage needed. Please coordinate handover."
        else:
            return "🚨 Significant impact anticipated. Let's discuss coverage planning."
    
    @staticmethod
    def calculate_impact_score(leave_data: Dict, team_data: List) -> Dict:
        """Calculate impact score"""
        score = 0
        factors = []
        
        overlapping = len([t for t in team_data if t.get("on_leave")])
        if overlapping > 0:
            score += overlapping * 20
            factors.append(f"{overlapping} team member(s) on leave")
        
        if leave_data.get("start_date") and leave_data.get("end_date"):
            duration = (leave_data["end_date"] - leave_data["start_date"]).days + 1
            if duration > 5:
                score += 30
                factors.append("Extended duration")
        
        score = min(score, 100)
        impact_level = "LOW" if score < 40 else "MEDIUM" if score < 70 else "HIGH"
        
        return {"score": score, "level": impact_level, "factors": factors}