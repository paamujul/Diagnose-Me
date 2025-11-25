from sqlalchemy import Column, Integer, String, DateTime, Text, JSON, Float, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.database import Base


class Patient(Base):
    __tablename__ = "patients"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    age = Column(Integer)
    gender = Column(String)
    medical_history = Column(JSON, default=list)
    created_at = Column(DateTime, default=datetime.utcnow)

    sessions = relationship("DiagnosticSession", back_populates="patient")
    prescriptions = relationship("Prescription", back_populates="patient")


class DiagnosticSession(Base):
    __tablename__ = "diagnostic_sessions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    symptoms = Column(JSON, default=list)
    conversation_history = Column(JSON, default=list)
    diagnosis = Column(JSON)
    confidence_score = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    patient = relationship("Patient", back_populates="sessions")
    report = relationship("DiagnosticReport", back_populates="session", uselist=False)


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_reports"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("diagnostic_sessions.id"), unique=True)
    content = Column(Text)
    findings = Column(JSON)
    recommendations = Column(JSON)
    generated_at = Column(DateTime, default=datetime.utcnow)

    session = relationship("DiagnosticSession", back_populates="report")


class Medication(Base):
    __tablename__ = "medications"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    generic_name = Column(String)
    category = Column(String)
    dosage_forms = Column(JSON)
    side_effects = Column(JSON)
    interactions = Column(JSON)
    is_otc = Column(Integer, default=0)  # 0=False, 1=True


class Prescription(Base):
    __tablename__ = "prescriptions"

    id = Column(Integer, primary_key=True, index=True)
    patient_id = Column(Integer, ForeignKey("patients.id"))
    medication_id = Column(Integer, ForeignKey("medications.id"))
    dosage = Column(String)
    frequency = Column(String)
    duration = Column(String)
    prescribed_date = Column(DateTime, default=datetime.utcnow)
    active = Column(Integer, default=1)

    patient = relationship("Patient", back_populates="prescriptions")


class MedicationImage(Base):
    __tablename__ = "medication_images"

    id = Column(Integer, primary_key=True, index=True)
    medication_id = Column(Integer, ForeignKey("medications.id"))
    image_path = Column(String)
    fill_level = Column(String)  # full, half, quarter, empty
    confidence = Column(Float)
    processed_at = Column(DateTime, default=datetime.utcnow)
