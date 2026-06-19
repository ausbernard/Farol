from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator

class Settings(BaseSettings):
    railway_token: str
    railway_project_id: str
    railway_service_id: str
    railway_workspace_id: str
    expected_projects: str = ""

    @field_validator("expected_projects", mode="after")
    @classmethod
    def split_csv(cls, v) -> list[str]:
        if not v:
            return []
        return [name.strip() for name in v.split(",") if name.strip()]

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()