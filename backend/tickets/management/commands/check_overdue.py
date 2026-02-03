from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import Ticket, SystemSetting
from tickets.services.email_service import EmailService

class Command(BaseCommand):
    help = 'Checks for overdue tickets and sends notifications'

    def handle(self, *args, **kwargs):
        now = timezone.now()
        overdue_tickets = Ticket.objects.filter(
            deadline__lt=now,
            is_overdue=False
        ).exclude(status__in=['CLOSED', 'UNFIXABLE'])

        sys_settings = SystemSetting.get_settings()
        count = 0
        for ticket in overdue_tickets:
            ticket.is_overdue = True
            ticket.save()
            count += 1
            
            # Send email via Service
            context = {
                'ticket_id': ticket.id,
                'deadline': ticket.deadline.strftime('%d.%m.%Y %H:%M') if ticket.deadline else '-',
                'helper_name': (ticket.assigned_to.first_name + ' ' + ticket.assigned_to.last_name).strip() or ticket.assigned_to.username if ticket.assigned_to else 'Не назначен'
            }
            
            recipients = [sys_settings.overdue_notification_email]
            if ticket.assigned_to and ticket.assigned_to.email:
                recipients.append(ticket.assigned_to.email)
            
            EmailService.send_notification('ticket_overdue', context, recipients)

        self.stdout.write(self.style.SUCCESS(f'Successfully marked {count} tickets as overdue'))
