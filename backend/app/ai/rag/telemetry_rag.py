import numpy as np
from scipy.spatial.distance import cosine
import json
import os
import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class SimpleVectorStore:
    """
    Lightweight vector store using cosine similarity.
    Stores embeddings in-memory with disk persistence.
    """
    
    def __init__(self, persist_path: str = './data/rag/telemetry_store.json'):
        self.persist_path = persist_path
        self.embeddings = []  # List of [embedding_vector]
        self.metadata = []   # List of metadata dicts
        self._load()
    
    def _load(self):
        """Load vector store from disk if exists."""
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                    
                # Convert embeddings to numpy arrays
                self.embeddings = [np.array(emb) for emb in data['embeddings']]
                self.metadata = data['metadata']
                
                logger.info(f"Loaded {len(self.embeddings)} vectors from {self.persist_path}")
            except Exception as e:
                logger.error(f"Failed to load vector store: {e}")
                self.embeddings = []
                self.metadata = []

    def _save(self):
        """Persist vector store to disk."""
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
            
            # Convert numpy arrays to lists for JSON serialization
            data = {
                'embeddings': [emb.tolist() for emb in self.embeddings],
                'metadata': self.metadata
            }
            
            with open(self.persist_path, 'w') as f:
                json.dump(data, f)
                
            logger.info(f"Saved {len(self.embeddings)} vectors to {self.persist_path}")
        except Exception as e:
            logger.error(f"Failed to save vector store: {e}")

    def add(self, embedding: List[float], metadata: Dict[str, Any]):
        """
        Add a new embedding to the store.
        
        Args:
            embedding: Vector embedding (list of floats)
            metadata: Associated metadata (e.g., {"lap": 24, "driver": "VER"})
        """
        self.embeddings.append(np.array(embedding))
        self.metadata.append(metadata)
        self._save()
    
    def retrieve(self, query_embedding: List[float], n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve the top-n most similar vectors.
        
        Args:
            query_embedding: Query vector
            n_results: Number of results to return
        
        Returns:
            List of metadata dicts for most similar vectors
        """
        if not self.embeddings:
            return []
        
        # Convert query to numpy array
        query = np.array(query_embedding)
        
        # Calculate cosine similarity for all vectors
        similarities = [
            (1 - cosine(query, emb), meta) 
            for emb, meta in zip(self.embeddings, self.metadata)
        ]
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[0], reverse=True)
        
        # Return top-n metadata
        return [{
            'similarity': float(sim),
            'document': f"Lap {meta.get('lap', '?')} - {meta.get('driver', 'Unknown')}: {meta.get('description', 'No description')}",
            'metadata': meta
        } for sim, meta in similarities[:n_results]]


class TelemetryRAG:
    """
    Telemetry RAG system using SimpleVectorStore.
    
    Provides retrieval of relevant telemetry evidence for AI queries.
    """
    
    def __init__(self):
        self.vector_store = SimpleVectorStore()
        
        # Initialize with sample telemetry data if empty
        if len(self.vector_store.embeddings) == 0:
            self._initialize_sample_data()
    
    def _initialize_sample_data(self):
        """Add sample telemetry data for demonstration."""
        sample_data = [
            {
                'embedding': [0.1, 0.2, 0.3, 0.4, 0.5],
                'metadata': {
                    'lap': 24,
                    'driver': 'VER',
                    'session': 'race',
                    'circuit': 'Hungaroring',
                    'description': 'Safety Car deployment on Lap 24'
                }
            },
            {
                'embedding': [0.5, 0.4, 0.3, 0.2, 0.1],
                'metadata': {
                    'lap': 18,
                    'driver': 'NOR',
                    'session': 'race',
                    'circuit': 'Hungaroring',
                    'description': 'Undercut opportunity on Lap 18'
                }
            },
            {
                'embedding': [0.2, 0.3, 0.5, 0.4, 0.1],
                'metadata': {
                    'lap': 32,
                    'driver': 'LEC',
                    'session': 'race',
                    'circuit': 'Hungaroring',
                    'description': 'Rain probability increase on Lap 32'
                }
            }
        ]
        
        for item in sample_data:
            self.vector_store.add(item['embedding'], item['metadata'])
    
    def retrieve(self, query: str, n_results: int = 3) -> List[Dict[str, Any]]:
        """
        Retrieve relevant telemetry evidence for a query.
        
        Args:
            query: Natural language query
            n_results: Number of results to return
        
        Returns:
            List of retrieved evidence with similarity scores
        """
        # In a real implementation, this would use an embedding model
        # For demo purposes, we'll use a simple heuristic
        query_embedding = self._get_query_embedding(query)
        return self.vector_store.retrieve(query_embedding, n_results)
    
    def _get_query_embedding(self, query: str) -> List[float]:
        """
        Convert query to embedding (simplified for demo).
        In production, use a real embedding model.
        """
        # Simplified embedding generation (in real system, use sentence-transformers)
        query_lower = query.lower()
        
        if 'safety car' in query_lower:
            return [0.1, 0.2, 0.3, 0.4, 0.5]  # Matches Safety Car sample
        elif 'undercut' in query_lower:
            return [0.5, 0.4, 0.3, 0.2, 0.1]  # Matches Undercut sample
        elif 'rain' in query_lower:
            return [0.2, 0.3, 0.5, 0.4, 0.1]  # Matches Rain sample
        else:
            # Default embedding (uniform)
            return [0.3, 0.3, 0.3, 0.3, 0.3]