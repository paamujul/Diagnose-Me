from typing import List, Dict, Optional
from sqlalchemy.orm import Session
from app.models.database_models import Medication, Prescription, Patient
from app.models.graph_models import DrugInteractionGraph
from datetime import datetime


class MedicationService:
    """Medication recommendation and interaction checking service"""

    def __init__(self):
        self.interaction_graph = DrugInteractionGraph()

    def get_patient_prescriptions(
        self, db: Session, patient_id: int, active_only: bool = True
    ) -> List[Prescription]:
        """Get patient's current prescriptions"""

        query = db.query(Prescription).filter(Prescription.patient_id == patient_id)

        if active_only:
            query = query.filter(Prescription.active == 1)

        return query.all()

    def check_medication_compatibility(
        self, db: Session, patient_id: int, new_medication_name: str
    ) -> Dict:
        """Check if new medication is compatible with existing prescriptions"""

        # Get patient's current medications
        prescriptions = self.get_patient_prescriptions(db, patient_id)
        current_meds = [
            db.query(Medication).filter(Medication.id == p.medication_id).first().name
            for p in prescriptions
        ]

        # Check for interactions
        all_meds = current_meds + [new_medication_name]
        interactions = self.interaction_graph.check_interactions(all_meds)

        # Filter for interactions involving the new medication
        relevant_interactions = [
            i for i in interactions if new_medication_name in [i["drug1"], i["drug2"]]
        ]

        is_safe = len(relevant_interactions) == 0

        return {
            "new_medication": new_medication_name,
            "is_compatible": is_safe,
            "interactions_found": len(relevant_interactions),
            "interactions": relevant_interactions,
            "current_medications": current_meds,
            "recommendation": self._generate_compatibility_recommendation(
                is_safe, relevant_interactions
            ),
        }

    def _generate_compatibility_recommendation(
        self, is_safe: bool, interactions: List[Dict]
    ) -> str:
        """Generate recommendation based on compatibility check"""

        if is_safe:
            return "No known interactions detected. Medication appears compatible."

        major_interactions = [i for i in interactions if i["severity"] == "major"]
        moderate_interactions = [i for i in interactions if i["severity"] == "moderate"]

        if major_interactions:
            return (
                "⚠️ MAJOR INTERACTIONS DETECTED. Do not prescribe without consultation."
            )
        elif moderate_interactions:
            return "⚠️ Moderate interactions found. Monitor patient closely and consider alternatives."
        else:
            return "Minor interactions present. Adjust dosage or timing as needed."

    def get_safe_alternatives(
        self, db: Session, patient_id: int, medication_category: str
    ) -> List[str]:
        """Find safe medication alternatives for a patient"""

        # Get patient's current medications
        prescriptions = self.get_patient_prescriptions(db, patient_id)
        current_meds = [
            db.query(Medication).filter(Medication.id == p.medication_id).first().name
            for p in prescriptions
        ]

        # Get medications in the requested category
        category_meds = (
            db.query(Medication)
            .filter(Medication.category == medication_category)
            .all()
        )

        # Find alternatives with no interactions
        safe_alternatives = []
        for med in category_meds:
            if med.name not in current_meds:
                interactions = self.interaction_graph.check_interactions(
                    current_meds + [med.name]
                )
                if not interactions:
                    safe_alternatives.append(med.name)

        return safe_alternatives

    def recommend_otc_medications(
        self, db: Session, patient_id: int, symptoms: List[str]
    ) -> Dict:
        """Recommend OTC medications based on symptoms"""

        # Symptom to medication mapping
        symptom_medication_map = {
            "headache": ["Acetaminophen", "Ibuprofen"],
            "fever": ["Acetaminophen", "Ibuprofen"],
            "cough": ["Dextromethorphan"],
            "runny_nose": ["Pseudoephedrine"],
            "sore_throat": ["Acetaminophen", "Ibuprofen"],
            "nausea": ["Bismuth subsalicylate"],
            "diarrhea": ["Loperamide"],
            "allergies": ["Cetirizine", "Loratadine"],
        }

        # Get recommended medications based on symptoms
        recommended = set()
        for symptom in symptoms:
            if symptom in symptom_medication_map:
                recommended.update(symptom_medication_map[symptom])

        # Check compatibility with existing prescriptions
        safe_recommendations = []
        warnings = []

        for med_name in recommended:
            compatibility = self.check_medication_compatibility(
                db, patient_id, med_name
            )

            if compatibility["is_compatible"]:
                safe_recommendations.append(
                    {"medication": med_name, "status": "safe", "interactions": []}
                )
            else:
                warnings.append(
                    {
                        "medication": med_name,
                        "status": "warning",
                        "interactions": compatibility["interactions"],
                    }
                )

        return {
            "symptoms": symptoms,
            "safe_otc_recommendations": safe_recommendations,
            "medications_with_warnings": warnings,
            "total_checked": len(recommended),
            "safe_count": len(safe_recommendations),
        }

    def prescribe_medication(
        self,
        db: Session,
        patient_id: int,
        medication_name: str,
        dosage: str,
        frequency: str,
        duration: str,
    ) -> Optional[Prescription]:
        """Create new prescription after safety checks"""

        # Check compatibility first
        compatibility = self.check_medication_compatibility(
            db, patient_id, medication_name
        )

        if not compatibility["is_compatible"]:
            major_interactions = [
                i for i in compatibility["interactions"] if i["severity"] == "major"
            ]
            if major_interactions:
                return None  # Cannot prescribe due to major interaction

        # Get or create medication
        medication = (
            db.query(Medication).filter(Medication.name == medication_name).first()
        )

        if not medication:
            return None

        # Create prescription
        prescription = Prescription(
            patient_id=patient_id,
            medication_id=medication.id,
            dosage=dosage,
            frequency=frequency,
            duration=duration,
            prescribed_date=datetime.utcnow(),
            active=1,
        )

        db.add(prescription)
        db.commit()
        db.refresh(prescription)

        return prescription
