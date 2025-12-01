from django.core.management.base import BaseCommand
from tickets.models import Ticket, Feedback, User

class Command(BaseCommand):
    help = 'Wipes all data (Tickets, Feedbacks) and non-default Users'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Starting full cleanup...'))

        # 1. Delete all Feedbacks
        deleted_feedbacks, _ = Feedback.objects.all().delete()
        self.stdout.write(f'Deleted {deleted_feedbacks} feedbacks.')

        # 2. Delete all Tickets
        deleted_tickets, _ = Ticket.objects.all().delete()
        self.stdout.write(f'Deleted {deleted_tickets} tickets.')

        # 3. Delete non-default Users
        # Preserved usernames: admin, teacher, helpdesk
        preserved_usernames = ['admin', 'teacher', 'helpdesk']
        
        users_to_delete = User.objects.exclude(username__in=preserved_usernames).exclude(is_superuser=True)
        count = users_to_delete.count()
        users_to_delete.delete()
        
        self.stdout.write(f'Deleted {count} users. Preserved: {preserved_usernames} and superusers.')

        self.stdout.write(self.style.SUCCESS('Full cleanup completed successfully.'))
