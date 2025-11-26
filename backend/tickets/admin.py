from django.contrib import admin
from .models import Corpus, User, Ticket

@admin.register(Corpus)
class CorpusAdmin(admin.ModelAdmin):
    list_display = ('name', 'number')
    search_fields = ('name',)
    ordering = ('number', 'name')

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'first_name', 'last_name', 'role', 'corpus')
    list_filter = ('role', 'corpus')
    search_fields = ('username', 'first_name', 'last_name')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Permissions', {'fields': ('role', 'corpus', 'is_active', 'is_staff', 'is_superuser')}),
    )

@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ('id', 'title', 'status', 'corpus', 'cabinet', 'author', 'assigned_to', 'created_at')
    list_filter = ('status', 'corpus', 'created_at')
    search_fields = ('title', 'description', 'author__username', 'assigned_to__username')
    readonly_fields = ('created_at', 'updated_at', 'started_at', 'completed_at')
