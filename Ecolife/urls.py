"""
URL configuration for Ecolife project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path
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
