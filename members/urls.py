from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('login/', views.member_login, name='member_login'),
    path('dashboard/', views.member_dashboard, name='dashboard'),
    path('logout/', views.member_logout, name='member_logout'),
    path('change-password/', views.change_password, name='change_password'),
    path('profile/', views.member_profile, name='profile'),
    path('loans/', views.member_loans, name='loans'),
    path('savings/', views.member_savings, name='savings'),          
    path('transactions/', views.member_transactions, name='transactions'), 
    path('support/', views.member_support, name='support'),

    # Admin member management
    path('add/', views.add_member, name='add_member'),
    path('list/', views.members_list, name='members_list'),
]

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
