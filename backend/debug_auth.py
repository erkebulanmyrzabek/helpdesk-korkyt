import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth import authenticate
from tickets.models import User

def debug_auth():
    users = ['admin', 'teacher', 'helpdesk']
    for username in users:
        try:
            user = User.objects.get(username=username)
            print(f"User: {username}, Active: {user.is_active}, Role: {user.role}, Has Password: {bool(user.password)}")
            
            # Try to authenticate
            auth_user = authenticate(username=username, password=f"{username}123")
            print(f"Authentication for {username}: {'SUCCESS' if auth_user else 'FAILED'}")
            
            if not auth_user:
                # Check if password matches manually
                print(f"Manual check check_password: {user.check_password(f'{username}123')}")
                
        except User.DoesNotExist:
            print(f"User {username} does not exist")

if __name__ == '__main__':
    debug_auth()
