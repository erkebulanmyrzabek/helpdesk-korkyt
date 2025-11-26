from rest_framework import serializers
from .models import User, Ticket, Corpus

class CorpusSerializer(serializers.ModelSerializer):
    class Meta:
        model = Corpus
        fields = ('id', 'name', 'number')
        read_only_fields = ('id',)

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    corpus_name = serializers.ReadOnlyField(source='corpus.name')
    corpus_id = serializers.PrimaryKeyRelatedField(queryset=Corpus.objects.all(), source='corpus', required=False, allow_null=True)

    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'role', 'first_name', 'last_name', 'corpus', 'corpus_id', 'corpus_name')
        extra_kwargs = {
            'corpus': {'read_only': True}
        }
    
    def create(self, validated_data):
        corpus = validated_data.pop('corpus', None)
        user = User.objects.create_user(**validated_data)
        if corpus:
            user.corpus = corpus
            user.save()
        return user

class TicketSerializer(serializers.ModelSerializer):
    author_username = serializers.ReadOnlyField(source='author.username')
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')
    corpus_name = serializers.ReadOnlyField(source='corpus.name')
    duration_minutes = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'started_at', 'completed_at')
    
    def get_duration_minutes(self, obj):
        return obj.get_duration()
    
    def to_internal_value(self, data):
        # Обрабатываем corpus_id из FormData
        if 'corpus_id' in data:
            # Преобразуем строку в число, если нужно
            corpus_id = data.get('corpus_id')
            if isinstance(corpus_id, str):
                try:
                    data = data.copy()  # Создаем копию, чтобы не изменять оригинал
                    data['corpus'] = int(corpus_id)
                except (ValueError, TypeError):
                    pass
            elif corpus_id is not None:
                data = data.copy()
                data['corpus'] = corpus_id
        return super().to_internal_value(data)
