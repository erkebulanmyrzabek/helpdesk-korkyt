import imaplib
import email
from email.header import decode_header
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings

class Command(BaseCommand):
    help = 'Check for new emails and forward them'

    def handle(self, *args, **options):
        # IMAP settings for Gmail
        imap_server = "imap.gmail.com"
        imap_port = 993
        
        # Get credentials from environment or settings
        email_user = settings.FORWARD_FROM_EMAIL
        email_password = settings.EMAIL_HOST_PASSWORD
        
        if not email_password:
            self.stdout.write(self.style.WARNING('EMAIL_HOST_PASSWORD not set. Skipping email check.'))
            return
        
        try:
            # Connect to Gmail IMAP
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(email_user, email_password)
            mail.select("INBOX")
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            if not email_ids:
                self.stdout.write(self.style.SUCCESS('No new emails'))
                return
            
            forwarded_count = 0
            for email_id in email_ids:
                # Fetch email
                status, msg_data = mail.fetch(email_id, "(RFC822)")
                email_body = msg_data[0][1]
                email_message = email.message_from_bytes(email_body)
                
                # Decode subject
                subject = decode_header(email_message["Subject"])[0][0]
                if isinstance(subject, bytes):
                    subject = subject.decode()
                
                # Get sender
                sender = email_message.get("From")
                
                # Forward email
                send_mail(
                    subject=f'Пересылка: {subject}',
                    message=f'От: {sender}\n\n{self.get_email_body(email_message)}',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[settings.FORWARD_TO_EMAIL],
                    fail_silently=False,
                )
                
                forwarded_count += 1
                self.stdout.write(self.style.SUCCESS(f'Forwarded email: {subject}'))
            
            mail.close()
            mail.logout()
            
            self.stdout.write(self.style.SUCCESS(f'Successfully forwarded {forwarded_count} email(s)'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
    
    def get_email_body(self, msg):
        """Extract email body"""
        body = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body = part.get_payload(decode=True).decode()
                    except:
                        pass
        else:
            try:
                body = msg.get_payload(decode=True).decode()
            except:
                pass
        return body

