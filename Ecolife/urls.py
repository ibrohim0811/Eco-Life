from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
import re
from django.contrib import admin
from django.urls import path, re_path
from eco.views import (
    EnteranceTemplateView, UserLoginView, MainTemplateView, user_out,
    custom_page_not_found, custom_server_error, custom_permission_denied,
    custom_bad_request
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", EnteranceTemplateView.as_view(), name='enterance'),
    path("login/", UserLoginView.as_view(), name='login'),
    path("logout/", user_out, name='logout'),
    path("app/", MainTemplateView.as_view(), name='main'),
]


handler404 = 'eco.views.custom_page_not_found'
handler500 = 'eco.views.custom_server_error'
handler403 = 'eco.views.custom_permission_denied'
handler400 = 'eco.views.custom_bad_request'

if not settings.DEBUG:
    # Production uchun (Static va Media)
    urlpatterns += [
        re_path(r'^static/(?P<path>.*)$', serve, {'document_root': settings.STATIC_ROOT}),
        re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
    ]
else:
    # Local (Development) uchun
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)