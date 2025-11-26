import imaplib
import email
import logging
from email.header import decode_header
from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.conf import settings
from datetime import datetime

# Настройка логгера
logger = logging.getLogger('email_forwarding')

class Command(BaseCommand):
    help = 'Check for new emails and forward them'

    def handle(self, *args, **options):
        # IMAP settings for Gmail
        imap_server = "imap.gmail.com"
        imap_port = 993
        
        # Get credentials from environment or settings
        email_user = settings.FORWARD_FROM_EMAIL
        email_password = settings.EMAIL_HOST_PASSWORD
        
        logger.info(f"[{datetime.now()}] Starting email check process")
        self.stdout.write(self.style.SUCCESS(f'[{datetime.now()}] Starting email check...'))
        
        if not email_password:
            warning_msg = 'EMAIL_HOST_PASSWORD not set. Skipping email check.'
            logger.warning(warning_msg)
            self.stdout.write(self.style.WARNING(warning_msg))
            return
        
        try:
            # Connect to Gmail IMAP
            logger.info(f"[{datetime.now()}] Connecting to IMAP server: {imap_server}:{imap_port}")
            self.stdout.write(f'Connecting to {imap_server}...')
            
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            mail.login(email_user, email_password)
            logger.info(f"[{datetime.now()}] Successfully connected to IMAP server")
            self.stdout.write(self.style.SUCCESS('Connected to IMAP server'))
            
            mail.select("INBOX")
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            logger.info(f"[{datetime.now()}] Found {len(email_ids)} unread email(s)")
            
            if not email_ids:
                logger.info(f"[{datetime.now()}] No new emails to forward")
                self.stdout.write(self.style.SUCCESS('No new emails'))
                mail.close()
                mail.logout()
                return
            
            forwarded_count = 0
            failed_count = 0
            
            for email_id in email_ids:
                try:
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
                    
                    logger.info(f"[{datetime.now()}] Processing email: Subject='{subject}', From='{sender}'")
                    self.stdout.write(f'Processing: {subject} from {sender}...')
                    
                    # Forward email
                    try:
                        send_mail(
                            subject=f'Пересылка: {subject}',
                            message=f'От: {sender}\n\n{self.get_email_body(email_message)}',
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[settings.FORWARD_TO_EMAIL],
                            fail_silently=False,
                        )
                        
                        forwarded_count += 1
                        success_msg = f'Successfully forwarded email: {subject} to {settings.FORWARD_TO_EMAIL}'
                        logger.info(f"[{datetime.now()}] {success_msg}")
                        self.stdout.write(self.style.SUCCESS(f'✓ Forwarded: {subject}'))
                        
                    except Exception as send_error:
                        failed_count += 1
                        error_msg = f'Failed to forward email "{subject}": {str(send_error)}'
                        logger.error(f"[{datetime.now()}] {error_msg}")
                        self.stdout.write(self.style.ERROR(f'✗ Failed: {subject} - {str(send_error)}'))
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f'Error processing email {email_id}: {str(e)}'
                    logger.error(f"[{datetime.now()}] {error_msg}")
                    self.stdout.write(self.style.ERROR(error_msg))
            
            mail.close()
            mail.logout()
            
            summary_msg = f'Completed: {forwarded_count} forwarded, {failed_count} failed'
            logger.info(f"[{datetime.now()}] {summary_msg}")
            self.stdout.write(self.style.SUCCESS(f'\n{summary_msg}'))
            
        except Exception as e:
            error_msg = f'Critical error: {str(e)}'
            logger.error(f"[{datetime.now()}] {error_msg}", exc_info=True)
            self.stdout.write(self.style.ERROR(error_msg))
    
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
