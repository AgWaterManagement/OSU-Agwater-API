import os
import smtplib
from email.message import EmailMessage
from flask import current_app

def send_email(params):
    """
    Sends an email using the SMTP server configured in the application.

    Args:
        params (dict): A dictionary containing:
            - recipient_email (list): List of recipient email addresses.
            - subject (str): Subject of the email.
            - body (str): Body of the email.
            - attachments (list): List of file paths to attach to the email.

    Returns:
        str: Success or failure message.
    """
    recipient_emails = params.get('recipient_email', [])
    subject = params.get('subject', 'No Subject')
    body = params.get('body', 'No Body')
    attachment_paths = params.get('attachments', [])

    # Get SMTP configuration from Flask app config
    smtp_server = current_app.config.get('SMTP_SERVER', 'mail.engr.oregonstate.edu')
    smtp_port = current_app.config.get('SMTP_PORT', 25)
    sender_email = current_app.config.get('SMTP_USERNAME', '')
    sender_password = current_app.config.get('SMTP_PASSWORD', '')

    if not sender_email or not sender_password:
        return "SMTP credentials are not configured."

    # Create the email message
    msg = EmailMessage()
    msg['From'] = sender_email
    msg['To'] = ', '.join(recipient_emails)
    msg['Subject'] = subject
    msg.set_content(body)

    # Attach files
    for path in attachment_paths:
        if os.path.isfile(path):
            with open(path, 'rb') as file:
                file_data = file.read()
                file_name = os.path.basename(path)
                msg.add_attachment(file_data, maintype='application', subtype='octet-stream', filename=file_name)

    # Send the email
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()  # Upgrade the connection to secure
            server.login(sender_email, sender_password)
            server.send_message(msg)
        return "Email sent successfully!"
    except Exception as e:
        return f"Failed to send email: {str(e)}"
