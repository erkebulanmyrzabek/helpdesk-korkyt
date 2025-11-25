import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from tickets.models import User

def create_users():
    if not User.objects.filter(username='admin').exists():
        User.objects.create_superuser('admin', 'admin@example.com', 'admin123', role='admin')
        print("Admin created")
    
    if not User.objects.filter(username='teacher').exists():
        User.objects.create_user('teacher', 'teacher@example.com', 'teacher123', role='teacher')
        print("Teacher created")
    
    if not User.objects.filter(username='helpdesk').exists():
        User.objects.create_user('helpdesk', 'helpdesk@example.com', 'helpdesk123', role='helpdesk')
        print("Helpdesk created")

if __name__ == '__main__':
    create_users()

