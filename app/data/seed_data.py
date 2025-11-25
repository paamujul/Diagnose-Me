from sqlalchemy.orm import Session
from app.models.database_models import Medication, Patient
import json


def seed_database(db: Session):
    """Seed database with sample medications and test patients"""

    # Sample medications with detailed information
    medications_data = [
        {
            "name": "Aspirin",
            "generic_name": "Acetylsalicylic Acid",
            "category": "NSAID",
            "dosage_forms": ["tablet", "chewable"],
            "side_effects": ["stomach upset", "bleeding", "heartburn"],
            "interactions": ["warfarin", "ibuprofen"],
            "is_otc": 1,
        },
        {
            "name": "Ibuprofen",
            "generic_name": "Ibuprofen",
            "category": "NSAID",
            "dosage_forms": ["tablet", "capsule", "liquid"],
            "side_effects": ["nausea", "dizziness", "heartburn"],
            "interactions": ["aspirin", "warfarin"],
            "is_otc": 1,
        },
        {
            "name": "Acetaminophen",
            "generic_name": "Paracetamol",
            "category": "Analgesic",
            "dosage_forms": ["tablet", "capsule", "liquid", "suppository"],
            "side_effects": ["rare at normal doses", "liver damage at high doses"],
            "interactions": ["warfarin", "alcohol"],
            "is_otc": 1,
        },
        {
            "name": "Lisinopril",
            "generic_name": "Lisinopril",
            "category": "ACE Inhibitor",
            "dosage_forms": ["tablet"],
            "side_effects": ["dizziness", "cough", "hyperkalemia"],
            "interactions": ["potassium", "nsaids"],
            "is_otc": 0,
        },
        {
            "name": "Metformin",
            "generic_name": "Metformin HCl",
            "category": "Antidiabetic",
            "dosage_forms": ["tablet", "extended-release"],
            "side_effects": ["diarrhea", "nausea", "lactic acidosis"],
            "interactions": ["alcohol", "contrast dye"],
            "is_otc": 0,
        },
        {
            "name": "Atorvastatin",
            "generic_name": "Atorvastatin Calcium",
            "category": "Statin",
            "dosage_forms": ["tablet"],
            "side_effects": ["muscle pain", "liver damage", "diabetes risk"],
            "interactions": ["grapefruit", "gemfibrozil"],
            "is_otc": 0,
        },
        {
            "name": "Omeprazole",
            "generic_name": "Omeprazole",
            "category": "Proton Pump Inhibitor",
            "dosage_forms": ["capsule", "tablet"],
            "side_effects": ["headache", "diarrhea", "bone fracture risk"],
            "interactions": ["clopidogrel", "warfarin"],
            "is_otc": 1,
        },
        {
            "name": "Levothyroxine",
            "generic_name": "Levothyroxine Sodium",
            "category": "Thyroid Hormone",
            "dosage_forms": ["tablet"],
            "side_effects": ["palpitations", "weight loss", "insomnia"],
            "interactions": ["calcium", "iron", "antacids"],
            "is_otc": 0,
        },
        {
            "name": "Amlodipine",
            "generic_name": "Amlodipine Besylate",
            "category": "Calcium Channel Blocker",
            "dosage_forms": ["tablet"],
            "side_effects": ["swelling", "dizziness", "flushing"],
            "interactions": ["simvastatin", "grapefruit"],
            "is_otc": 0,
        },
        {
            "name": "Metoprolol",
            "generic_name": "Metoprolol Tartrate",
            "category": "Beta Blocker",
            "dosage_forms": ["tablet", "extended-release"],
            "side_effects": ["fatigue", "dizziness", "bradycardia"],
            "interactions": ["calcium channel blockers", "clonidine"],
            "is_otc": 0,
        },
        {
            "name": "Losartan",
            "generic_name": "Losartan Potassium",
            "category": "ARB",
            "dosage_forms": ["tablet"],
            "side_effects": ["dizziness", "hyperkalemia", "fatigue"],
            "interactions": ["potassium", "nsaids"],
            "is_otc": 0,
        },
        {
            "name": "Simvastatin",
            "generic_name": "Simvastatin",
            "category": "Statin",
            "dosage_forms": ["tablet"],
            "side_effects": ["muscle pain", "liver damage"],
            "interactions": ["amlodipine", "grapefruit", "gemfibrozil"],
            "is_otc": 0,
        },
        {
            "name": "Warfarin",
            "generic_name": "Warfarin Sodium",
            "category": "Anticoagulant",
            "dosage_forms": ["tablet"],
            "side_effects": ["bleeding", "bruising"],
            "interactions": ["aspirin", "nsaids", "antibiotics", "vitamin k"],
            "is_otc": 0,
        },
        {
            "name": "Clopidogrel",
            "generic_name": "Clopidogrel Bisulfate",
            "category": "Antiplatelet",
            "dosage_forms": ["tablet"],
            "side_effects": ["bleeding", "bruising", "rash"],
            "interactions": ["omeprazole", "aspirin"],
            "is_otc": 0,
        },
        {
            "name": "Gabapentin",
            "generic_name": "Gabapentin",
            "category": "Anticonvulsant",
            "dosage_forms": ["capsule", "tablet"],
            "side_effects": ["dizziness", "drowsiness", "weight gain"],
            "interactions": ["antacids", "opioids"],
            "is_otc": 0,
        },
        {
            "name": "Sertraline",
            "generic_name": "Sertraline HCl",
            "category": "SSRI",
            "dosage_forms": ["tablet", "oral solution"],
            "side_effects": ["nausea", "insomnia", "sexual dysfunction"],
            "interactions": ["maois", "nsaids", "warfarin"],
            "is_otc": 0,
        },
        {
            "name": "Fluoxetine",
            "generic_name": "Fluoxetine HCl",
            "category": "SSRI",
            "dosage_forms": ["capsule", "tablet", "solution"],
            "side_effects": ["nausea", "insomnia", "anxiety"],
            "interactions": ["maois", "warfarin", "nsaids"],
            "is_otc": 0,
        },
        {
            "name": "Prednisone",
            "generic_name": "Prednisone",
            "category": "Corticosteroid",
            "dosage_forms": ["tablet", "solution"],
            "side_effects": ["weight gain", "mood changes", "osteoporosis"],
            "interactions": ["nsaids", "vaccines", "diabetes medications"],
            "is_otc": 0,
        },
        {
            "name": "Hydrochlorothiazide",
            "generic_name": "Hydrochlorothiazide",
            "category": "Diuretic",
            "dosage_forms": ["tablet", "capsule"],
            "side_effects": ["dizziness", "electrolyte imbalance"],
            "interactions": ["lithium", "nsaids", "diabetes medications"],
            "is_otc": 0,
        },
        {
            "name": "Escitalopram",
            "generic_name": "Escitalopram Oxalate",
            "category": "SSRI",
            "dosage_forms": ["tablet", "solution"],
            "side_effects": ["nausea", "insomnia", "sexual dysfunction"],
            "interactions": ["maois", "nsaids", "tramadol"],
            "is_otc": 0,
        },
    ]

    # Add medications to database
    for med_data in medications_data:
        med = Medication(**med_data)
        db.add(med)

    # Add sample patients
    sample_patients = [
        {
            "name": "John Doe",
            "age": 45,
            "gender": "Male",
            "medical_history": ["Hypertension", "Type 2 Diabetes"],
        },
        {
            "name": "Jane Smith",
            "age": 32,
            "gender": "Female",
            "medical_history": ["Asthma"],
        },
        {
            "name": "Robert Johnson",
            "age": 67,
            "gender": "Male",
            "medical_history": ["Coronary Artery Disease", "Hyperlipidemia"],
        },
    ]

    for patient_data in sample_patients:
        patient = Patient(**patient_data)
        db.add(patient)

    db.commit()
    print(f"✓ Seeded {len(medications_data)} medications")
    print(f"✓ Seeded {len(sample_patients)} sample patients")
