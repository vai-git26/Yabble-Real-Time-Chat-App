from allauth.account.forms import LoginForm
from captcha.fields import CaptchaField

class CustomLoginForm(LoginForm):
    captcha = CaptchaField()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)