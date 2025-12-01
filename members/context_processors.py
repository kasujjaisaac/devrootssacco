# core/context_processors.py
from .models import AdminNotification

def admin_notifications(request):
    context = {}
    # only show for authenticated admin users
    if request.user.is_authenticated and (request.user.is_superuser or request.user.groups.filter(name='Admin').exists()):
        unread_count = AdminNotification.objects.filter(is_read=False).count()
        latest_notifications = AdminNotification.objects.all()[:7]  # show latest 7
        context = {
            'admin_unread_count': unread_count,
            'admin_latest_notifications': latest_notifications
        }
    return context
