from django.core.mail import get_connection, EmailMessage
from django.template import Template, Context
from tickets.models import SystemSetting, EmailTemplate, EmailLog
import logging

logger = logging.getLogger(__name__)

class EmailService:
    @staticmethod
    def send_notification(template_type, context_data, recipients):
        """
        Main entry point for sending notifications.
        This should be called from views/commands.
        It checks if notification is enabled and then enqueues the task.
        """
        try:
            settings = SystemSetting.get_settings()
            
            # Check global toggle for this type
            notify_map = {
                'new_ticket': settings.notify_on_create,
                'comment_added': settings.notify_on_comment,
                'ticket_completed': settings.notify_on_complete,
                'ticket_overdue': settings.notify_on_overdue,
            }
            
            if not notify_map.get(template_type, True):
                return False

            # Enqueue the task
            from tickets.tasks import send_email_task
            try:
                send_email_task.delay(template_type, context_data, recipients)
            except Exception as e:
                logger.error(f"Celery error: Could not enqueue email task ({template_type}). Broker might be down: {e}")
                # Optional: Fallback to sync send if broker is down? 
                # For now, we just log and continue to avoid 500 errors.
            
            return True
        except Exception as e:
            logger.error(f"Critical error in send_notification: {e}")
            return False

    @staticmethod
    def process_send(template_type, context_data, recipients):
        """
        The actual sending logic, used by the Celery task.
        Reads SMTP settings from DB.
        """
        settings = SystemSetting.get_settings()
        
        try:
            template = EmailTemplate.objects.get(type=template_type, is_active=True)
        except EmailTemplate.DoesNotExist:
            logger.warning(f"Email template {template_type} not found or inactive")
            return False

        # Render subject and body
        subject = Template(template.subject).render(Context(context_data))
        body = Template(template.body).render(Context(context_data))

        # Setup custom connection
        connection = get_connection(
            host=settings.smtp_host,
            port=settings.smtp_port,
            username=settings.smtp_user,
            password=settings.smtp_password,
            use_tls=settings.smtp_use_tls,
            use_ssl=settings.smtp_use_ssl,
            timeout=10
        )

        from_email = f"{settings.email_from_name} <{settings.email_from_address}>"
        
        results = []
        for recipient in recipients:
            msg = EmailMessage(
                subject=subject,
                body=body,
                from_email=from_email,
                to=[recipient],
                connection=connection
            )
            msg.content_subtype = "html"  # Support HTML in body
            
            try:
                msg.send()
                EmailLog.objects.create(
                    to_email=recipient,
                    template_type=template_type,
                    subject=subject,
                    status='success'
                )
                results.append(True)
            except Exception as e:
                logger.error(f"Failed to send email to {recipient}: {e}")
                EmailLog.objects.create(
                    to_email=recipient,
                    template_type=template_type,
                    subject=subject,
                    status='failed',
                    error_message=str(e)
                )
                results.append(False)
        
        return all(results)
