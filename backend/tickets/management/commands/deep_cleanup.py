from django.core.management.base import BaseCommand
from django.utils import timezone
from tickets.models import Ticket
import datetime
import os

class Command(BaseCommand):
    help = 'Deletes media files for tickets older than 6 months'

    def handle(self, *args, **kwargs):
        six_months_ago = timezone.now() - datetime.timedelta(days=180)
        old_tickets = Ticket.objects.filter(created_at__lt=six_months_ago)

        count = 0
        for ticket in old_tickets:
            # Delete media_before
            if ticket.media_before and os.path.isfile(ticket.media_before.path):
                os.remove(ticket.media_before.path)
                ticket.media_before = None # Optional: clear field reference
            
            # Delete media_after
            if ticket.media_after and os.path.isfile(ticket.media_after.path):
                os.remove(ticket.media_after.path)
                ticket.media_after = None
            
            ticket.save()
            count += 1

        self.stdout.write(self.style.SUCCESS(f'Successfully cleaned up media for {count} old tickets'))
