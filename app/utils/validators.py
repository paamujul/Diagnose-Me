import re
from typing import List


def validate_symptom_name(symptom: str) -> bool:
    """Validate symptom name format"""
    # Should be lowercase with underscores
    pattern = r"^[a-z][a-z0-9_]*"
