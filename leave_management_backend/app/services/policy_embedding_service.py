import requests
from typing import List
import numpy as np

class PolicyEmbeddingService:
    """Generate embeddings for policy chunks using Groq"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.model = "llama-3.1-8b-instant"
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
    
    def generate_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using Groq's completion API
        Note: This is a workaround since Groq doesn't have native embeddings API
        We'll use text similarity through completions"""
        
        # For production, consider using OpenAI embeddings or a dedicated embedding model
        # This is a simplified approach using text analysis
        
        try:
            response = requests.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": self.model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Extract key semantic features from this policy text as a list of important keywords and concepts."
                        },
                        {
                            "role": "user",
                            "content": text[:1000]  # Limit to first 1000 chars
                        }
                    ],
                    "temperature": 0.1
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                keywords = result["choices"][0]["message"]["content"]
                
                # Create a simple embedding based on text characteristics
                # In production, use proper embedding models
                embedding = self._create_simple_embedding(text, keywords)
                return embedding
            
            return self._create_simple_embedding(text)
            
        except Exception as e:
            print(f"Embedding generation failed: {e}")
            return self._create_simple_embedding(text)
    
    def _create_simple_embedding(self, text: str, keywords: str = "") -> List[float]:
        """Create a simple embedding based on text characteristics"""
        # This is a placeholder - in production use proper embeddings
        # Consider using sentence-transformers or OpenAI embeddings
        
        features = []
        
        # Basic text statistics (384 dimensions)
        features.extend([
            len(text),
            text.count(' '),
            text.count('.'),
            text.count('leave'),
            text.count('days'),
            text.count('annual'),
            text.count('sick'),
            text.count('approval'),
            text.count('manager'),
            text.count('notice')
        ])
        
        # Pad to 384 dimensions (common embedding size)
        while len(features) < 384:
            features.append(0.0)
        
        # Normalize
        features = np.array(features[:384])
        norm = np.linalg.norm(features)
        if norm > 0:
            features = features / norm
        
        return features.tolist()
    
    def batch_generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        return [self.generate_embedding(text) for text in texts]