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
    path('admin/system_settings/', views.system_settings, name='system_settings'),  # System configuration
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),  # Admin notifications
    path('admin/activity-logs/', views.admin_activity_logs, name='admin_activity_logs'),  # User activity logs
    path('admin/support/', views.admin_support, name='admin_support'),              # Admin support tickets

    # ============================================
    # ADMIN MEMBERS MANAGEMENT
    # ============================================
    path('admin/members/', views.members_list, name='admin_members_list'),                  # List all members
    path('admin/members/add/', views.add_member, name='admin_add_member'),                 # Add new member
    path('admin/members/edit/<int:member_id>/', views.edit_member, name='admin_edit_member'),  # Edit member details

    # ============================================
    # ADMIN SAVINGS MANAGEMENT
    # ============================================
    path('admin/savings/', views.savings_list, name='admin_savings_list'),                 # List all savings

    # ============================================
    # ADMIN LOAN MANAGEMENT
    # ============================================
    path('admin/loans/', views.loans_list, name='admin_loans_list'),                       # List all loans
    path('admin/loan-applications/', views.loan_applications, name='admin_loan_applications'),  # Pending loan applications
    path('admin/loan/approve/<int:loan_id>/', views.approve_loan, name='admin_approve_loan'),   # Approve a loan
    path('admin/loan/reject/<int:loan_id>/', views.reject_loan, name='admin_reject_loan'),      # Reject a loan
    path('admin/loan/repay/<int:loan_id>/', views.record_repayment, name='admin_record_repayment'),  # Record repayment

    # ============================================
    # ADMIN REPORTS
    # ============================================
    path('admin/savings-reports/', views.savings_reports, name='savings_reports'),        # Savings reports
    path('admin/loan-reports/', views.loan_reports, name='admin_loan_reports'),          # Loan reports

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
]

# ============================================================
# MEDIA FILES IN DEVELOPMENT MODE
# ============================================================
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
