from django.conf.urls import url
from django.urls import path

from login import views
from django.contrib.auth import views as auth_views
from .views import *

urlpatterns = [
    path('register/', Register.as_view(), name='register'),
    path('login/', Login.as_view(), name='login'),
    path('mailrestore/', RestoreWithEmail.as_view(), name='mailRestore'),
    path('newPassword/', RestorePassword.as_view(), name='newPassword'),

    url(r'^activate/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.activate, name='activate'),
    url(r'^restore/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',
        views.restore_password, name='restore'),
]
