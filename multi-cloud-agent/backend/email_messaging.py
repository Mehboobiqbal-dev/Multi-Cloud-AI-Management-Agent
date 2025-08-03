from typing import Dict, Any
from googleapiclient.discovery import build
import base64

def send_email_gmail(subject: str, body: str, to: str, credentials: Dict[str, str]) -> str:
    """Sends an email via Gmail API."""
    service = build('gmail', 'v1', credentials=credentials)
    message = {'raw': base64.urlsafe_b64encode(f'Subject: {subject}\nTo: {to}\n\n{body}'.encode()).decode()}
    try:
        service.users().messages().send(userId='me', body=message).execute()
        return "Email sent successfully."
    except Exception as e:
        return f"Error sending email: {e}"

def read_emails_gmail(credentials: Dict[str, str], max_results: int = 5) -> str:
    """Reads recent emails from Gmail."""
    service = build('gmail', 'v1', credentials=credentials)
    try:
        results = service.users().messages().list(userId='me', maxResults=max_results).execute()
        messages = results.get('messages', [])
        summaries = []
        for msg in messages:
            msg_data = service.users().messages().get(userId='me', id=msg['id']).execute()
            summaries.append(f"From: {msg_data['payload']['headers'][0]['value']} Subject: {msg_data['payload']['headers'][1]['value']}")
        return "\n".join(summaries)
    except Exception as e:
        return f"Error reading emails: {e}"

def reply_email_gmail(message_id: str, body: str, credentials: Dict[str, str]) -> str:
    """Replies to a Gmail email."""
    service = build('gmail', 'v1', credentials=credentials)
    try:
        message = {'raw': base64.urlsafe_b64encode(body.encode()).decode(), 'threadId': message_id}
        service.users().messages().send(userId='me', body=message).execute()
        return "Replied to email successfully."
    except Exception as e:
        return f"Error replying to email: {e}"

def send_email_outlook(subject: str, body: str, to: str, credentials: Dict[str, str]) -> str:
    """Sends an email via Outlook (placeholder)."""
    # Implement actual Outlook API integration here
    return "Email sent via Outlook successfully (placeholder)."