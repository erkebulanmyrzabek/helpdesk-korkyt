from rest_framework import serializers
from .models import User, Ticket, Corpus, Feedback

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
        fields = ('id', 'username', 'email', 'password', 'role', 'first_name', 'last_name', 'corpus', 'corpus_id', 'corpus_name', 'is_checked_in', 'rating', 'plain_password')
        extra_kwargs = {
            'corpus': {'read_only': True},
            'rating': {'read_only': True},
            'plain_password': {'read_only': True}
        }
    
    def create(self, validated_data):
        corpus = validated_data.pop('corpus', None)
        password = validated_data.get('password')
        
        # Save plain password
        validated_data['plain_password'] = password
        
        user = User.objects.create_user(**validated_data)
        if corpus:
            user.corpus = corpus
            user.save()
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
    author_username = serializers.ReadOnlyField(source='author.username')
    assigned_to_username = serializers.ReadOnlyField(source='assigned_to.username')
    duration_minutes = serializers.SerializerMethodField()
    feedback = FeedbackSerializer(read_only=True)

    class Meta:
        model = Ticket
        fields = '__all__'
        read_only_fields = ('author', 'created_at', 'updated_at', 'taken_at', 'started_at', 'completed_at', 'deadline', 'is_overdue', 'status')
    
    def get_duration_minutes(self, obj):
        return obj.get_duration()
    
    def to_representation(self, instance):
        data = super().to_representation(instance)
        request = self.context.get('request')
        
        # Masking logic for Helpdesk
        if request and request.user.role == 'helpdesk':
            # If ticket is NOT taken by this user, mask the room
            if instance.assigned_to != request.user:
                 data['room'] = "*****"
        
        return data
