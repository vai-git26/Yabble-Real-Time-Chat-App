from django.db import models
from django.contrib.auth.models import User
from django.db.models.fields import related
import shortuuid
import os


# Create your models here.
class ChatGroup(models.Model):
    group_name = models.CharField(max_length=128, unique=True, blank=True)
    groupchat_name = models.CharField(max_length=128, null=True, blank=True)
    admin = models.ForeignKey(User, related_name='groupchats', blank=True, null=True, on_delete=models.SET_NULL)
    users_online = models.ManyToManyField(User, related_name = 'online_in_groups', blank=True)
    members = models.ManyToManyField(User, related_name='chat_groups', blank=True)
    is_private = models.BooleanField(default=False)


    def __str__(self):
        return self.group_name
    
    def save(self, *args, **kwargs):
        if not self.group_name:
            self.group_name = shortuuid.uuid()
        super().save(*args, **kwargs)


class GroupMessage(models. Model):
    group = models.ForeignKey(ChatGroup, related_name='chat_messages', on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    body = models.CharField(max_length = 300, blank=True, null=True)
    file= models.FileField(upload_to ='files/', blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    
    @property
    def filename(self):
        if self.file:
            return os.path.basename(self.file.name)
        else:
            return None


    def __str__(self):
        if self.body:
            return f'{self.author.username} : {self.body}'
        elif self.file:
            return f'{self.author.username} : {self.filename}'
        else:
            return f'{self.author.username} : [No content]'

    class Meta:
        ordering = ['-created'] 


    @property
    def is_image(self):
        if self.filename.lower().endswith(('.jpg', '.jpeg','.png','.gif','.svg','.webp')):  
            return True
        else:
            return False
        
    @property
    def is_audio(self):
        if not self.file:
            return False
        filename = self.file.name.lower()
        return filename.endswith('.webm') or filename.endswith('.mp3') or filename.endswith('.wav')



class PushSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='push_subscriptions')
    endpoint = models.URLField(max_length=500)
    p256dh = models.CharField(max_length=255)  # Encryption key
    auth = models.CharField(max_length=255)    # Authentication secret
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"PushSubscription for {self.user.username}"


class MessageRead(models.Model):
    message = models.ForeignKey('GroupMessage', related_name='reads', on_delete=models.CASCADE)
    user = models.ForeignKey(User, related_name='message_reads', on_delete=models.CASCADE)
    read_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('message', 'user')

    def __str__(self) -> str:
        return f"{self.user.username} read {self.message_id}"
    




class Message(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='chat_files/', blank=True, null=True)
    voice = models.FileField(upload_to='voice_messages/', blank=True, null=True)   # <- new
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender.username} - {self.text}"
