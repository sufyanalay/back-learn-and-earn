import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from .models import ChatRoom, Message, MessageAttachment

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_id = self.scope['url_route']['kwargs']['room_id']
        self.room_group_name = f'chat_{self.room_id}'
        
        # Add user to room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        # Check if user is a participant in the chat room
        user = self.scope['user']
        is_participant = await self.is_room_participant(user, self.room_id)
        
        if not is_participant:
            await self.close()
            return
        
        await self.accept()
    
    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type', 'message')
        
        if message_type == 'message':
            message = data.get('message', '')
            
            # Save message to database
            user = self.scope['user']
            saved_message = await self.save_message(user.id, self.room_id, message)
            
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': saved_message['id'],
                        'content': saved_message['content'],
                        'sender_id': saved_message['sender_id'],
                        'sender_name': saved_message['sender_name'],
                        'sender_role': saved_message['sender_role'],
                        'created_at': saved_message['created_at'].isoformat(),
                        'is_read': saved_message['is_read']
                    }
                }
            )
        
        elif message_type == 'read':
            # Mark messages as read
            message_ids = data.get('message_ids', [])
            if message_ids:
                await self.mark_messages_read(message_ids)
                
                # Notify other users that messages have been read
                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'messages_read',
                        'message_ids': message_ids,
                        'reader_id': self.scope['user'].id
                    }
                )
    
    # Receive message from room group
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'message',
            'message': event['message']
        }))
    
    # Receive message read notification from room group
    async def messages_read(self, event):
        # Send read status to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'read',
            'message_ids': event['message_ids'],
            'reader_id': event['reader_id']
        }))
    
    @database_sync_to_async
    def is_room_participant(self, user, room_id):
        if not user.is_authenticated:
            return False
        
        try:
            room = ChatRoom.objects.get(id=room_id)
            return room.participants.filter(id=user.id).exists()
        except ChatRoom.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, user_id, room_id, content):
        user = User.objects.get(id=user_id)
        room = ChatRoom.objects.get(id=room_id)
        
        message = Message.objects.create(
            room=room,
            sender=user,
            content=content
        )
        
        return {
            'id': message.id,
            'content': message.content,
            'sender_id': message.sender.id,
            'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
            'sender_role': message.sender.role,
            'created_at': message.created_at,
            'is_read': message.is_read
        }
    
    @database_sync_to_async
    def mark_messages_read(self, message_ids):
        Message.objects.filter(id__in=message_ids).update(is_read=True)