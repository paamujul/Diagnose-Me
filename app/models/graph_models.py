import networkx as nx
import json
from typing import List, Dict, Set, Tuple
from pathlib import Path


class SymptomDiseaseGraph:
    """Graph-theoretic model for symptom-disease relationships (200+ nodes)"""

    def __init__(self, data_path: str = None):
        self.graph = nx.DiGraph()
        self.symptom_nodes = set()
        self.disease_nodes = set()

        if data_path and Path(data_path).exists():
            self.load_from_file(data_path)
        else:
            self._initialize_sample_data()

    def _initialize_sample_data(self):
        """Initialize with sample symptom-disease relationships"""
        # Sample diseases with their symptoms and probabilities
        disease_symptoms = {
            "Common Cold": [
                ("runny_nose", 0.9),
                ("sore_throat", 0.8),
                ("cough", 0.7),
                ("fatigue", 0.6),
                ("mild_fever", 0.5),
            ]
        }
