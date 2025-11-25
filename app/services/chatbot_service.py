import re
import json
from typing import List, Dict, Union
from openai import AzureOpenAI
from app.config import get_settings
from app.models.graph_models import SymptomDiseaseGraph

settings = get_settings()


class ChatbotService:
    """Multi-LLM chatbot for symptom assessment using Azure OpenAI"""

    def __init__(self):
        self.client = AzureOpenAI(
            api_key=settings.AZURE_OPENAI_KEY,
            api_version=settings.AZURE_OPENAI_VERSION,
            azure_endpoint=settings.AZURE_OPENAI_ENDPOINT,
        )
        self.deployment = settings.AZURE_OPENAI_DEPLOYMENT
        # Assuming SymptomDiseaseGraph is defined elsewhere in your project
        self.symptom_graph = SymptomDiseaseGraph()

        self.system_prompt = """You are a medical assessment AI assistant. Your role is to:
1. Ask relevant questions about patient symptoms
2. Gather detailed information about symptom duration, severity, and context
3. Be empathetic and professional
4. Never provide definitive diagnoses - only gather information
5. Ask one question at a time
6. Use the symptom information to guide your questions

Format your responses as a raw JSON object (no markdown formatting) with this structure:
{
    "message": "Your question or response to the patient",
    "extracted_symptoms": ["symptom1", "symptom2"],
    "needs_more_info": true,
    "suggested_next_questions": ["question1", "question2"]
}
"""

    def _clean_json_string(self, json_string: str) -> str:
        """Helper to strip markdown code blocks if the LLM includes them"""
        cleaned = json_string.strip()
        if cleaned.startswith("```"):
            # Remove opening ```json or just ```
            cleaned = re.sub(r"^```\w*\s*", "", cleaned)
            # Remove closing ```
            cleaned = re.sub(r"\s*```$", "", cleaned)
        return cleaned

    def process_message(
        self,
        user_message: str,
        conversation_history: List[Dict],
        current_symptoms: List[str],
    ) -> Dict:
        """Process user message and generate response"""

        # Get relevant symptom suggestions from graph
        suggested_symptoms = self.symptom_graph.suggest_next_questions(current_symptoms)

        # Build context for the LLM
        context = f"""
Current symptoms identified: {", ".join(current_symptoms) if current_symptoms else "None yet"}
Suggested areas to explore: {", ".join(suggested_symptoms[:3])}
"""

        # Prepare messages for Azure OpenAI
        messages = [
            {"role": "system", "content": self.system_prompt},
            {"role": "system", "content": context},
        ]

        # Add conversation history (ensure format is correct)
        for msg in conversation_history[-10:]:  # Keep last 10 messages
            messages.append(msg)

        # Add current user message
        messages.append({"role": "user", "content": user_message})

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=messages,
                temperature=0.7,
                max_tokens=500,
            )

            assistant_message = response.choices[0].message.content
            cleaned_message = self._clean_json_string(assistant_message)

            # Try to parse JSON response
            try:
                parsed_response = json.loads(cleaned_message)
            except json.JSONDecodeError:
                # If not JSON, wrap in standard format
                parsed_response = {
                    "message": assistant_message,
                    "extracted_symptoms": [],
                    "needs_more_info": True,
                    "suggested_next_questions": [],
                }

            return parsed_response

        except Exception as e:
            return {
                "message": "I apologize, but I'm having trouble processing your message. Could you please rephrase?",
                "extracted_symptoms": [],
                "needs_more_info": True,
                "suggested_next_questions": [],
                "error": str(e),
            }

    def extract_symptoms_from_text(
        self, text: str, known_symptoms: List[str]
    ) -> List[str]:
        """Use LLM to extract symptoms from free text"""

        prompt = f"""Extract medical symptoms from this text: "{text}"

Known symptoms in our system: {", ".join(known_symptoms[:50])}

Return ONLY a JSON array of symptom identifiers found, using snake_case format.
Example: ["headache", "fever", "sore_throat"]

If no symptoms found, return empty array: []
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200,
            )

            result = response.choices[0].message.content.strip()
            cleaned_result = self._clean_json_string(result)
            symptoms = json.loads(cleaned_result)

            return symptoms if isinstance(symptoms, list) else []

        except Exception:
            return []

    def generate_followup_questions(
        self, symptoms: List[str], conversation_history: List[Dict]
    ) -> List[str]:
        """Generate intelligent follow-up questions based on symptoms"""

        # Get graph-based suggestions (unused in prompt currently, but kept for consistency)
        # graph_suggestions = self.symptom_graph.suggest_next_questions(symptoms)

        prompt = f"""Based on these symptoms: {", ".join(symptoms)}

Generate 3 specific follow-up questions to better assess the patient's condition.
Focus on: severity, duration, triggers, associated symptoms, and impact on daily life.

Return as a JSON array of strings.
"""

        try:
            response = self.client.chat.completions.create(
                model=self.deployment,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.8,
                max_tokens=300,
            )

            result = response.choices[0].message.content.strip()
            cleaned_result = self._clean_json_string(result)
            questions = json.loads(cleaned_result)

            return questions if isinstance(questions, list) else []

        except Exception:
            # Fallback to template questions
            return [
                f"How long have you been experiencing {symptoms[0] if symptoms else 'these symptoms'}?",
                "On a scale of 1-10, how severe is the discomfort?",
                "Have you noticed anything that makes it better or worse?",
            ]


def validate_medication(medication: str) -> bool:
    """
    Validate medication name format.
    Allowing alphanumeric, spaces, dashes, and standard punctuation.
    """
    if not medication:
        return False
    # Example pattern: Allow letters, numbers, spaces, hyphens, parens
    pattern = r"^[a-zA-Z0-9\s\-\(\)\.]+$"
    return bool(re.match(pattern, medication))


def normalize_symptom(symptom: str) -> str:
    """Normalize symptom to standard format"""
    if not symptom:
        return ""
    # Convert to lowercase and replace spaces with underscores
    normalized = symptom.lower().strip()
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^a-z0-9_]", "", normalized)
    return normalized


def validate_age(age: int) -> bool:
    """Validate patient age"""
    return 0 <= age <= 120


def validate_confidence_score(score: float) -> bool:
    """Validate confidence score range"""
    return 0.0 <= score <= 1.0
