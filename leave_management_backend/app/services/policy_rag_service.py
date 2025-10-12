from sqlalchemy.orm import Session
from typing import List, Dict
import numpy as np
import json
from app.services.policy_embedding_service import PolicyEmbeddingService
import requests

class PolicyRAGService:
    """RAG service for policy compliance checking"""
    
    def __init__(self, db: Session, api_key: str):
        self.db = db
        self.embedding_service = PolicyEmbeddingService(api_key)
    
    def retrieve_relevant_policies(
        self,
        query: str,
        top_k: int = 5,
        policy_type: str = None
    ) -> List[Dict]:
        """Retrieve most relevant policy chunks for a query"""
        from app.models.policy_chunk import PolicyChunk
        from app.models.company_policy import CompanyPolicy
        
        # Generate query embedding
        query_embedding = self.embedding_service.generate_embedding(query)
        
        # Get all active policy chunks
        query = self.db.query(PolicyChunk, CompanyPolicy).join(
            CompanyPolicy, PolicyChunk.policy_id == CompanyPolicy.id
        ).filter(CompanyPolicy.is_active == True)
        
        if policy_type:
            query = query.filter(CompanyPolicy.policy_type == policy_type)
        
        chunks = query.all()
        
        # Calculate similarities
        similarities = []
        for chunk, policy in chunks:
            if not chunk.embedding:
                continue
            
            chunk_embedding = json.loads(chunk.embedding)
            similarity = self._cosine_similarity(query_embedding, chunk_embedding)
            
            similarities.append({
                "chunk_id": chunk.id,
                "policy_id": policy.id,
                "policy_name": policy.filename,
                "content": chunk.content,
                "section_title": chunk.section_title,
                "similarity": similarity
            })
        
        # Sort by similarity and return top k
        similarities.sort(key=lambda x: x["similarity"], reverse=True)
        return similarities[:top_k]
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def check_policy_compliance(
        self,
        leave_request: Dict,
        user_context: Dict
    ) -> Dict:
        """Check if leave request complies with company policy"""
        
        leave_type = leave_request.get('leave_type', 'LEAVE')
        
        # Build SPECIFIC query for the leave type being requested
        # CRITICAL: Only retrieve policies relevant to THIS leave type
        specific_query = f"{leave_type} leave policy requirements notice period duration approval"
        
        # Retrieve ONLY policies relevant to this specific leave type
        relevant_policies = self.retrieve_relevant_policies(
            query=specific_query,
            top_k=3,
            policy_type="LEAVE"
        )
        
        # Filter to only include chunks that mention the specific leave type
        filtered_policies = []
        for policy in relevant_policies:
            content_lower = policy['content'].lower()
            leave_type_lower = leave_type.lower()
            
            # Only include if policy explicitly mentions this leave type
            if leave_type_lower in content_lower:
                filtered_policies.append(policy)
        
        if not filtered_policies:
            # If no specific policies found, return compliant with warning
            return {
                "compliant": True,
                "violations": [],
                "warnings": ["No specific policy found for this leave type"],
                "relevant_policies": relevant_policies[:2]
            }
        
        # Use AI to analyze compliance with ONLY the relevant policies
        analysis = self._analyze_compliance_with_ai(
            leave_request,
            filtered_policies,
            user_context
        )
        
        return {
            "compliant": analysis.get("compliant", True),
            "violations": analysis.get("violations", []),
            "warnings": analysis.get("warnings", []),
            "relevant_policies": filtered_policies[:2]
        }
    
    def _analyze_compliance_with_ai(
        self,
        leave_request: Dict,
        policies: List[Dict],
        user_context: Dict
    ) -> Dict:
        """Use AI to analyze if leave request violates policies"""
        
        if not policies:
            return {"violations": [], "warnings": [], "compliant": True}
        
        policy_context = "\n\n".join([
            f"Policy Section:\n{p['content']}"
            for p in policies
        ])
        
        leave_type = leave_request.get('leave_type', 'LEAVE')
        start_date = leave_request.get('start_date')
        end_date = leave_request.get('end_date')
        
        # Calculate duration
        if start_date and end_date:
            if isinstance(start_date, str):
                from datetime import datetime
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            duration = (end_date - start_date).days + 1
        else:
            duration = 1
        
        prompt = f"""You are analyzing a {leave_type} leave request for {duration} day(s) with {leave_request.get('notice_days', 0)} days notice.

CRITICAL LOGIC RULES:
1. Duration-based rules: "X required for 3+ days" only applies if duration >= 3
2. Notice period rules: ALWAYS check - these apply regardless of duration
3. A VIOLATION means the request should be REJECTED/BLOCKED

CURRENT REQUEST:
- Type: {leave_type}
- Duration: {duration} day(s)
- Notice provided: {leave_request.get('notice_days', 0)} days
- Start: {leave_request.get('start_date')}
- End: {leave_request.get('end_date')}
- Reason: {leave_request.get('reason', 'Not provided')}

POLICIES:
{policy_context}

STEP-BY-STEP ANALYSIS FOR {leave_type.upper()} LEAVE:

{"Step 1: Check notice period for SICK leave" if leave_type.upper() == "SICK" else ""}
{"- Policy: Same-day notification acceptable" if leave_type.upper() == "SICK" else ""}
{"- Provided: " + str(leave_request.get('notice_days', 0)) + " days" if leave_type.upper() == "SICK" else ""}
{"- Violation? NO - same-day is acceptable" if leave_type.upper() == "SICK" else ""}

{"Step 1: Check notice period for CASUAL leave" if leave_type.upper() == "CASUAL" else ""}
{"- Policy: Minimum 24 hours (1 day) advance notice required" if leave_type.upper() == "CASUAL" else ""}
{"- Provided: " + str(leave_request.get('notice_days', 0)) + " days" if leave_type.upper() == "CASUAL" else ""}
{"- Violation? " + ("YES - requires 1 day minimum" if leave_type.upper() == "CASUAL" and leave_request.get('notice_days', 0) < 1 else "NO - meets requirement") if leave_type.upper() == "CASUAL" else ""}

{"Step 1: Check notice period for ANNUAL leave" if leave_type.upper() == "ANNUAL" else ""}
{"- Policy: Minimum 7 days advance notice required" if leave_type.upper() == "ANNUAL" else ""}
{"- Provided: " + str(leave_request.get('notice_days', 0)) + " days" if leave_type.upper() == "ANNUAL" else ""}
{"- Violation? " + ("YES - requires 7 days minimum (provided: " + str(leave_request.get('notice_days', 0)) + ")" if leave_type.upper() == "ANNUAL" and leave_request.get('notice_days', 0) < 7 else "NO - meets requirement") if leave_type.upper() == "ANNUAL" else ""}

{"Step 2: Check extended leave notice for ANNUAL leave" if leave_type.upper() == "ANNUAL" and duration > 5 else ""}
{"- Policy: 14 days notice for 5+ consecutive days" if leave_type.upper() == "ANNUAL" and duration > 5 else ""}
{"- Duration: " + str(duration) + " days, Notice: " + str(leave_request.get('notice_days', 0)) + " days" if leave_type.upper() == "ANNUAL" and duration > 5 else ""}
{"- Violation? " + ("YES - requires 14 days for 5+ day leave" if duration > 5 and leave_request.get('notice_days', 0) < 14 else "NO") if leave_type.upper() == "ANNUAL" and duration > 5 else ""}

{"Step 2: Check medical certificate requirement" if leave_type.upper() == "SICK" else ""}
{"- Policy: Medical certificate required for 3+ consecutive days" if leave_type.upper() == "SICK" else ""}
{"- Duration: " + str(duration) + " days" if leave_type.upper() == "SICK" else ""}
{"- Applies? " + ("YES - duration >= 3" if duration >= 3 else "NO - duration < 3, NOT required") if leave_type.upper() == "SICK" else ""}
{"- Violation? " + ("Check if certificate provided" if duration >= 3 else "NO - certificate not required for " + str(duration) + " day leave") if leave_type.upper() == "SICK" else ""}

FINAL DECISION:
Return JSON format:
{{
    "violations": ["List ONLY rules that are VIOLATED and would BLOCK approval"],
    "warnings": ["Minor suggestions or informational notes"],
    "compliant": true/false
}}

EXAMPLES:
- SICK leave, 1 day, 0 days notice → {{"violations": [], "compliant": true}} (same-day OK, no cert needed)
- ANNUAL leave, 1 day, 1 day notice → {{"violations": ["Annual leave requires minimum 7 days' notice (provided: 1 day)"], "compliant": false}}
- ANNUAL leave, 1 day, 10 days notice → {{"violations": [], "compliant": true}}
- CASUAL leave, 2 days, 0 days notice → {{"violations": ["Casual leave requires minimum 24 hours' notice"], "compliant": false}}"""

        try:
            response = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.embedding_service.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "llama-3.1-8b-instant",
                    "messages": [
                        {
                            "role": "system", 
                            "content": f"You are a policy compliance analyzer. Analyze {leave_type} leave rules ONLY. A violation means the request CANNOT be approved. If a requirement doesn't apply to this specific request (e.g., 3+ day rule for 1-day leave), that is COMPLIANT, not a violation."
                        },
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "max_tokens": 300,
                    "response_format": {"type": "json_object"}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result["choices"][0]["message"]["content"]
                analysis = json.loads(content)
                
                # Enhanced post-processing: Remove false positives
                if analysis.get("violations"):
                    filtered_violations = []
                    for v in analysis["violations"]:
                        v_lower = v.lower()
                        
                        # IMMEDIATE CHECK: If violation mentions "3+ days" or similar but duration < 3, SKIP IT
                        if duration < 3:
                            day_threshold_patterns = ["3+", "3 or more", "three or more", "3+ days", "3+ consecutive"]
                            if any(pattern in v_lower for pattern in day_threshold_patterns):
                                # This is definitely a false positive - skip it entirely
                                continue
                        
                        # Skip if it mentions other leave types
                        other_types = []
                        if leave_type.lower() == "sick":
                            other_types = ["casual leave", "annual leave", "maternity", "paternity"]
                        elif leave_type.lower() == "casual":
                            other_types = ["sick leave", "annual leave", "maternity", "paternity"]
                        elif leave_type.lower() == "annual":
                            other_types = ["sick leave", "casual leave", "maternity", "paternity"]
                        
                        if any(other_type in v_lower for other_type in other_types):
                            continue
                        
                        # CRITICAL: Detect false positive patterns for inapplicable requirements
                        false_positive_patterns = [
                            # Certificate-related false positives (pattern, condition)
                            ("certificate required for 3+", duration < 3),
                            ("certificate for 3+ consecutive days", duration < 3),
                            ("medical certificate required for 3+", duration < 3),
                            ("certificate needed for 3 or more", duration < 3),
                            ("required for 3+ days", duration < 3),
                            ("certificate required for leave duration of 3+", duration < 3),
                            ("required for leave duration of 3+", duration < 3),
                            
                            # Catch any mention of "3+ days" when duration < 3
                            ("3+ days", duration < 3),
                            ("three or more days", duration < 3),
                            ("3 or more days", duration < 3),
                            
                            # Statements of what IS allowed/acceptable
                            "no medical certificate is required",
                            "not required",
                            "same-day notification is acceptable",
                            "is acceptable",
                            "is allowed",
                            "within allowed",
                            "does not require",
                            "no certificate needed",
                            "certificate not mandatory",
                            "no documentation required",
                        ]
                        
                        is_false_positive = False
                        for pattern in false_positive_patterns:
                            if isinstance(pattern, tuple):
                                phrase, condition = pattern
                                if phrase in v_lower and condition:
                                    is_false_positive = True
                                    break
                            elif isinstance(pattern, str) and pattern in v_lower:
                                is_false_positive = True
                                break
                        
                        if is_false_positive:
                            # Move informational items to warnings if relevant
                            if "certificate" in v_lower and duration >= 3:
                                if "warnings" not in analysis:
                                    analysis["warnings"] = []
                                analysis["warnings"].append(
                                    f"Medical certificate may be required for {duration} days of leave"
                                )
                            continue
                        
                        # This is a real violation
                        filtered_violations.append(v)
                    
                    analysis["violations"] = filtered_violations
                    analysis["compliant"] = len(filtered_violations) == 0
                
                return analysis
            else:
                print(f"Groq API error: {response.status_code} - {response.text}")
            
        except Exception as e:
            print(f"AI compliance check failed: {e}")
        
        # Fallback: Apply basic rule-based checking
        return self._rule_based_compliance_check(leave_request, policies, user_context)
    
    def _rule_based_compliance_check(
        self,
        leave_request: Dict,
        policies: List[Dict],
        user_context: Dict
    ) -> Dict:
        """Fallback rule-based compliance checking"""
        
        violations = []
        warnings = []
        
        leave_type = leave_request.get('leave_type', '').upper()
        notice_days = leave_request.get('notice_days', 0)
        
        # Combine all policy content
        policy_text = " ".join([p['content'] for p in policies]).lower()
        
        # Extract duration
        start_date = leave_request.get('start_date')
        end_date = leave_request.get('end_date')
        if start_date and end_date:
            if isinstance(start_date, str):
                from datetime import datetime
                start_date = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date = datetime.strptime(end_date, "%Y-%m-%d").date()
            duration = (end_date - start_date).days + 1
        else:
            duration = 1
        
        # SICK LEAVE RULES
        if leave_type == "SICK":
            # Same-day notification is acceptable for sick leave - NO VIOLATION
            if "same-day notification acceptable" in policy_text or "same-day notification is acceptable" in policy_text:
                # This is compliant - no action needed
                pass
            
            # Medical certificate only for 3+ days
            if duration >= 3:
                if "medical certificate required for 3+" in policy_text or "certificate for 3+ sick days" in policy_text or "certificate required for 3 or more" in policy_text:
                    reason_text = leave_request.get('reason', '').lower()
                    if not reason_text or ('certificate' not in reason_text and 'doctor' not in reason_text):
                        warnings.append("Medical certificate may be required for 3+ consecutive sick days (please provide if available)")
        
        # CASUAL LEAVE RULES
        elif leave_type == "CASUAL":
            # Check for 24 hours / 1 day notice requirement
            if "24 hours' notice required" in policy_text or "minimum 24 hours" in policy_text or "24 hours advance notice" in policy_text:
                if notice_days < 1:
                    # Check if emergency clause exists
                    if "emergency" in policy_text and "approval" in policy_text:
                        warnings.append("Casual leave typically requires 24 hours' notice. This will be treated as an emergency request requiring manager approval.")
                    else:
                        violations.append("Casual leave requires minimum 24 hours' advance notice")
        
        # ANNUAL LEAVE RULES
        elif leave_type == "ANNUAL":
            # Check 7 days minimum notice
            if "7 days' notice minimum" in policy_text or "minimum 7 days advance notice" in policy_text or "7 days advance notice" in policy_text:
                if notice_days < 7:
                    violations.append(f"Annual leave requires minimum 7 days' advance notice (provided: {notice_days} days)")
            
            # Check extended leave notice (14 days for 5+ days)
            if duration > 5:
                if "14 days' notice for 5+ day leave" in policy_text or "14 days notice required for leaves exceeding 5" in policy_text:
                    if notice_days < 14:
                        violations.append(f"Annual leave of 5+ consecutive days requires 14 days' advance notice (provided: {notice_days} days)")
        
        return {
            "violations": violations,
            "warnings": warnings,
            "compliant": len(violations) == 0
        }