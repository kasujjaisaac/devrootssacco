from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [

    # ================================
    # AUTHENTICATION
    # ================================
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # ================================
    # MEMBER ROUTES
    # ================================
    path('dashboard/', views.member_dashboard, name='member_dashboard'),
    path('profile/', views.member_profile, name='member_profile'),
    path('change-password/', views.change_password, name='change_password'),
    path('support/', views.member_support, name='member_support'),
    path('loans/', views.member_loans, name='member_loans'),
    path('savings/', views.member_savings, name='member_savings'),
    path('transactions/', views.member_transactions, name='member_transactions'),

    path('notifications/mark-read/<int:notification_id>/', 
         views.mark_notification_read, 
         name='mark_notification_read'),

    # ================================
    # ADMIN ROUTES
    # ================================
    path('admin/dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('admin/system_settings/', views.system_settings, name='system_settings'),
    path('admin/notifications/', views.admin_notifications, name='admin_notifications'),
    path('admin/activity-logs/', views.admin_activity_logs, name='admin_activity_logs'),
    path('admin/support/', views.admin_support, name='admin_support'),

    # Members
    path('admin/members/', views.members_list, name='admin_members_list'),
    path('admin/members/add/', views.add_member, name='admin_add_member'),
    path('admin/members/edit/<int:member_id>/', views.edit_member, name='admin_edit_member'),

    # Savings
    path('admin/savings/', views.savings_list, name='admin_savings_list'),

    # Loans
    path('admin/loans/', views.loans_list, name='admin_loans_list'),
    path('admin/loan-applications/', views.loan_applications, name='admin_loan_applications'),
    path('admin/loan/approve/<int:loan_id>/', views.approve_loan, name='admin_approve_loan'),
    path('admin/loan/reject/<int:loan_id>/', views.reject_loan, name='admin_reject_loan'),
    path('admin/loan/repay/<int:loan_id>/', views.record_repayment, name='admin_record_repayment'),

    # Reports
    path('admin/savings-reports/', views.savings_reports, name='savings_reports'),
    path('admin/loan-reports/', views.loan_reports, name='admin_loan_reports'),


    #members dashboard
    path("members/management/", views.members_management_home, name="members_management_home"),
    path("members/add/", views.add_member, name="add_member"),
    path("members/list/", views.members_list, name="members_list"),

    path('admin/manage-users/', views.admin_manage_users, name='admin_manage_users'),
    
    
    


]


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
