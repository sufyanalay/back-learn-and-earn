from rest_framework import viewsets, generics, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django.db.models import Q
from .models import ChatRoom, Message, MessageAttachment
from .serializers import ChatRoomSerializer, ChatRoomDetailSerializer, MessageSerializer, MessageAttachmentSerializer


class ChatRoomViewSet(viewsets.ModelViewSet):
    serializer_class = ChatRoomSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        # Only return chat rooms where the current user is a participant
        return ChatRoom.objects.filter(participants=self.request.user)
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ChatRoomDetailSerializer
        return ChatRoomSerializer
    
    def perform_create(self, serializer):
        # Ensure current user is a participant
        chat_room = serializer.save()
        if self.request.user not in chat_room.participants.all():
            chat_room.participants.add(self.request.user)
    
    @action(detail=False, methods=['get'])
    def find_or_create(self, request):
        other_user_id = request.query_params.get('user_id')
        if not other_user_id:
            return Response(
                {"error": "user_id query parameter is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Find existing chat room with just these two participants
        user_rooms = ChatRoom.objects.filter(participants=request.user)
        other_user_rooms = ChatRoom.objects.filter(participants=other_user_id)
        
        # Find intersection of both users' rooms
        common_rooms = user_rooms.intersection(other_user_rooms)
        
        # Further filter to find rooms with exactly 2 participants
        for room in common_rooms:
            if room.participants.count() == 2:
                serializer = self.get_serializer(room)
                return Response(serializer.data)
        
        # No existing room found, create a new one
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        try:
            other_user = User.objects.get(id=other_user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User with provided ID does not exist"},
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_room = ChatRoom.objects.create()
        new_room.participants.add(request.user, other_user)
        
        serializer = self.get_serializer(new_room)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MessageCreateView(generics.CreateAPIView):
    queryset = Message.objects.all()
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        room = get_object_or_404(ChatRoom, pk=self.kwargs.get('room_id'))
        
        # Ensure user is a participant in the chat room
        if self.request.user not in room.participants.all():
            self.permission_denied(
                self.request, 
                message="You are not a participant in this chat room"
            )
        
        message = serializer.save(sender=self.request.user, room=room)
        
        # Handle file attachments if any
        files = self.request.FILES.getlist('files', [])
        for file in files:
            MessageAttachment.objects.create(message=message, file=file)


class MessageListView(generics.ListAPIView):
    serializer_class = MessageSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        room = get_object_or_404(ChatRoom, pk=self.kwargs.get('room_id'))
        
        # Ensure user is a participant in the chat room
        if self.request.user not in room.participants.all():
            self.permission_denied(
                self.request, 
                message="You are not a participant in this chat room"
            )
        
        # Mark all unread messages from others as read
        unread_messages = room.messages.filter(
            ~Q(sender=self.request.user),
            is_read=False
        )
        unread_messages.update(is_read=True)
        
        return room.messages.all().order_by('-created_at')