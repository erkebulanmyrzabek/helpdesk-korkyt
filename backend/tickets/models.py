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
    institute = models.CharField("Институт / подразделение", max_length=255, null=True, blank=True)
    position = models.CharField("Должность", max_length=255, null=True, blank=True)
    full_name = models.CharField("ФИО", max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"

class Ticket(models.Model):
    STATUS_CHOICES = (
        ('NEW', 'Новая'),
        ('IN_PROGRESS', 'В работе'),
        ('WAITING_FOR_PARTS', 'Ожидается запчасть'),
        ('CLOSED', 'Закрыта'),
        ('CANCELED', 'Отменена'),
    )

    title = models.CharField("Заголовок", max_length=200)
    description = models.TextField("Описание проблемы")
    
    # Location
    building = models.CharField("Корпус", max_length=100) # De-normalized
    room = models.CharField("Кабинет", max_length=50)
    
    # Attachments by Teacher
    media_before = models.FileField("Медиа (До)", upload_to='tickets/before/', null=True, blank=True)
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='NEW')
    
    author = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='created_tickets', verbose_name="Автор")
    author_name_display = models.CharField("Имя автора (отображение)", max_length=255, null=True, blank=True)
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_tickets', verbose_name="Исполнитель")
    
    # Report by Helpdesk
    media_after = models.ImageField("Фото (После)", upload_to='tickets/after/', null=True, blank=True)
    report_comment = models.TextField("Комментарий к выполнению", null=True, blank=True)
    parts_wait_reason = models.TextField("Причина ожидания запчастей", null=True, blank=True)
    
    # Timing fields
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    taken_at = models.DateTimeField("Взят в работу", null=True, blank=True)
    started_at = models.DateTimeField("Начало работы", null=True, blank=True) # Kept for legacy/stats if needed, or alias to taken_at
    completed_at = models.DateTimeField("Время завершения", null=True, blank=True)
    
    is_overdue = models.BooleanField("Просрочена", default=False)
    
    # Feature: User can hide ticket
    hidden_at_by_author = models.DateTimeField("Скрыто пользователем", null=True, blank=True)

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
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='feedbacks', verbose_name="Пользователь")
    rating = models.IntegerField("Оценка", choices=[(i, i) for i in range(1, 6)])
    comment = models.TextField("Комментарий", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    is_viewed_by_admin = models.BooleanField("Просмотрен администратором", default=False)

    class Meta:
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"

    def __str__(self):
        return f"Отзыв к заявке #{self.ticket.id} - {self.rating}"

class SystemSetting(models.Model):
    # Working Hours
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

class RegistrationRequest(models.Model):
    INSTITUTE_CHOICES = (
        ('Ректорат', 'Ректорат'),
        ('Институт педагогики и традиционного искусства', 'Институт педагогики и традиционного искусства'),
        ('Институт естествознания', 'Институт естествознания'),
        ('Инженерно-технологический институт', 'Инженерно-технологический институт'),
        ('Институт экономики и права', 'Институт экономики и права'),
        ('Гуманитарно-педагогический институт', 'Гуманитарно-педагогический институт'),
        ('Институт искусственного интеллекта', 'Институт искусственного интеллекта'),
    )

    STATUS_CHOICES = (
        ('PENDING', 'Ожидает решения'),
        ('APPROVED', 'Одобрено'),
        ('REJECTED', 'Отклонено'),
    )

    full_name = models.CharField("Фамилия и имя", max_length=255)
    username = models.CharField("Имя пользователя (Login)", max_length=150, unique=True)
    password = models.CharField("Хэш пароля", max_length=128) # Same length as Django default
    institute = models.CharField("Институт / подразделение", max_length=255, choices=INSTITUTE_CHOICES)
    position = models.CharField("Должность", max_length=255)
    plain_password = models.CharField("Пароль (raw)", max_length=255, null=True, blank=True)
    
    status = models.CharField("Статус", max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    is_viewed_by_admin = models.BooleanField("Просмотрен администратором", default=False)

    class Meta:
        verbose_name = "Запрос на регистрацию"
        verbose_name_plural = "Запросы на регистрацию"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} ({self.username}) - {self.get_status_display()}"
