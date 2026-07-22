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
    # Admin WhatsApp notifications (founder ops feed) — WhatsApp Cloud API via the gurukul_announce
    # template. Inert until WA_TOKEN + WA_PHONE_ID + ADMIN_WHATSAPP are all set. See app/notify.py.
    WA_TOKEN = os.getenv("WA_TOKEN", "").strip()
    WA_PHONE_ID = os.getenv("WA_PHONE_ID", "").strip()
    WA_GRAPH_VERSION = os.getenv("WA_GRAPH_VERSION", "v21.0").strip()
    ADMIN_WHATSAPP = os.getenv("ADMIN_WHATSAPP", "").strip()   # digits only, e.g. 9198XXXXXXXX
    NOTIFY_ENABLED = os.getenv("NOTIFY_ENABLED", "1") == "1"
    # Azure OpenAI (the TrigunAI guide / personalized examples)
    AOAI_ENDPOINT = os.getenv("AOAI_ENDPOINT", "").strip().rstrip("/")
    AOAI_KEY = os.getenv("AOAI_KEY", "").strip()
    AOAI_DEPLOYMENT = os.getenv("AOAI_DEPLOYMENT", "gpt-4o-mini")
    AOAI_API_VERSION = os.getenv("AOAI_API_VERSION", "2024-10-21")
    # GitHub "owner/repo" of the cohort starter repo → one-click Codespaces
    STARTER_REPO = os.getenv("STARTER_REPO", "").strip()
    # Acharya web chat (Gurukul VM). CHAT_SECRET must match the bridge's CHAT_SECRET.
    CHAT_SECRET = os.getenv("CHAT_SECRET", "").strip()
    GURUKUL_CHAT_URL = os.getenv("GURUKUL_CHAT_URL", "https://gurukul.trigunai.com/chat").rstrip("/")

    # ---- Subscriptions (Razorpay) ----
    # MASTER SWITCH: when False, the access gate is a no-op — nothing is paywalled,
    # current cohort behaviour is unchanged. Flip to True only after live keys are tested.
    SUBS_ENABLED = os.getenv("SUBS_ENABLED", "false").lower() in ("1", "true", "yes")
    RZP_KEY_ID = os.getenv("RZP_KEY_ID", "").strip()
    RZP_KEY_SECRET = os.getenv("RZP_KEY_SECRET", "").strip()
    RZP_PLAN_ID = os.getenv("RZP_PLAN_ID", "").strip()            # ₹499/month plan, created in Razorpay
    RZP_WEBHOOK_SECRET = os.getenv("RZP_WEBHOOK_SECRET", "").strip()
    TRIAL_DAYS = int(os.getenv("TRIAL_DAYS", "7"))
    PRICE_INR = int(os.getenv("PRICE_INR", "499"))
    SUB_TOTAL_COUNT = int(os.getenv("SUB_TOTAL_COUNT", "120"))    # max billing cycles (10 yrs ≈ "until cancelled")
    # Shared secret so learn.trigunai.com's admin can pull self-paced stats (server-to-server only)
    BRIDGE_KEY = os.getenv("BRIDGE_KEY", "").strip()

    # Learning-loop instrumentation — capture every graded attempt into learning_events.
    # Dark by default; flip to "1" once the consent copy ("your usage improves Acharya") is live.
    LOOP_CAPTURE_ENABLED = os.getenv("LOOP_CAPTURE_ENABLED", "0") == "1"

    # ---- Student exam-prep assessment plan (₹199/mo) — a SEPARATE, parallel Razorpay track ----
    # Its OWN master switch, independent of SUBS_ENABLED (the ₹499 course plan). While False the
    # assessment gate is a no-op — /exam-prep stays free for everyone (the soft-launch state).
    # To go live: create a ₹199/month plan in Razorpay, set RZP_ASSESS_PLAN_ID, flip ASSESS_ENABLED=1.
    ASSESS_ENABLED = os.getenv("ASSESS_ENABLED", "false").lower() in ("1", "true", "yes")
    RZP_ASSESS_PLAN_ID = os.getenv("RZP_ASSESS_PLAN_ID", "").strip()   # ₹199/month plan, created in Razorpay
    ASSESS_PRICE_INR = int(os.getenv("ASSESS_PRICE_INR", "199"))
    ASSESS_TRIAL_DAYS = int(os.getenv("ASSESS_TRIAL_DAYS", "14"))

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()
