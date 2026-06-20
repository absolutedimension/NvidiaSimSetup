from .config import settings


def send_magic_link(email: str, link: str) -> None:
    """Send the login link via Azure Communication Services. In dev (no ACS
    connection string), print the link to the console so you can click it."""
    subject = "Your TrigunAI LMS login link"
    html = f"""
    <div style="font-family:Poppins,Arial,sans-serif;max-width:480px;margin:auto">
      <h2 style="color:#2b2b33">Welcome to your cohort 🚀</h2>
      <p style="color:#555;line-height:1.6">Tap the button to log in. This link works once
      and expires in {settings.MAGIC_TTL_MIN} minutes.</p>
      <p style="margin:24px 0">
        <a href="{link}" style="background:#2d2d33;color:#fff;text-decoration:none;
        padding:14px 28px;border-radius:999px;font-weight:500">Log in to the LMS</a>
      </p>
      <p style="color:#999;font-size:13px">If the button doesn't work, paste this link:<br>{link}</p>
      <p style="color:#999;font-size:13px">— TrigunAI Innovations</p>
    </div>"""

    if not settings.ACS_CONNECTION_STRING:
        print("\n" + "=" * 70)
        print(f"[DEV] Magic link for {email}:\n{link}")
        print("=" * 70 + "\n")
        return

    try:
        from azure.communication.email import EmailClient

        client = EmailClient.from_connection_string(settings.ACS_CONNECTION_STRING)
        message = {
            "senderAddress": settings.ACS_SENDER,
            "recipients": {"to": [{"address": email}]},
            "content": {"subject": subject, "html": html},
        }
        poller = client.begin_send(message)
        poller.result()
    except Exception as exc:  # never block login on email transport
        print(f"[emailer] ACS send failed ({exc}); link for {email}: {link}")
