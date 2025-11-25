from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Azure OpenAI
    AZURE_OPENAI_KEY: str
    AZURE_OPENAI_ENDPOINT: str
    AZURE_OPENAI_DEPLOYMENT: str
    AZURE_OPENAI_VERSION: str = "2024-02-15-preview"

    # Application
    DEBUG: bool = False
    LOG_LEVEL: str = "INFO"

    # CNN Model
    CNN_MODEL_PATH: str = "/models/medication_cnn.pth"
    CNN_IMAGE_SIZE: int = 224

    # Graph parameters
    SYMPTOM_DISEASE_NODES: int = 200
    DRUG_INTERACTION_EDGES: int = 5000

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
