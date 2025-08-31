from channels.generic.websocket import WebsocketConsumer
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from asgiref.sync import async_to_sync
from django.contrib.auth import get_user_model
import json
from .models import *
from .models import ChatGroup
from .utils.push_notifications import notify_users_about_message
from channels.generic.websocket import AsyncWebsocketConsumer

User = get_user_model()

class ChatroomConsumer(WebsocketConsumer):
    def connect(self):
        # Resolve the lazy user
        user = self.scope['user']
        if not user.is_authenticated:
            self.close()
            return

        self.user = User.objects.get(id=user.id)  # Convert lazy user to real user

        self.chatroom_name = self.scope['url_route']['kwargs']['chatroom_name']
        self.chatroom = get_object_or_404(ChatGroup, group_name = self.chatroom_name)

        async_to_sync(self.channel_layer.group_add)(
            self.chatroom_name, self.channel_name
        )



        #add and update online users
        if self.user not in self.chatroom.users_online.all():
            self.chatroom.users_online.add(self.user)
            self.update_online_count()

        self.accept()



    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.chatroom_name, self.channel_name
        )
        
        #remove and update online users 

        if self.user in self.chatroom.users_online.all():
            self.chatroom.users_online.remove(self.user)
            self.update_online_count()
             


    def receive(self, text_data):
        text_data_json = json.loads(text_data)
        body = text_data_json['body']
        message = GroupMessage.objects.create(
            body = body,
            author = self.user,
            group = self.chatroom   
        )
        notify_users_about_message(message)

        event = {
            'type': 'message_handler',
            'message_id':message.id,
        }

        async_to_sync(self.channel_layer.group_send)(
            self.chatroom_name, event
        )


    def message_handler(self, event):
        message_id= event['message_id']
        message = GroupMessage.objects.get(id=message_id)
        users_online_ids = list(self.chatroom.users_online.values_list('id', flat=True))
        context = {
            'message': message,
            'user': self.user,
            'chat_group': self.chatroom,
            'users_online_ids': users_online_ids,
        }
        html = render_to_string("a_rtchat/partials/chat_message_p.html", context = context)
        self.send(text_data=html)

    def member_removed_handler(self, event):
        """Handle member removal notification"""
        removed_user_id = event.get('removed_user_id')
        removed_username = event.get('removed_username')
        
        # Check if this user is the one being removed
        if self.user.id == removed_user_id:
            # Send removal notification and close connection
            self.send(text_data=json.dumps({
                'type': 'member_removed',
                'message': f'You have been removed from {self.chatroom_name}',
                'redirect_url': '/chat/public-chat/'
            }))
            # Force disconnect after a short delay
            import threading
            threading.Timer(2.0, self.close).start()


    def update_online_count(self):
        online_count = self.chatroom.users_online.count()

        event={
            'type':'online_count_handler',
            'online_count': online_count    
        }

        async_to_sync(self.channel_layer.group_send)(self.chatroom_name, event)
    



    def online_count_handler(self, event): 
        online_count = event['online_count']
        context = {
            'online_count' : online_count,
            'chat_group' : self.chatroom
        }
        html = render_to_string("a_rtchat/partials/online_count.html", context)
        self.send(text_data = html)



    def audio_message_handler(self, event):
        """
        Handle audio messages specifically
        This is called when an audio message is uploaded via the HTTP endpoint
        """
        message_id = event['message_id']
        try:
            message = GroupMessage.objects.get(id=message_id)
            users_online_ids = list(self.chatroom.users_online.values_list('id', flat=True))
            context = {
                'message': message,
                'user': self.user,
                'chat_group': self.chatroom,
                'users_online_ids': users_online_ids,
                'is_audio': True  # Flag to indicate this is an audio message
            }
            html = render_to_string("a_rtchat/partials/chat_message_p.html", context=context)
            self.send(text_data=html)
        except GroupMessage.DoesNotExist:
            print(f"Audio message with ID {message_id} not found")




class OnlineStatusConsumer(WebsocketConsumer):

    def connect(self):
        self.user = self.scope['user']
        self.group_name = 'online-status'
        
        # Ensure the online-status group exists
        self.group, created = ChatGroup.objects.get_or_create(
            group_name='online-status',
            defaults={'groupchat_name': 'Global Online Status', 'is_private': False}
        )
        if created:
            print(" Created online-status group")
        
        if self.user not in self.group.users_online.all():
            self.group.users_online.add(self.user)
            
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )
            
        self.accept()
        self.online_status()
    


    def disconnect(self, close_code):
        if self.user in self.group.users_online.all():
            self.group.users_online.remove(self.user)

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )
        self.online_status()
    


    def online_status(self):
        event ={
            'type': 'online_status_handler'
        }
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, event
        )



    def online_status_handler(self, event):
        # Get all online users (including current user for total count)
        all_online_users = self.group.users_online.all()
        online_users = self.group.users_online.exclude(id=self.user.id)
        total_online_count = all_online_users.count()
        
        context = {
            'online_users': online_users,
            'online_count': total_online_count,  # Total count including current user
        }
        html = render_to_string("a_rtchat/partials/online_status.html", context=context)
        self.send(text_data=html)      




class CallConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = f"call_{self.room_name}"

        # Join the room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()
        print(f" WebSocket connected: {self.channel_name} joined {self.room_group_name}")



    async def disconnect(self, close_code):
        # Leave the room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
        print(f" WebSocket disconnected: {self.channel_name} left {self.room_group_name}")



    async def receive(self, text_data):
        data = json.loads(text_data)
        msg_type = data.get("type")
        
        print(f" Received from {self.channel_name}: {data}")

        # Relay the message to all others in the room (but not sender)
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "signal_message",
                "message": data,
                "sender": self.channel_name
            }
        )



    async def signal_message(self, event):
        # Only send to others, not back to sender
        if event["sender"] != self.channel_name:
            await self.send(text_data=json.dumps(event["message"]))