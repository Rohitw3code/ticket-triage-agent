import json
import logging
from typing import List, Dict
import numpy as np
from openai import OpenAI
from app.config import get_settings

logger = logging.getLogger(__name__)


class KnowledgeBase:
    def __init__(self):
        settings = get_settings()
        self.kb_path = settings.KB_PATH
        self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        self.embeddings_cache = {}
    
    def load_kb(self) -> List[Dict]:
        try:
            with open(self.kb_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Error loading KB: {e}")
            return []
    
    def search(self, query: str, top_k: int = 3) -> List[Dict]:
        kb_entries = self.load_kb()
        
        query_embedding = self._get_embedding(query)
        
        results = []
        
        for entry in kb_entries:
            entry_text = self._build_entry_text(entry)
            entry_embedding = self._get_embedding(entry_text)
            
            score = self._cosine_similarity(query_embedding, entry_embedding)
            
            results.append({
                'id': entry['id'],
                'title': entry['title'],
                'category': entry['category'],
                'score': score,
                'recommended_action': entry.get('recommended_action', '')
            })
        
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:top_k]
    
    def _build_entry_text(self, entry: Dict) -> str:
        text = entry['title']
        symptoms = entry.get('symptoms', [])
        if symptoms:
            text += ' ' + ' '.join(symptoms)
        return text
    
    def _get_embedding(self, text: str) -> List[float]:
        if text in self.embeddings_cache:
            return self.embeddings_cache[text]
        
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
            embedding = response.data[0].embedding
            self.embeddings_cache[text] = embedding
            return embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            return [0.0] * 1536
    
    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))  