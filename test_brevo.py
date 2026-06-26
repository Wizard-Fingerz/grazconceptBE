"""
Run this to diagnose the Brevo SMTP connection:
  python test_brevo.py
"""
import smtplib, ssl, os
from dotenv import load_dotenv
load_dotenv(os.path.join(os.path.dirname(__file__), '.env'))

LOGIN = os.environ.get('BREVO_SMTP_LOGIN', '')
KEY   = os.environ.get('BREVO_SMTP_KEY', '')
FROM  = os.environ.get('DEFAULT_FROM_EMAIL', 'no-reply@grazconcept.com.ng')

print(f"Login : {repr(LOGIN)}")
print(f"Key   : {KEY[:12]}...{KEY[-6:] if len(KEY) > 18 else repr(KEY)}")
print(f"From  : {repr(FROM)}")
print()

if not LOGIN or not KEY:
    print("❌  Credentials not loaded from .env — check formatting (no spaces around =, quote values with < >)")
    raise SystemExit(1)

print("Connecting to smtp-relay.brevo.com:587 ...")
try:
    with smtplib.SMTP('smtp-relay.brevo.com', 587, timeout=15) as s:
        s.set_debuglevel(1)          # prints every SMTP command + response
        s.ehlo()
        s.starttls()
        s.ehlo()
        s.login(LOGIN, KEY)
        print("\n✅  Login successful — Brevo SMTP is working!")
except smtplib.SMTPAuthenticationError as e:
    print(f"\n❌  Authentication failed: {e}")
    print()
    print("Fix: go to brevo.com → Settings → SMTP & API → SMTP tab")
    print("     click  'Generate a new SMTP key'  (NOT the API key)")
    print("     paste the new key as BREVO_SMTP_KEY in your .env")
except Exception as e:
    print(f"\n❌  Connection error: {type(e).__name__}: {e}")
