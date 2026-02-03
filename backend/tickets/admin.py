from django.contrib import admin
from django import forms
from .models import Corpus, User, Ticket, Feedback, SystemSetting, EmailTemplate, EmailLog

class SystemSettingForm(forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = '__all__'
        widgets = {
            'smtp_password': forms.PasswordInput(render_value=True),
        }

@admin.register(SystemSetting)
class SystemSettingAdmin(admin.ModelAdmin):
    form = SystemSettingForm
    list_display = ('__str__', 'email_from_address', 'smtp_host', 'notify_on_create', 'notify_on_complete')
    
    fieldsets = (
        ('Рабочее время', {
            'fields': ('work_start_time', 'work_end_time', 'allow_outside_working_hours')
        }),
        ('Настройки SMTP', {
            'fields': (
                ('email_from_name', 'email_from_address'),
                'smtp_host', 'smtp_port',
                'smtp_user', 'smtp_password',
                ('smtp_use_tls', 'smtp_use_ssl'),
            )
        }),
        ('Уведомления', {
            'fields': (
                'notify_on_create', 'notify_on_comment',
                'notify_on_complete', 'notify_on_overdue',
                'overdue_notification_email'
            )
        }),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)
    ordering = ('id',)

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'rating')
    list_filter = ('role',)
    search_fields = ('username', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'plain_password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('role', 'is_active', 'is_staff', 'is_superuser')}),
        ('Helpdesk Info', {'fields': ('rating',)}),
    )
    readonly_fields = ('plain_password',)

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'building', 'room', 'author', 'assigned_to', 'deadline', 'is_overdue')
    list_filter = ('status', 'building', 'created_at', 'is_overdue')
    search_fields = ('title', 'description', 'author__username', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at', 'taken_at', 'completed_at')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('ticket', 'user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')

@admin.register(EmailTemplate)
class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ('type', 'subject', 'is_active')
    list_editable = ('is_active',)

@admin.register(EmailLog)
class EmailLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'to_email', 'template_type', 'status')
    list_filter = ('status', 'template_type', 'created_at')
    readonly_fields = ('to_email', 'template_type', 'subject', 'status', 'error_message', 'created_at')
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
