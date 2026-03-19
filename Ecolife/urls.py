from django.contrib import admin
from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from eco.views import (
    EnteranceTemplateView, UserLoginView, MainTemplateView, user_out,
    custom_page_not_found, custom_server_error, custom_permission_denied,
    custom_bad_request, check_notifications, groq_chat, SettingsTemplateView, check_username, ProfileSettingsView
)

urlpatterns = [
    path("only-ibrohim-can-enter/", admin.site.urls),
    path("", EnteranceTemplateView.as_view(), name='enterance'),
    path("login/", UserLoginView.as_view(), name='login'),
    path("logout/", user_out, name='logout'),
    path("app/", MainTemplateView.as_view(), name='main'),
    path('api/check-notifications/', check_notifications, name='check_notifications'),
    path('settings/', SettingsTemplateView.as_view(), name='settings'),
    path('api/chat/', groq_chat, name='groq_chat'),
    path('check-username/', check_username, name='check_username'),
    path('profile-settings/', ProfileSettingsView.as_view(), name='profile_settings'),
    
    ]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    

handler404 = 'eco.views.custom_page_not_found'
handler500 = 'eco.views.custom_server_error'
handler403 = 'eco.views.custom_permission_denied'
handler400 = 'eco.views.custom_bad_request'
