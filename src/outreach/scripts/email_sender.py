import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import csv

def send_email(smtp_host, smtp_port, username, password, to_email, subject, body):
    msg = MIMEMultipart()
    msg["From"] = username
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))
    with smtplib.SMTP_SSL(smtp_host, smtp_port) as server:
        server.login(username, password)
        server.sendmail(username, to_email, msg.as_string())

if __name__ == "__main__":
    import sys
    to = sys.argv[1]
    subject = sys.argv[2]
    body = sys.argv[3]
    send_email(
        os.environ.get("SMTP_HOST", "smtp.gmail.com"),
        int(os.environ.get("SMTP_PORT", "465")),
        os.environ.get("SMTP_USER", ""),
        os.environ.get("SMTP_PASS", ""),
        to,
        subject,
        body,
    )
