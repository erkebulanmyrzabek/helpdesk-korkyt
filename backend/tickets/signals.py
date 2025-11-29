from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Ticket
import os

@receiver(post_save, sender=Ticket)
def delete_files_on_close(sender, instance, created, **kwargs):
    if instance.status == 'CLOSED':
        # Delete media_before
        if instance.media_before:
            if os.path.isfile(instance.media_before.path):
                os.remove(instance.media_before.path)
                # Optional: instance.media_before = None; instance.save() 
                # But be careful of recursion. Better to just delete file.
        
        # Delete media_after
        if instance.media_after:
            if os.path.isfile(instance.media_after.path):
                os.remove(instance.media_after.path)
