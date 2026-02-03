from celery import shared_task
from tickets.services.email_service import EmailService

@shared_task
def send_email_task(template_type, context_data, recipients):
    """
    Celery task to send emails asynchronously.
    """
    return EmailService.process_send(template_type, context_data, recipients)
