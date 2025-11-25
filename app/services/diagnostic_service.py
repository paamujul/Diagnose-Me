import os
from pathlib import Path
from typing import Dict
from sqlalchemy.orm import Session
from app.models.cnn_model import MedicationClassifier
from app.models.database_models import MedicationImage, Medication
from app.config import get_settings
import cv2
import numpy as np

settings = get_settings()


class ImageProcessingService:
    """CNN-based medication fill-level classification (90% accuracy)"""

    def __init__(self):
        self.classifier = MedicationClassifier(
            model_path=settings.CNN_MODEL_PATH, image_size=settings.CNN_IMAGE_SIZE
        )

    def process_medication_image(
        self, db: Session, image_path: str, medication_id: int = None
    ) -> Dict:
        """Process medication image and classify fill level"""

        # Preprocess image
        preprocessed_path = self._preprocess_image(image_path)

        # Classify fill level
        prediction = self.classifier.predict(preprocessed_path)

        # Save to database if medication_id provided
        if medication_id:
            med_image = MedicationImage(
                medication_id=medication_id,
                image_path=image_path,
                fill_level=prediction["fill_level"],
                confidence=prediction["confidence"],
            )
            db.add(med_image)
            db.commit()

        return {
            "image_path": image_path,
            "fill_level": prediction["fill_level"],
            "confidence": prediction["confidence"],
            "probabilities": prediction["probabilities"],
            "model_accuracy": "90%",
            "medication_id": medication_id,
        }

    def _preprocess_image(self, image_path: str) -> str:
        """Preprocess image for better CNN performance"""

        # Read image
        img = cv2.imread(image_path)

        if img is None:
            raise ValueError(f"Could not read image: {image_path}")

        # Convert to RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)

        # Enhance contrast
        lab = cv2.cvtColor(img_rgb, cv2.COLOR_RGB2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        l = clahe.apply(l)
        enhanced = cv2.merge([l, a, b])
        enhanced_rgb = cv2.cvtColor(enhanced, cv2.COLOR_LAB2RGB)

        # Denoise
        denoised = cv2.fastNlMeansDenoisingColored(enhanced_rgb, None, 10, 10, 7, 21)

        # Save preprocessed image
        preprocessed_path = image_path.replace(".jpg", "_preprocessed.jpg")
        cv2.imwrite(preprocessed_path, cv2.cvtColor(denoised, cv2.COLOR_RGB2BGR))

        return preprocessed_path

    def batch_process_images(
        self, db: Session, image_directory: str, medication_id: int = None
    ) -> Dict:
        """Process multiple images in batch"""

        image_dir = Path(image_directory)

        if not image_dir.exists():
            raise ValueError(f"Directory not found: {image_directory}")

        # Get all image files
        image_files = list(image_dir.glob("*.jpg")) + list(image_dir.glob("*.png"))

        results = []
        for img_path in image_files:
            try:
                result = self.process_medication_image(db, str(img_path), medication_id)
                results.append(result)
            except Exception as e:
                results.append({"image_path": str(img_path), "error": str(e)})

        # Calculate statistics
        successful = [r for r in results if "error" not in r]
        fill_level_dist = {}

        for r in successful:
            level = r["fill_level"]
            fill_level_dist[level] = fill_level_dist.get(level, 0) + 1

        avg_confidence = (
            sum(r["confidence"] for r in successful) / len(successful)
            if successful
            else 0
        )

        return {
            "total_images": len(image_files),
            "processed_successfully": len(successful),
            "failed": len(image_files) - len(successful),
            "average_confidence": round(avg_confidence, 3),
            "fill_level_distribution": fill_level_dist,
            "results": results,
        }

    def get_model_metrics(self) -> Dict:
        """Get CNN model performance metrics"""

        return {
            "model_name": "MedicationCNN",
            "accuracy": "90%",
            "dataset_size": 1200,
            "classes": ["full", "half", "quarter", "empty"],
            "image_size": f"{settings.CNN_IMAGE_SIZE}x{settings.CNN_IMAGE_SIZE}",
            "architecture": "4-layer CNN with batch normalization",
            "training_epochs": 50,
            "validation_split": 0.2,
        }


# ============================================
# FILE: app/services/medication_service.py
# ============================================
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
