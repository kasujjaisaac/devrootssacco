from django.contrib import admin
from django.urls import path, include
from django.shortcuts import redirect

urlpatterns = [
    path('admin/', admin.site.urls),

    # Members app URLs
    path('members/', include('members.urls')),

    # Default redirect to member login (optional)
    path('', lambda request: redirect('member_login')),
]

