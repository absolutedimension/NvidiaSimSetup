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
    # Read-only ops "pulse" key — gates GET /admin/api/pulse (the campaign-tracker skill).
    # Override in prod via env. Rotate by changing PULSE_KEY on the container app.
    PULSE_KEY = os.getenv("PULSE_KEY", "trigunai-pulse-2026").strip()
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
    RZP_ASSESS_PLAN_ID = os.getenv("RZP_ASSESS_PLAN_ID", "").strip()   # STUDENT monthly plan (₹249)
    ASSESS_PRICE_INR = int(os.getenv("ASSESS_PRICE_INR", "249"))         # student monthly
    # Teacher/institute tier — a SEPARATE Razorpay plan (min ₹999/mo). Same 14-day trial + gate;
    # the subscribe flow picks this plan when Student.is_teacher is set.
    RZP_ASSESS_TEACHER_PLAN_ID = os.getenv("RZP_ASSESS_TEACHER_PLAN_ID", "").strip()  # TEACHER monthly plan (₹999)
    ASSESS_TEACHER_PRICE_INR = int(os.getenv("ASSESS_TEACHER_PRICE_INR", "999"))       # teacher monthly (from)
    ASSESS_PASS_PRICE_INR = int(os.getenv("ASSESS_PASS_PRICE_INR", "1299"))  # "till your exam" Pass — the LEAD offer
    ASSESS_TRIAL_DAYS = int(os.getenv("ASSESS_TRIAL_DAYS", "14"))

    # ---- Teacher / institute (B2B) pricing — land-and-expand (see PRICING_MODEL.md, 2026-07-24) ----
    # Billing not yet wired; these drive the DISPLAYED tiers on /teacher so the offer is testable on a
    # real buyer. First-paid closes over WhatsApp/transfer (CONTACT_WA) until Razorpay B2B is live.
    TEACHER_SOLO_INR = int(os.getenv("TEACHER_SOLO_INR", "999"))          # 1 teacher, <=60 students (the 0->1 wedge)
    TEACHER_COACHING_INR = int(os.getenv("TEACHER_COACHING_INR", "2999")) # <=300 students, white-label + analytics
    TEACHER_INSTITUTE_INR = int(os.getenv("TEACHER_INSTITUTE_INR", "7999"))  # unlimited + branding + priority

    # Real contact handles for manual activation while billing is inert (both verified live in templates)
    CONTACT_WA = os.getenv("CONTACT_WA", "919135255107").strip()         # Acharya WhatsApp (wa.me/<this>)
    CONTACT_EMAIL = os.getenv("CONTACT_EMAIL", "deepak@trigunai.com").strip()

    # ---- Google Ads (student exam-prep funnel) ----
    # The CONVERSION = a completed free signup (a new student who lands in the test = "entered + using"),
    # fired once on /exam-prep/test?new=1 — NOT on the click. Set STUDENT_SIGNUP_CONV_LABEL after you
    # create the "Student free signup" conversion action in Google Ads (its value is like "abcDEF123");
    # until it's set the conversion tag simply doesn't fire.
    ADS_CONVERSION_ID = os.getenv("ADS_CONVERSION_ID", "AW-18339354528").strip()
    STUDENT_SIGNUP_CONV_LABEL = os.getenv("STUDENT_SIGNUP_CONV_LABEL", "").strip()

    # Same pattern, teacher side. CONVERSION = a new teacher account created at /teacher/signup
    # (email or Google), fired once on landing back at /teacher?new=1. Set TEACHER_SIGNUP_CONV_LABEL
    # after creating the "Teacher signup" conversion action in Google Ads.
    TEACHER_SIGNUP_CONV_LABEL = os.getenv("TEACHER_SIGNUP_CONV_LABEL", "").strip()

    # Google One Tap sign-in (register with ONE TAP, no magic link) for the ad teaser funnel.
    # Set GOOGLE_CLIENT_ID to a Web OAuth 2.0 Client ID (Google Cloud Console → Credentials;
    # authorized JS origin = https://acharya.trigunai.com). Empty = One Tap hidden, email path only.
    GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID", "").strip()

    # ---- RAG question generator (the /examgen API — authentic exam-paper style) ----
    # High-quality, past-paper-imitating question generation, currently IIT-JEE Physics only.
    # The LMS proxies it server-side (key never reaches the browser). Empty URL = RAG off →
    # every subject falls back to the in-LMS generator (assess_gen).
    # MIGRATED 2026-07-23 to the ALWAYS-ON Gurukul VM so the exam generator survives the EC2 GPU
    # box being stopped. The default MUST stay on gurukul — the old rtx.trigunai.com host lives on
    # the EC2 box that gets powered off, so falling back to it would silently break generation.
    EXAMGEN_URL = os.getenv("EXAMGEN_URL", "https://gurukul.trigunai.com/examgen").strip().rstrip("/")
    EXAMGEN_KEY = os.getenv("EXAMGEN_KEY", "").strip()
    EXAMGEN_TIMEOUT = int(os.getenv("EXAMGEN_TIMEOUT", "230"))

    @property
    def is_sqlite(self) -> bool:
        return self.DATABASE_URL.startswith("sqlite")


settings = Settings()
