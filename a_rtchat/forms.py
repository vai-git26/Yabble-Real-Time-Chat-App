from django.forms import ModelForm, widgets
from django import forms
from .models import GroupMessage, ChatGroup


class ChatmessageCreateForm(ModelForm):
    class Meta:
        model = GroupMessage
        fields = ['body']
        widgets = {
            'body': forms.TextInput(attrs={
                'placeholder': 'Add message...',
                'class': 'p-2 text-black',
                'maxlength': '300',
                'autofocus': True
                # Do NOT add 'name': 'body' — Django sets this automatically
            }),
        }


class NewGroupForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets = {
            'groupchat_name': forms.TextInput(attrs={
                'placeholder': 'Add name...',
                'class': 'p-4 text-black',
                'maxlength': '300',
                'autofocus': True,
            }),
        }


class ChatRoomEditForm(ModelForm):
    class Meta:
        model = ChatGroup
        fields = ['groupchat_name']
        widgets = {
            'groupchat_name': forms.TextInput(attrs={
                'class': 'p-4 text-xl font-bold mb-4',
                'maxlength':'300',
            }),
        }   
