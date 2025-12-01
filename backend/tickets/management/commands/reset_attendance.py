from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model

class Command(BaseCommand):
    help = 'Resets is_checked_in status for all helpdesk users to False'

    def handle(self, *args, **options):
        User = get_user_model()
        # Filter users with role='helpdesk' who are currently checked in
        users_to_reset = User.objects.filter(role='helpdesk', is_checked_in=True)
        count = users_to_reset.count()
        
        if count > 0:
            users_to_reset.update(is_checked_in=False)
            self.stdout.write(self.style.SUCCESS(f'Successfully reset attendance for {count} users'))
        else:
            self.stdout.write(self.style.SUCCESS('No users found to reset'))
