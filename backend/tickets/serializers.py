from rest_framework import serializers
from .models import User, Ticket, Corpus, Feedback, SystemSetting, RegistrationRequest
from django.contrib.auth.hashers import make_password
import re

class CorpusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Corpus
        fields = ('id', 'name')
        read_only_fields = ('id',)

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'role', 'first_name', 'last_name', 'full_name', 'institute', 'position', 'rating', 'plain_password', 'date_joined')
        extra_kwargs = {
            'rating': {'read_only': True},
            'plain_password': {'read_only': True},
            'date_joined': {'read_only': True}
        }

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        request = self.context.get('request')
        # Only admins can see plain passwords
        if not (request and request.user.is_authenticated and request.user.role == 'admin'):
            ret.pop('plain_password', None)
        return ret

    def validate(self, data):
        role = data.get('role')
        if role == 'teacher':
            institute = data.get('institute')
            position = data.get('position')
            
            if not institute:
                raise serializers.ValidationError({"institute": "Для роли Учитель это поле обязательно."})
            if not position:
                raise serializers.ValidationError({"position": "Для роли Учитель это поле обязательно."})
            
            # Use choices from RegistrationRequest model
            valid_institutes = [choice[0] for choice in RegistrationRequest.INSTITUTE_CHOICES]
            if institute not in valid_institutes:
                raise serializers.ValidationError({"institute": f"Выберите институт из списка: {', '.join(valid_institutes)}"})
        
        return data
    
    def create(self, validated_data):
        password = validated_data.get('password')
        
        # Save plain password
        validated_data['plain_password'] = password
        
        user = User.objects.create_user(**validated_data)
        return user

class FeedbackSerializer(serializers.ModelSerializer):
    helper_username = serializers.ReadOnlyField(source='user.username')
    author_username = serializers.ReadOnlyField(source='ticket.author.username')
    ticket_title = serializers.ReadOnlyField(source='ticket.title')

    class Meta:
        model = Feedback
        fields = '__all__'
        read_only_fields = ('user', 'ticket', 'created_at')

class TicketSerializer(serializers.ModelSerializer):
    author_username = serializers.SerializerMethodField()
    author_full_name = serializers.SerializerMethodField()
    author_details = UserSerializer(source='author', read_only=True)
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')
    duration_minutes = serializers.SerializerMethodField()
    feedback = FeedbackSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'taken_at', 'started_at', 'completed_at', 'is_overdue', 'status')
    
    def get_duration_minutes(self, obj):
        return obj.get_duration()

    def get_author_username(self, obj):
        if obj.author:
            return obj.author.username
        return "удален"

    def get_author_full_name(self, obj):
        if obj.author:
            return obj.author.full_name or obj.author.get_full_name() or obj.author.username
        return obj.author_name_display or "Удаленный пользователь"

class SystemSettingSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemSetting
        fields = '__all__'

class RegistrationRequestSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = RegistrationRequest
        fields = ('id', 'full_name', 'username', 'password', 'institute', 'position', 'status', 'created_at')
        read_only_fields = ('id', 'status', 'created_at')

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Это имя пользователя уже занято.")
        if RegistrationRequest.objects.filter(username=value, status='PENDING').exists():
            raise serializers.ValidationError("Запрос с таким логином уже ожидает подтверждения.")
        if not re.match(r'^[a-zA-Z0-9]+$', value):
            raise serializers.ValidationError("Имя пользователя должно быть на английском языке и без пробелов.")
        if len(value) < 3:
            raise serializers.ValidationError("Минимум 3 символа.")
        return value

    def validate_full_name(self, value):
        # Allow Russian and Kazakh Cyrillic characters, spaces, hyphens
        kazakh_chars = "ӘәҒғҚқҢңӨөҰұҮүҺһІі"
        pattern = rf'^[а-яА-ЯёЁ{kazakh_chars}\s-]+$'
        if not re.match(pattern, value):
             raise serializers.ValidationError("Введите фамилию и имя на русском или казахском языке. Английские буквы запрещены.")
        return value

    def validate(self, data):
        password = data.get('password')
        full_name = data.get('full_name', '').lower()
        username = data.get('username', '').lower()

        if len(password) < 8:
            raise serializers.ValidationError({"password": "Пароль должен быть не менее 8 символов."})
        if not any(char.isdigit() for char in password):
            raise serializers.ValidationError({"password": "Пароль должен содержать цифры."})
        if not any(char.isupper() for char in password):
            raise serializers.ValidationError({"password": "Пароль должен содержать заглавные буквы."})
        if not any(char.islower() for char in password):
            raise serializers.ValidationError({"password": "Пароль должен содержать строчные буквы."})
        
        # Check if password contains parts of full name or username
        parts = full_name.split()
        for part in parts:
            if len(part) > 3 and part in password.lower():
                raise serializers.ValidationError({"password": "Пароль не должен содержать ваше имя или фамилию."})
        if username in password.lower():
            raise serializers.ValidationError({"password": "Пароль не должен содержать имя пользователя."})

        return data

    def create(self, validated_data):
        password = validated_data.pop('password')
        validated_data['plain_password'] = password # Save plain password
        validated_data['password'] = make_password(password) # Hash the password
        return super().create(validated_data)
