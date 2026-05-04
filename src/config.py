from enum import Enum
from pydantic import BaseModel, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

DEFAULT_GEMINI_MODEL = "gemini-2.5-flash"

class EnvironmentType(str, Enum):
    TEST = "TEST"
    DEV = "DEV"
    PROD = "PROD"

class DatabaseSettings(BaseModel):
    user: str
    password: SecretStr
    host: str
    port: int = 5432
    name: str

    @property
    def url(self) -> str:
        return f"postgresql://{self.user}:{self.password.get_secret_value()}@{self.host}:{self.port}/{self.name}"

class LLMSettings(BaseModel):
    generator: str = DEFAULT_GEMINI_MODEL
    critic: str = DEFAULT_GEMINI_MODEL
    classifier: str = DEFAULT_GEMINI_MODEL

class AppSettings(BaseSettings):
    environment: EnvironmentType = EnvironmentType.DEV
    max_iterations: int = 5
    google_api_key: SecretStr

    db_prod: DatabaseSettings
    db_test: DatabaseSettings
    models: LLMSettings = LLMSettings()

    model_config = SettingsConfigDict(
        env_nested_delimiter="__",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = AppSettings()
