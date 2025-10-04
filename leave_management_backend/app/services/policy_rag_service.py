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
        
        # Build query based on leave request
        query_parts = [
            f"{leave_request.get('leave_type', 'leave')} policy",
            f"notice period {leave_request.get('leave_type', '')}",
            f"maximum duration {leave_request.get('leave_type', '')}",
            f"approval requirements {leave_request.get('leave_type', '')}"
        ]
        violations = []
        warnings = []
        compliant = True
        
        for query in query_parts:
            relevant_policies = self.retrieve_relevant_policies(
                query=query,
                top_k=3,
                policy_type="LEAVE"
            )
            
            if relevant_policies:
                # Use AI to analyze compliance
                analysis = self._analyze_compliance_with_ai(
                    leave_request,
                    relevant_policies,
                    user_context
                )
                
                if analysis.get("violations"):
                    violations.extend(analysis["violations"])
                    compliant = False
                
                if analysis.get("warnings"):
                    warnings.extend(analysis["warnings"])
        
        return {
            "compliant": compliant,
            "violations": violations,
            "warnings": warnings,
            "relevant_policies": self.retrieve_relevant_policies(
                f"{leave_request.get('leave_type', 'leave')} policy overview",
                top_k=2
            )
        }
    
    def _analyze_compliance_with_ai(
        self,
        leave_request: Dict,
        policies: List[Dict],
        user_context: Dict
    ) -> Dict:
        """Use AI to analyze if leave request violates policies"""
        
        policy_context = "\n\n".join([
            f"Policy Section: {p['section_title']}\n{p['content']}"
            for p in policies
        ])
        
        prompt = f"""Analyze if this leave request complies with company policy.

LEAVE REQUEST:
- Type: {leave_request.get('leave_type')}

- Start: {leave_request.get('start_date')}
- End: {leave_request.get('end_date')}
- Reason: {leave_request.get('reason', 'Not provided')}
- Notice: {leave_request.get('notice_days', 0)} days

USER CONTEXT:
- Role: {user_context.get('role')}
- Department: {user_context.get('department')}

COMPANY POLICIES:
{policy_context}

Return JSON with:
{{
    "violations": ["list of policy violations"],
    "warnings": ["list of warnings"],
    "compliant": true/false
}}"""

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
                        {"role": "system", "content": "You are a policy compliance analyzer."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.1,
                    "response_format": {"type": "json_object"}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                return json.loads(result["choices"][0]["message"]["content"])
            
        except Exception as e:
            print(f"AI compliance check failed: {e}")
        
        return {"violations": [], "warnings": [], "compliant": True}