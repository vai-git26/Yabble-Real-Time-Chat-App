from django.contrib import admin
from django.urls import path, include
from django.conf.urls.static import static
from django.conf import settings
from a_users.views import profile_view
from a_home.views import *
from django.views.generic import TemplateView

urlpatterns = [

    path('admin/', admin.site.urls),    
    path('accounts/', include('allauth.urls')),
    path('', include('a_rtchat.urls')),
    path('profile/', include('a_users.urls')),
    path('@<username>/', profile_view, name="profile"),
    path('service-worker.js', TemplateView.as_view(template_name='service-worker.js', content_type='application/javascript')),
    path('captcha/', include('captcha.urls')), 
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
