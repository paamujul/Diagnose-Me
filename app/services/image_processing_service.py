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
