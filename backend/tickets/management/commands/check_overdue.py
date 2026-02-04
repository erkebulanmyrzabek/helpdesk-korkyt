from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import Ticket

class Command(BaseCommand):
    help = 'Checks for overdue tickets'

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
            
        self.stdout.write(self.style.SUCCESS(f'Successfully marked {count} tickets as overdue'))
