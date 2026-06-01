from functools import lru_cache
from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

ROOT_DIR = Path(__file__).resolve().parents[2]

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ROOT_DIR / ".env", env_file_encoding="utf-8", extra="ignore")

    app_name: str = "OptiCare Glaucoma Screening"
    app_env: str = "production"
    secret_key: str = "change-this-secret-key"

    database_path: str = "data/eyecare.db"
    upload_dir: str = "data/uploads"
    report_dir: str = "data/reports"
    rag_docs_dir: str = "data/rag_docs"

    api_base_url: str = "http://127.0.0.1:8000"

    model_backend: str = "disabled"  # disabled, external_api, local_torch
    model_path: str = "models/glaucoma_model.pt"
    model_device: str = "cpu"
    model_threshold_high: float = 0.60
    model_threshold_uncertain: float = 0.20
    model_api_url: str = "http://127.0.0.1:9000/predict"
    model_api_key: str = ""

    llm_provider: str = "disabled"
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"

    @property
    def db_path(self) -> Path:
        p = Path(self.database_path)
        return p if p.is_absolute() else ROOT_DIR / p

    @property
    def uploads_path(self) -> Path:
        p = Path(self.upload_dir)
        return p if p.is_absolute() else ROOT_DIR / p

    @property
    def reports_path(self) -> Path:
        p = Path(self.report_dir)
        return p if p.is_absolute() else ROOT_DIR / p

    @property
    def rag_docs_path(self) -> Path:
        p = Path(self.rag_docs_dir)
        return p if p.is_absolute() else ROOT_DIR / p

    @property
    def model_file_path(self) -> Path:
        p = Path(self.model_path)
        return p if p.is_absolute() else ROOT_DIR / p

@lru_cache
def get_settings() -> Settings:
    settings = Settings()
    settings.db_path.parent.mkdir(parents=True, exist_ok=True)
    settings.uploads_path.mkdir(parents=True, exist_ok=True)
    settings.reports_path.mkdir(parents=True, exist_ok=True)
    settings.rag_docs_path.mkdir(parents=True, exist_ok=True)
    return settings
