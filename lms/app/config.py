import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-change-me")
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./lms.db")
    BASE_URL = os.getenv("BASE_URL", "http://localhost:8000").rstrip("/")
    ADMIN_EMAILS = {
        e.strip().lower()
        for e in os.getenv("ADMIN_EMAILS", "deepak@trigunai.com").split(",")
        if e.strip()
    }
    ACS_CONNECTION_STRING = os.getenv("ACS_CONNECTION_STRING", "").strip()
    ACS_SENDER = os.getenv("ACS_SENDER", "DoNotReply@trigunai.com")
    MAGIC_TTL_MIN = int(os.getenv("MAGIC_TTL_MIN", "20"))
    # Azure OpenAI (the TrigunAI guide / personalized examples)
    AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT", "").strip().rstrip("/")
    AOAI_KEY = os.getenv("AOAI_KEY", "").strip()
    AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "gpt-4o-mini")
    AOAI_API_VERSION = os.getenv("AOAI_API_VERSION", "2024-10-21")
    # GitHub "owner/repo" of the cohort starter repo → one-click Codespaces
    STARTER_REPO = os.getenv("STARTER_REPO", "").strip()

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()
