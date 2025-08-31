import json
from django.contrib import messages
from django.shortcuts import render, get_object_or_404, render,redirect
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import *
from .forms import *
from django.http import Http404, HttpResponseNotAllowed
from .models import PushSubscription, MessageRead, GroupMessage
from django.conf import settings
from django.views.decorators.http import require_POST
from .utils.push_notifications import notify_users_about_message, send_push_notification
from django.db import transaction
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
# from webpush import save_info
# Create your views here.



@login_required
def chat_view(request, chatroom_name='public-chat'):
    print(f" chat_view called with chatroom_name: {chatroom_name}")
    
    # Ensure public chat exists
    if chatroom_name == 'public-chat':
        chat_group, created = ChatGroup.objects.get_or_create(
            group_name='public-chat',
            defaults={'groupchat_name': None, 'is_private': False}
        )
        if created:
            print(" Created public chat group")
        else:
            print(" Public chat group already exists")
    else:
        try:
            chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
            print(f" Found chat group: {chat_group.group_name}")
        except:
            print(f" Chat group not found: {chatroom_name}")
            raise

    # Add user to public chat if not already a member (prevent duplicates)
    if chatroom_name == 'public-chat':
        if request.user not in chat_group.members.all():
            chat_group.members.add(request.user)
            print(f" Added {request.user.username} to public chat")
        else:
            print(f" {request.user.username} already in public chat")

    # Prevent infinite redirect loop for group chats
    if chatroom_name != 'public-chat' and chat_group.groupchat_name and request.user not in chat_group.members.all():
        chat_group.members.add(request.user)
        messages.success(request, "You have been added to this chat group.")

    chat_messages = chat_group.chat_messages.all()[:30]
    form = ChatmessageCreateForm()

    other_user = None
    if chat_group.is_private:
        if request.user not in chat_group.members.all():
            raise Http404()
        for member in chat_group.members.all():
            if member != request.user:
                other_user = member
                break

    if chat_group.groupchat_name:
        if request.user not in chat_group.members.all():
            if request.user.emailaddress_set.filter(verified=True).exists():
                chat_group.members.add(request.user)
            else:
                messages.warning(request, 'You need to verify your email to join the chat!')
                return redirect('profile-settings')

    # Handle HTMX form submission
    if request.htmx:
        form = ChatmessageCreateForm(request.POST)
        if form.is_valid():
            message = form.save(commit=False)
            message.author = request.user
            message.group = chat_group
            message.save()
            
            # Send push notifications for HTMX form submissions
            print(f"HTMX message created by {message.author.username} in group {message.group.group_name}")
            notify_users_about_message(message)
            
            context = {
                'message': message,
                'user': request.user
            }
            return render(request, 'a_rtchat/partials/chat_message_p.html', context)

    # If user is removed from a group then redirect them
    if request.user not in chat_group.members.all():
        if chatroom_name != 'public-chat':
            messages.error(request, "You have been removed from this group.")
            return redirect('chatroom', 'public-chat')

    context = {
        'chat_messages': chat_messages,
        'form': form,
        'other_user': other_user,
        'chatroom_name': chatroom_name,
        'chat_group': chat_group,
        'vapid_public_key': settings.WEBPUSH_SETTINGS['VAPID_PUBLIC_KEY'],
        'show_video_call': chat_group.is_private and chat_group.members.count() == 2,
    }   
    return render(request, 'a_rtchat/chat.html', context)



@login_required
def get_or_create_chatroom(request, username):
    if request.user.username == username:
        return redirect('home')
    
    other_user = User.objects.get(username = username)
    my_chatrooms = request.user.chat_groups.filter(is_private = True)

    if my_chatrooms.exists():
        for chatroom in my_chatrooms:
            if other_user in chatroom.members.all():
                chatroom = chatroom 
                break
            else:
                chatroom = ChatGroup.objects.create(is_private=True)
                chatroom.members.add(other_user, request.user)
        
    else:
        chatroom = ChatGroup.objects.create(is_private = True)
        chatroom.members.add(other_user, request.user)

    return redirect('chatroom', chatroom.group_name)



@login_required
def create_groupchat(request):
    form= NewGroupForm()

    if request.method =="POST":
        form = NewGroupForm(request.POST)
        if form.is_valid():
            new_groupchat = form.save(commit=False)
            new_groupchat.admin = request.user
            new_groupchat.save()
            new_groupchat.members.add(request.user)
            return redirect('chatroom', new_groupchat.group_name)
    context ={
        'form':form
    }
    return render(request,'a_rtchat/create_groupchat.html',context)



def chatroom_edit_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()

    form = ChatRoomEditForm(instance=chat_group)

    if request.method == "POST":
        form = ChatRoomEditForm(request.POST, instance=chat_group)
        if form.is_valid():
            form.save()

            remove_members = request.POST.getlist('remove_members')

            # Keep track of removed members for the success message
            removed_names = []

            for member_id in remove_members:
                member = User.objects.get(id=member_id)
                chat_group.members.remove(member)
                removed_names.append(member.username)

                # Send real-time notification via WebSocket
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    chat_group.group_name,
                    {
                        'type': 'member_removed_handler',
                        'removed_user_id': member.id,
                        'removed_username': member.username,
                    }
                )

                # Send a message to the removed member
                message = f"You have been removed from the {chat_group.group_name} group. You can join the public chat here: {reverse('chatroom', args=['public-chat'])}"
                
                if hasattr(member, 'userprofile'):
                    member.userprofile.send_message(message)

            if removed_names:
                messages.success(request, f"Successfully removed: {', '.join(removed_names)}")
            else:
                messages.success(request, "Chatroom updated")

            return redirect('chatroom', chatroom_name)

    context = {
        'form': form,
        'chat_group': chat_group
    }
    return render(request, 'a_rtchat/chatroom_edit.html', context)



@login_required
def chatroom_delete_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user != chat_group.admin:
        raise Http404()
    
    if request.method == "POST":
        chat_group.delete()
        messages.success(request, "Chatroom deleted")
        return redirect('home')
    return render(request, 'a_rtchat/chatroom_delete.html', {'chat_group': chat_group})



@login_required
def chatroom_leave_view(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    if request.user not in chat_group.members.all():
        raise Http404()
    
    if request.method == "POST":
        chat_group.members.remove(request.user)
        messages.success(request, 'You left the Chat')
        return redirect('home')
    return HttpResponseNotAllowed(['POST'])



def chat_file_upload(request, chatroom_name):
    chat_group = get_object_or_404(ChatGroup, group_name = chatroom_name)

    if request.htmx and request.FILES:
        file = request.FILES['file']
        message = GroupMessage.objects.create(
            file = file,
            author = request.user,
            group = chat_group,
        )   
        
        # Notify users about the new file message
        notify_users_about_message(message)
        
        channel_layer = get_channel_layer() 
        event = {
            'type':'message_handler',
            'message_id':message.id,
        }   
        async_to_sync(channel_layer.group_send)(
            chatroom_name, event 
        )
    return HttpResponse()



@csrf_exempt
def save_subscription(request):
    print("Save subscription view function called")

    if request.method == "POST":
        data = json.loads(request.body.decode("utf-8"))
        
        endpoint = data.get("endpoint", "")
        keys = data.get("keys", {})
        p256dh = keys.get("p256dh", "")
        auth = keys.get("auth", "")

        # Save subscription
        with transaction.atomic():
            obj, created = PushSubscription.objects.select_for_update().update_or_create(
                user=request.user,
                endpoint=endpoint,
                defaults={'p256dh': p256dh, 'auth': auth}
            )

        # Push subscription saved successfully - no welcome notification needed

        return JsonResponse({"status": "success"})

    return JsonResponse({"status": "failed"}, status=400)



@login_required
def test_push(request):
    if request.method != 'POST':
        return JsonResponse({"error": "Only POST requests allowed"}, status=405)
        
    payload = json.dumps({
        "title": "Test notification",
        "body": "Push is configured correctly.",
        "icon": "/static/images/ape1.jpg",
        "url": "/chat/room/public-chat/"
    })

    sent = 0
    failed = 0
    subscriptions = PushSubscription.objects.filter(user=request.user)
    
    print(f"Testing push for user {request.user.username}, found {subscriptions.count()} subscriptions")
    
    for sub in subscriptions:
        print(f"Sending test notification to subscription: {sub.endpoint[:50]}...")
        ok = send_push_notification(sub, payload)
        if ok:
            sent += 1
        else:
            failed += 1
            
    return JsonResponse({
        "attempted": sent + failed, 
        "sent": sent, 
        "failed": failed,
        "message": f"Test completed: {sent} sent, {failed} failed"
    })


@login_required
def upload_audio_message(request, group_name):
    import logging
    logger = logging.getLogger(__name__)
    logger.info(f"upload_audio_message called by user: {request.user}, group: {group_name}, method: {request.method}")

    if request.method != 'POST':
        logger.warning("upload_audio_message: Method not allowed")
        return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)
    
    chat_group = get_object_or_404(ChatGroup, group_name=group_name)
    

    audio_file = request.FILES.get('audio')
    if not audio_file:
        logger.warning("upload_audio_message: No audio file provided")
        return JsonResponse({'error': 'No audio file provided'}, status=400)
    
    # Create a new message
    message = GroupMessage.objects.create(
        author=request.user,
        group=chat_group,  
        body="" 
    )
    
    # Save the audio file
    filename = f"voice_message_{message.id}.mp3"
    message.file.save(filename, audio_file)
    message.save()
    
    # Notify users about the new message
    notify_users_about_message(message)
    
    # Send WebSocket event to all users in the chat
    channel_layer = get_channel_layer()
    event = {
        'type': 'message_handler',  
        'message_id': message.id,
    }
    
    async_to_sync(channel_layer.group_send)(
        group_name,  
        event
    )
    
    logger.info(f"upload_audio_message: Audio message saved with id {message.id}")
    return JsonResponse({'success': True, 'message_id': message.id})

@login_required
def check_membership(request, chatroom_name):
    """Check if the current user is a member of the specified chat group"""
    chat_group = get_object_or_404(ChatGroup, group_name=chatroom_name)
    
    is_member = request.user in chat_group.members.all()
    
    return JsonResponse({
        'is_member': is_member,
        'chatroom_name': chatroom_name
    })
