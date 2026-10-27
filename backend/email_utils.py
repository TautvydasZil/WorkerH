import os
import smtplib
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv

logger = logging.getLogger('app')

# Užtikrinti, kad .env būtų nuskaitytas nepriklausomai nuo importavimo tvarkos
_base_dir = Path(__file__).resolve().parent
load_dotenv(_base_dir / '.env')
load_dotenv(_base_dir.parent / '.env')

def get_smtp_config():
    return {
        'host': os.getenv('SMTP_HOST', '').strip(),
        'port': int(os.getenv('SMTP_PORT', '587').strip() or '587'),
        'user': os.getenv('SMTP_USER', '').strip(),
        'pass': os.getenv('SMTP_PASS', '').strip(),
        'from': (os.getenv('SMTP_FROM', '').strip() or os.getenv('SMTP_USER', '').strip()),
        'frontend_url': os.getenv('FRONTEND_URL', 'http://localhost:5173').strip().rstrip('/'),
    }

ROLE_LT = {'worker': 'darbuotojo', 'manager': 'vadybininko', 'admin': 'administratoriaus'}


def _send_email(to_email: str, subject: str, html: str, fallback_link: str = '') -> bool:
    cfg = get_smtp_config()
    if not cfg['host'] or not cfg['user'] or not cfg['pass']:
        logger.warning(
            'SMTP not configured — email not sent to %s. Tiesioginė nuoroda: %s',
            to_email,
            fallback_link or '(žr. sąsają)',
        )
        return False
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From']    = cfg['from']
    msg['To']      = to_email
    msg.attach(MIMEText(html, 'html', 'utf-8'))
    try:
        logger.info('Sending email to %s via %s:%s...', to_email, cfg['host'], cfg['port'])
        with smtplib.SMTP(cfg['host'], cfg['port'], timeout=15) as server:
            server.ehlo()
            server.starttls()
            server.login(cfg['user'], cfg['pass'])
            server.sendmail(cfg['from'], [to_email], msg.as_string())
        logger.info('Email successfully sent to %s', to_email)
        return True
    except Exception as exc:
        logger.error('Failed to send email to %s: %s', to_email, exc)
        return False


def send_invite_email(to_email: str, token: str, role: str) -> None:
    cfg = get_smtp_config()
    link    = f"{cfg['frontend_url']}/register?token={token}"
    role_lt = ROLE_LT.get(role, role)
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px;color:#1e293b">Pakvietimas į Darbuotojų Apskaitą</h2>
      <p style="color:#475569;margin:0 0 24px">
        Jus pakvietė prisijungti kaip <strong>{role_lt}</strong>.
        Nuoroda galioja 7 dienas ir yra vienkartinė.
      </p>
      <a href="{link}"
         style="display:inline-block;padding:12px 24px;background:#4f46e5;color:#fff;
                border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Registruotis
      </a>
      <p style="color:#94a3b8;font-size:12px;margin:24px 0 0">
        Arba nukopijuokite šią nuorodą:<br>
        <span style="color:#4f46e5">{link}</span>
      </p>
    </div>"""
    _send_email(to_email, 'Pakvietimas registruotis', html, fallback_link=link)


def send_password_reset_email(to_email: str, token: str) -> None:
    cfg = get_smtp_config()
    link = f"{cfg['frontend_url']}/reset-password?token={token}"
    html = f"""
    <div style="font-family:sans-serif;max-width:520px;margin:0 auto;padding:32px 24px">
      <h2 style="margin:0 0 8px;color:#1e293b">Slaptažodžio keitimas</h2>
      <p style="color:#475569;margin:0 0 24px">
        Gautas prašymas pakeisti slaptažodį. Nuoroda galioja 1 valandą.
        Jei to neprašėte — nieko nedarykite.
      </p>
      <a href="{link}"
         style="display:inline-block;padding:12px 24px;background:#4f46e5;color:#fff;
                border-radius:8px;text-decoration:none;font-weight:600;font-size:15px">
        Keisti slaptažodį
      </a>
      <p style="color:#94a3b8;font-size:12px;margin:24px 0 0">
        Arba nukopijuokite šią nuorodą:<br>
        <span style="color:#4f46e5">{link}</span>
      </p>
    </div>"""
    _send_email(to_email, 'Slaptažodžio keitimas', html, fallback_link=link)
