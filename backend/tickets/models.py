from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Учитель'),
        ('helpdesk', 'Хелпдеск'),
        ('admin', 'Админ'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='teacher')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('open', 'Открыта'),
        ('in_progress', 'В работе'),
        ('done', 'Выполнена'),
    )

    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание проблемы")
    corpus = models.CharField("Корпус", max_length=100)
    cabinet = models.CharField("Кабинет", max_length=50)
    
    # Attachments by Teacher
    image = models.ImageField("Фото", upload_to='tickets/images/', null=True, blank=True)
    video = models.FileField("Видео", upload_to='tickets/videos/', null=True, blank=True)
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='open')
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets', verbose_name="Автор")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="Исполнитель")
    
    # Report by Helpdesk
    report_image = models.ImageField("Фотоотчет", upload_to='tickets/reports/', null=True, blank=True)
    report_comment = models.TextField("Комментарий к выполнению", null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"#{self.id} - {self.title} ({self.get_status_display()})"
