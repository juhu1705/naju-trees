"""
Enthält Funktionen für den E-Mail-Versand.
"""
import os
import smtplib
from datetime import datetime
from email.mime.text import MIMEText

from typing import Optional, Union

from flask import current_app, render_template


def _smtp_create() -> Union[smtplib.SMTP, smtplib.SMTP_SSL]:
    """Erstellt die der Konfiguration entsprechende SMTP-Instanz und verbindet zum SMTP-Server."""
    logger = current_app.logger
    logger.debug("Stellt Verbindung zum SMTP-Server her...")

    smtp = smtplib.SMTP("smtp.live.com:587")
    smtp.starttls()

    with open(os.path.join(current_app.instance_path, '2357.p')) as file:
        lines = file.read().splitlines()
        username = lines[0]
        password = lines[1]
    smtp.login(username, password)

    logger.debug("Erfolgreich mit SMTP-Server verbunden.")

    return smtp


def _send_mail(address: str, subject: str, content: str, content_type="html", content_charset="utf-8",
               smtp: Optional[smtplib.SMTP] = None) -> None:
    """
    Sendet eine E-Mail mit den in der NateMan-Konfiguration angegebenen SMTP-Daten.

    :param address: Adresse, zu der die E-Mail gesendet werden soll
    :param subject: Betreff der E-Mail
    :param content: Inhalt der E-Mail
    :param content_type: Inhaltstyp der E-Mail
    :param content_charset: Zeichensatz des E-Mail-Inhalts
    :param smtp: SMTP-Verbindung. Falls keine Verbindung angegeben wird, wird eine erstellt
    (und nach dem E-Mail-Versand geschlossen).
    """
    logger = current_app.logger
    sender_address = 'fabius1705@live.de'

    msg = MIMEText(content, content_type, content_charset)
    msg["From"] = f"DfS <{sender_address}>"
    msg["Subject"] = subject

    smtp_param = smtp is not None
    if not smtp_param:
        smtp = _smtp_create()

    logger.debug(f"E-Mail wird an {address} versandt...")
    try:
        smtp.sendmail(sender_address, address, msg.as_string())
    except smtplib.SMTPRecipientsRefused as exc:
        if not smtp_param:
            smtp.close()
        logger.debug(f"E-Mail an {address} konnte nicht versandt werden "
                     f"(wahrscheinlich ungültige Adresse).", exc_info=exc)
        raise
    else:
        logger.debug(f"E-Mail an {address} erfolgreich versandt.")

    if not smtp_param:
        smtp.close()


def send_password_reset_email(address, user, token):
    content = render_template('emails/reset.html', user=user, token=token)
    _send_mail(address, 'DfS: Passwort zurücksetzen', content)


def send_confirmation_email(address, user, token):
    content = render_template('emails/confirm.html', user=user, token=token)
    _send_mail(address, 'DfS: Anmeldung Abschließen', content)
