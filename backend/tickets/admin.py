from django.contrib import admin
from .models import Corpus, User, Ticket, Feedback

@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ('name', 'number')
    search_fields = ('name',)
    ordering = ('number', 'name')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'corpus', 'is_checked_in', 'rating')
    list_filter = ('role', 'corpus', 'is_checked_in')
    search_fields = ('username', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password', 'plain_password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('role', 'corpus', 'is_active', 'is_staff', 'is_superuser')}),
        ('Helpdesk Info', {'fields': ('is_checked_in', 'rating')}),
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
