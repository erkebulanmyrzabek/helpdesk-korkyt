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
    # Working Hours
    work_start_time = models.TimeField("Начало работы", default="09:00")
    work_end_time = models.TimeField("Конец работы", default="18:00")
    allow_outside_working_hours = models.BooleanField("Разрешить заявки вне рабочего времени", default=False)

    # SMTP Settings
    email_from_name = models.CharField("Имя отправителя", max_length=100, default="HelpDesk")
    email_from_address = models.EmailField("Email отправителя", default="erkemyrzaa@gmail.com")
    smtp_host = models.CharField("SMTP Host", max_length=100, default="smtp.gmail.com")
    smtp_port = models.IntegerField("SMTP Port", default=587)
    smtp_user = models.CharField("SMTP User", max_length=100, default="erkemyrzaa@gmail.com")
    smtp_password = models.CharField("SMTP Password", max_length=100, blank=True)
    smtp_use_tls = models.BooleanField("Использовать TLS", default=True)
    smtp_use_ssl = models.BooleanField("Использовать SSL", default=False)
    
    # Notification Toggles
    notify_on_create = models.BooleanField("Уведомлять о новой заявке", default=True)
    notify_on_comment = models.BooleanField("Уведомлять о новом комментарии", default=True)
    notify_on_complete = models.BooleanField("Уведомлять о завершении заявки", default=True)
    notify_on_overdue = models.BooleanField("Уведомлять о просрочке", default=True)
    
    # Admin email for overdue notifications
    overdue_notification_email = models.EmailField("Email для уведомлений о просрочке", default="myrzabekerkebulanakt@gmail.com")

    class Meta:
        verbose_name = "Настройка системы"
        verbose_name_plural = "Настройки системы"

    @classmethod
    def get_settings(cls):
        obj, created = cls.objects.get_or_create(id=1)
        return obj

    def __str__(self):
        return "Настройки системы"

class EmailTemplate(models.Model):
    TYPE_CHOICES = (
        ('new_ticket', 'Новая заявка'),
        ('comment_added', 'Добавлен комментарий'),
        ('ticket_completed', 'Заявка выполнена'),
        ('ticket_overdue', 'Заявка просрочена'),
    )
    
    type = models.CharField("Тип уведомления", max_length=50, choices=TYPE_CHOICES, unique=True)
    subject = models.CharField("Тема письма", max_length=255)
    body = models.TextField("Текст письма (поддерживает HTML)")
    is_active = models.BooleanField("Активен", default=True)
    
    class Meta:
        verbose_name = "Шаблон письма"
        verbose_name_plural = "Шаблоны писем"

    def __str__(self):
        return self.get_type_display()

class EmailLog(models.Model):
    to_email = models.EmailField("Кому")
    template_type = models.CharField("Тип шаблона", max_length=50)
    subject = models.CharField("Тема", max_length=255)
    status = models.CharField("Статус", max_length=20, choices=(('success', 'Успешно'), ('failed', 'Ошибка')))
    error_message = models.TextField("Ошибка", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = "Лог письма"
        verbose_name_plural = "Логи писем"
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.created_at} - {self.to_email} - {self.status}"
