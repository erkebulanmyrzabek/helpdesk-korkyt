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
    help = 'Check for new emails and forward them (DISABLED - use ticket creation instead)'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--enable',
            action='store_true',
            help='Enable email forwarding (disabled by default)',
        )

    def handle(self, *args, **options):
        # По умолчанию команда отключена
        if not options.get('enable', False):
            self.stdout.write(self.style.WARNING(
                '\n⚠️  Автоматическая пересылка писем ОТКЛЮЧЕНА!\n'
                'Письма отправляются только при создании тикетов через веб-интерфейс.\n'
                'Если нужно включить пересылку, используйте: python3 manage.py check_email --enable\n'
            ))
            return
        
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
            self.stdout.write(self.style.WARNING('⚠️  Установите EMAIL_HOST_PASSWORD в settings.py или через переменную окружения'))
            return
        
        try:
            # Connect to Gmail IMAP
            logger.info(f"[{datetime.now()}] Connecting to IMAP server: {imap_server}:{imap_port}")
            self.stdout.write(f'Подключение к {imap_server}...')
            
            mail = imaplib.IMAP4_SSL(imap_server, imap_port)
            
            try:
                mail.login(email_user, email_password)
            except imaplib.IMAP4.error as auth_error:
                error_msg = f'Ошибка аутентификации: {str(auth_error)}'
                logger.error(f"[{datetime.now()}] {error_msg}")
                self.stdout.write(self.style.ERROR(f'\n❌ {error_msg}'))
                self.stdout.write(self.style.WARNING('\n📋 ВАЖНО: При включенной двухфакторной аутентификации нужен App Password!'))
                self.stdout.write(self.style.WARNING('📖 Инструкция: См. EMAIL_SETUP_INSTRUCTIONS.md'))
                self.stdout.write(self.style.WARNING('🔗 Создать App Password: https://myaccount.google.com/apppasswords'))
                return
            
            logger.info(f"[{datetime.now()}] Successfully connected to IMAP server")
            self.stdout.write(self.style.SUCCESS('✓ Подключено к почтовому серверу'))
            
            mail.select("INBOX")
            
            # Search for unread emails
            status, messages = mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            
            logger.info(f"[{datetime.now()}] Found {len(email_ids)} unread email(s)")
            self.stdout.write(f'Найдено непрочитанных писем: {len(email_ids)}')
            
            if not email_ids:
                logger.info(f"[{datetime.now()}] No new emails to forward")
                self.stdout.write(self.style.SUCCESS('Нет новых писем для пересылки'))
                mail.close()
                mail.logout()
                return
            
            # Предупреждение о большом количестве писем
            if len(email_ids) > 10:
                self.stdout.write(self.style.WARNING(
                    f'\n⚠️  ВНИМАНИЕ: Найдено {len(email_ids)} непрочитанных писем!\n'
                    'Это может занять много времени. Рекомендуется использовать создание тикетов через веб-интерфейс.\n'
                ))
                response = input('Продолжить пересылку? (yes/no): ')
                if response.lower() != 'yes':
                    self.stdout.write(self.style.SUCCESS('Пересылка отменена'))
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
                    self.stdout.write(f'Обработка: {subject} от {sender}...')
                    
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
                        self.stdout.write(self.style.SUCCESS(f'✓ Переслано: {subject} → {settings.FORWARD_TO_EMAIL}'))
                        
                    except Exception as send_error:
                        failed_count += 1
                        error_msg = f'Failed to forward email "{subject}": {str(send_error)}'
                        logger.error(f"[{datetime.now()}] {error_msg}", exc_info=True)
                        self.stdout.write(self.style.ERROR(f'✗ Ошибка отправки "{subject}": {str(send_error)}'))
                        
                except Exception as e:
                    failed_count += 1
                    error_msg = f'Error processing email {email_id}: {str(e)}'
                    logger.error(f"[{datetime.now()}] {error_msg}", exc_info=True)
                    self.stdout.write(self.style.ERROR(f'✗ Ошибка обработки письма: {str(e)}'))
            
            mail.close()
            mail.logout()
            
            summary_msg = f'Завершено: {forwarded_count} переслано, {failed_count} ошибок'
            logger.info(f"[{datetime.now()}] {summary_msg}")
            self.stdout.write(self.style.SUCCESS(f'\n{summary_msg}'))
            
        except Exception as e:
            error_msg = f'Критическая ошибка: {str(e)}'
            logger.error(f"[{datetime.now()}] {error_msg}", exc_info=True)
            self.stdout.write(self.style.ERROR(f'\n❌ {error_msg}'))
            if 'AUTHENTICATIONFAILED' in str(e) or 'Invalid credentials' in str(e):
                self.stdout.write(self.style.WARNING('\n💡 Подсказка: Проверьте App Password в settings.py'))
                self.stdout.write(self.style.WARNING('📖 См. инструкцию: EMAIL_SETUP_INSTRUCTIONS.md'))
    
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
