import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv
import os

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 465
SMTP_USER = os.environ.get("SMTP_USER", "grandefe33@gmail.com")
SMTP_PASS = os.environ.get("SMTP_PASS", "Efe7174")

def send_email(to_email: str, subject: str, body: str):
    msg = MIMEMultipart()
    msg["From"] = SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT) as server:
        server.login(SMTP_USER, SMTP_PASS)
        server.sendmail(SMTP_USER, to_email, msg.as_string())
    return True

if __name__ == "__main__":
    import sys
    to = sys.argv[1]
    subject = sys.argv[2]
    body_file = sys.argv[3]
    with open(body_file, "r", encoding="utf-8") as f:
        body = f.read()
    ok = send_email(to, subject, body)
    print("sent" if ok else "failed")
