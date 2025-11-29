from django.core.management.base import BaseCommand
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
from tickets.models import Ticket

class Command(BaseCommand):
    help = 'Checks for overdue tickets and sends notifications'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        overdue_tickets = Ticket.objects.filter(
            deadline__lt=now,
            is_overdue=False
        ).exclude(status__in=['CLOSED', 'UNFIXABLE'])

        count = 0
        for ticket in overdue_tickets:
            ticket.is_overdue = True
            ticket.save()
            count += 1
            
            # Send email
            try:
                subject = f'ПРОСРОЧЕНО: Заявка #{ticket.id}'
                message = f"Заявка #{ticket.id} просрочена.\nДедлайн: {ticket.deadline}\nИсполнитель: {ticket.assigned_to}"
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    [settings.FORWARD_TO_EMAIL], # Send to Admin/Helpdesk email
                    fail_silently=True
                )
            except Exception:
                pass

        self.stdout.write(self.style.SUCCESS(f'Successfully marked {count} tickets as overdue'))
