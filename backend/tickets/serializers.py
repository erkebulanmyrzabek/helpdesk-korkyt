from rest_framework import serializers
from .models import User, Ticket

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'role', 'first_name', 'last_name')
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user

class TicketSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'started_at', 'completed_at')
    
    def get_duration_minutes(self, obj):
        return obj.get_duration()
