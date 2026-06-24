from django.urls import path
from .views import (
    home,
    register_view,
    login_view,
    logout_view,
    history_view,
    export_csv,
    MailboxAPIView
)

urlpatterns = [

    # Home Page
    path('', home, name='home'),

    # Authentication
    path('register/', register_view, name='register'),
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Email History Dashboard
    path('history/', history_view, name='history'),

    # Export History CSV
    path('export-csv/', export_csv, name='export_csv'),

    # Email Sending API
    path('send-mail/', MailboxAPIView.as_view(), name='send-mail'),
]