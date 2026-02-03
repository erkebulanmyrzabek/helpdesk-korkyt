from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
import os

class Corpus(models.Model):
    name = models.CharField("Название корпуса", max_length=100, unique=True)
    
    class Meta:
        verbose_name = "Корпус"
        verbose_name_plural = "Корпуса"
        ordering = ['id']
    
    def __str__(self):
        return self.name

class User(AbstractUser):
    ROLE_CHOICES = (
        ('teacher', 'Учитель'),
        ('helpdesk', 'Хелпдеск'),
        ('admin', 'Админ'),
    )
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='teacher')
    plain_password = models.CharField("Пароль (raw)", max_length=255, null=True, blank=True)
    rating = models.FloatField("Рейтинг", default=0.0)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'Новая'),
        ('IN_PROGRESS', 'В работе'),
        ('WAITING_APPROVE', 'Ожидает подтверждения'),
        ('CLOSED', 'Закрыта'),
        ('UNFIXABLE', 'Неисправима'),
    )

    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание проблемы")
    
    # Location
    building = models.CharField("Корпус", max_length=100) # De-normalized
    room = models.CharField("Кабинет", max_length=50)
    
    # Attachments by Teacher
    media_before = models.FileField("Медиа (До)", upload_to='tickets/before/', null=True, blank=True)
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_tickets', verbose_name="Автор")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="Исполнитель")
    
    # Report by Helpdesk
    media_after = models.ImageField("Фото (После)", upload_to='tickets/after/', null=True, blank=True)
    report_comment = models.TextField("Комментарий к выполнению", null=True, blank=True)
    
    # Timing fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    taken_at = models.DateTimeField("Взят в работу", null=True, blank=True)
    started_at = models.DateTimeField("Начало работы", null=True, blank=True) # Kept for legacy/stats if needed, or alias to taken_at
    completed_at = models.DateTimeField("Время завершения", null=True, blank=True)
    deadline = models.DateTimeField("Дедлайн", null=True, blank=True)
    
    is_overdue = models.BooleanField("Просрочена", default=False)

    def __str__(self):
        return f"#{self.id} - {self.title} ({self.get_status_display()})"
    
    def get_duration(self):
        """Возвращает длительность выполнения в минутах"""
        if self.taken_at and self.completed_at:
            delta = self.completed_at - self.taken_at
            return int(delta.total_seconds() / 60)
        return None

class Feedback(models.Model):
    ticket = models.OneToOneField(Ticket, on_delete=models.CASCADE, related_name='feedback', verbose_name="Заявка")
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='feedbacks', verbose_name="Пользователь")
    rating = models.IntegerField("Оценка", choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField("Комментарий", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв к заявке #{self.ticket.id} - {self.rating}"

class SystemSetting(models.Model):
    work_start_time = models.TimeField("Начало работы", default="09:00")
    work_end_time = models.TimeField("Конец работы", default="18:00")
    allow_outside_working_hours = models.BooleanField("Разрешить заявки вне рабочего времени", default=False)

    class Meta:
        verbose_name = "Настройка системы"
        verbose_name_plural = "Настройки системы"

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return "Настройки системы"
