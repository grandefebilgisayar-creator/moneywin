"""MoneyWin outreach mailer — sends one email over SMTP_SSL.

Credentials come from the environment::

    SMTP_USER  sender address (default grandefe33@gmail.com)
    SMTP_PASS  app password — REQUIRED, no fallback

Gmail requires an app password (Google Account → Security → 2-Step Verification
→ App passwords), not the account password. Set it per-session or in the
system environment; never commit it.

The previous version fell back to a password hardcoded in the source, which is
a credential leak waiting to be committed. There is deliberately no default.
"""

from __future__ import annotations

import argparse
import os
import smtplib
import ssl
import sys
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from pathlib import Path
from typing import Optional

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.environ.get("SMTP_USER", "grandefe33@gmail.com")


class MissingCredential(RuntimeError):
    """SMTP_PASS is not set — refuse rather than send with a hardcoded secret."""


def _require_password() -> str:
    password = os.environ.get("SMTP_PASS", "").strip()
    if not password:
        raise MissingCredential(
            "SMTP_PASS ortam degiskeni tanimli degil. Gmail app password ile "
            "disaridan ver: SMTP_PASS='...' python email_sender.py ... "
            "(kaynak kodda sifre saklamayin, repo'ya commit etmeyin)"
        )
    return password


def send_email(to_email: str, subject: str, body: str, *, dry_run: bool = False) -> dict:
    """Send one plain-text email. Returns a result dict, never raises for SMTP errors."""
    if not to_email or "@" not in to_email:
        return {"sent": False, "error": f"gecersiz alici: {to_email!r}"}
    if dry_run:
        return {"sent": False, "dry_run": True, "to": to_email, "subject": subject}

    try:
        password = _require_password()
    except MissingCredential as exc:
        return {"sent": False, "error": str(exc)}

    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=30) as server:
            server.login(SMTP_USER, password)
            server.sendmail(SMTP_USER, [to_email], msg.as_string())
    except smtplib.SMTPAuthenticationError:
        return {"sent": False, "error": "SMTP giris basarisiz — SMTP_PASS gecersiz veya app password degil"}
    except (smtplib.SMTPException, OSError) as exc:
        return {"sent": False, "error": f"SMTP hatasi: {exc}"}

    return {"sent": True, "to": to_email, "subject": subject}


def main(argv: Optional[list] = None) -> int:
    ap = argparse.ArgumentParser(description="Send one MoneyWin outreach email.")
    ap.add_argument("to", nargs="?", help="Recipient address")
    ap.add_argument("subject", nargs="?", help="Subject line")
    ap.add_argument("body_file", nargs="?", help="File containing the plain-text body")
    ap.add_argument("--dry-run", action="store_true", help="Validate and report without sending")
    args = ap.parse_args(argv)

    if not (args.to and args.subject and args.body_file):
        ap.print_help()
        return 2

    try:
        body = Path(args.body_file).read_text(encoding="utf-8")
    except OSError as exc:
        print(f"govde dosyasi okunamadi: {exc}", file=sys.stderr)
        return 2

    result = send_email(args.to, args.subject, body, dry_run=args.dry_run)
    if result.get("dry_run"):
        print(f"[dry-run] gonderilmedi -> {result['to']} | {result['subject']}")
        return 0
    if result.get("sent"):
        print(f"gonderildi -> {result['to']} | {result['subject']}")
        return 0
    print(f"gonderilemedi: {result.get('error', 'bilinmeyen hata')}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
