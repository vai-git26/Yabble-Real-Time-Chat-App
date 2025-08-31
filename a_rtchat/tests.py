from django.test import TestCase

# Create your tests here.
from . import store_voice_message

user_id = 1
group_id = 1
message = b'audio data'  # replace with actual audio data

filepath = store_voice_message(user_id, group_id, message)
print(filepath)