from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageAttachment

User = get_user_model()


class MessageAttachmentSerializer(serializers.ModelSerializer):
    class Meta:
        model = MessageAttachment
        fields = ('id', 'file', 'uploaded_at')


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.SerializerMethodField()
    sender_role = serializers.SerializerMethodField()
    attachments = MessageAttachmentSerializer(many=True, read_only=True)
    
    class Meta:
        model = Message
        fields = ('id', 'room', 'sender', 'sender_name', 'sender_role', 'content', 'created_at', 'is_read', 'attachments')
        read_only_fields = ('sender', 'created_at', 'is_read')
    
    def get_sender_name(self, obj):
        return f"{obj.sender.first_name} {obj.sender.last_name}"
    
    def get_sender_role(self, obj):
        return obj.sender.role


class ChatRoomSerializer(serializers.ModelSerializer):
    participants = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=User.objects.all()
    )
    participant_details = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()
    
    class Meta:
        model = ChatRoom
        fields = ('id', 'participants', 'participant_details', 'last_message', 'created_at')
        read_only_fields = ('created_at',)
    
    def get_participant_details(self, obj):
        return [
            {
                'id': user.id,
                'name': f"{user.first_name} {user.last_name}",
                'email': user.email,
                'role': user.role
            }
            for user in obj.participants.all()
        ]
    
    def get_last_message(self, obj):
        last_message = obj.messages.order_by('-created_at').first()
        if last_message:
            return {
                'content': last_message.content,
                'sender': last_message.sender.id,
                'sender_name': f"{last_message.sender.first_name} {last_message.sender.last_name}",
                'created_at': last_message.created_at,
                'is_read': last_message.is_read
            }
        return None
    
    def validate_participants(self, value):
        # Ensure the current user is included in participants
        if self.context['request'].user not in value:
            value.append(self.context['request'].user)
        
        # Ensure there are at least 2 participants
        if len(value) < 2:
            raise serializers.ValidationError("A chat room must have at least 2 participants")
        
        return value


class ChatRoomDetailSerializer(ChatRoomSerializer):
    messages = MessageSerializer(many=True, read_only=True)
    
    class Meta(ChatRoomSerializer.Meta):
        fields = ChatRoomSerializer.Meta.fields + ('messages',)