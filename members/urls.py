from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

# ============================================================
#                      MEMBER URLS
# ============================================================

urlpatterns = [

    # ============================================
    # DEFAULT LANDING PAGE FOR /members/
    # ============================================
    path("", views.member_dashboard, name="members_home"),  # Landing page for members

    # ============================================
    # AUTHENTICATION ROUTES
    # ============================================
    path('login/', views.login_view, name='member_login'),    # Member login page
    path('logout/', views.logout_view, name='logout'),        # Member logout

    # ============================================
    # MEMBER DASHBOARD & PROFILE
    # ============================================
    path('dashboard/', views.member_dashboard, name='member_dashboard'),  # Member dashboard
    path('profile/', views.member_profile, name='member_profile'),        # View/edit member profile
    path('change-password/', views.change_password, name='change_password'),  # Change password

    # ============================================
    # MEMBER SUPPORT & FINANCIALS
    # ============================================
    path('support/', views.member_support, name='member_support'),        # Submit support tickets
    path('loans/', views.member_loans, name='member_loans'),              # View member loans
    path('savings/', views.member_savings, name='member_savings'),        # View member savings account
    path('transactions/', views.member_transactions, name='member_transactions'),  # View transactions history

    # ============================================
    # MEMBER NOTIFICATIONS
    # ============================================
    path(
        'notifications/mark-read/<int:notification_id>/',
        views.mark_notification_read,
        name='mark_notification_read'
    ),  # Mark a notification as read

    # ============================================
    # ADMIN DASHBOARD & SETTINGS
    # ============================================
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),        # Admin home
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),  # Admin notifications
    path('admin/activity-logs/', views.admin_activity_logs, name='admin_activity_logs'),  # User activity logs
    path('admin/support/', views.admin_support, name='admin_support'),              # Admin support tickets
    path('admin/reports', views.admin_reports, name='admin_reports'),

    # ============================================
    # ADMIN MEMBERS MANAGEMENT
    # ============================================
    # Admin Members Management
    path('admin/members/', views.members_list, name='admin_members_list'),
    path('admin/members/add/', views.add_member, name='admin_add_member'),
    path('admin/members/edit/<int:member_id>/', views.edit_member, name='admin_edit_member'),
    path('admin/members/profile/<int:member_id>/', views.admin_member_profile, name='admin_member_profile'),


    # ============================================
    # ADMIN LOAN MANAGEMENT
    # ============================================
    path('admin/loans/', views.loans_list, name="admin_loans_list"),                       # List all loans
    path("admin/loans/add/", views.add_loan, name="admin_add_loan"),
    path('admin/loans/<int:loan_id>/', views.loan_profile, name='loan_profile'),
    path('admin/loans/<int:loan_id>/repay/', views.loan_repayment_view, name='loan_repayment'),
    
    # ============================================
    # ADMIN SAVINGS MANAGEMENT
    # ============================================
    path('admin/savings/', views.savings_list, name='admin_savings_list'),                 # List all savings
    path('admin/savings/add/', views.add_saving, name='admin_add_savings'),
    path('admin/savings/<int:saving_id>/', views.savings_profile, name='admin_savings_profile'),

    # ============================================
    # ADMIN TRANSACTIONS MANAGEMENT
    # ============================================
    path('admin/savings/<int:saving_id>/transaction/add/', views.add_transaction, name='admin_add_transaction'),
     
    # ============================================
    # MEMBERS MANAGEMENT (GENERAL ROUTES)
    # ============================================
    path("management/", views.members_management_home, name="members_management_home"),  # Members management landing
    path("add/", views.add_member, name="add_member"),                                   # Add member (non-admin route)
    path("list/", views.members_list, name="members_list"),                              # List members (non-admin route)
  

    # ============================================
    # ADMIN USER MANAGEMENT
    # ============================================
    path('admin/manage-users/', views.admin_manage_users, name='admin_manage_users'),    # Manage system users
    path('admin/profile/', views.admin_profile, name='admin_profile'),

    # ============================================
    # ADMIN NOTIFICATIONS
    # ============================================
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/notifications/mark-all-read/', views.admin_mark_all_notifications_read, name='admin_mark_all_notifications_read'),


    # ============================================
    # SYSTEM SETTINGS
    # ============================================
    path('admin/settings/', views.system_settings, name='system_settings'),
    path("admin/roles/", views.manage_roles, name="manage_roles"),
    path('admin/settings/roles/', views.manage_roles, name="manage_roles"),
    path('admin/settings/roles/<int:role_id>/permissions/', views.assign_permissions, name="assign_permissions"),



]

# ============================================================
# MEDIA FILES IN DEVELOPMENT MODE
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
