# ==========================================================
# IMPORTS
# ==========================================================
# Standard libraries
from datetime import date
import random
import string

# Django shortcuts and utilities
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Sum

# Forms and models from the app
from .forms import AdminAddMemberForm, MemberUpdateForm, LoanForm
from .models import (
    Member, SavingAccount, SavingTransaction,
    Loan, LoanRepayment, LoanGuarantor,
    UserActivityLog, Notification
)

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def get_client_ip(request):
    """
    Get the client IP address from the request.
    Useful for logging user activity.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def is_admin(user):
    """
    Check if a user is an Admin.
    Admins are either in the 'Admin' group or marked as staff.
    """
    return user.groups.filter(name="Admin").exists() or user.is_staff


# ==========================================================
# AUTHENTICATION VIEWS
# ==========================================================
def login_view(request):
    """
    Handles user login for both Admins and Members.
    POST: Authenticate user and redirect to the appropriate dashboard.
    GET: Render the login page.
    """
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            # Redirect Admin users to admin dashboard
            return redirect('admin_dashboard') if is_admin(user) else redirect('member_dashboard')

        # Display error if authentication fails
        messages.error(request, "Invalid username or password")

    return render(request, 'members/login.html')


@login_required
def logout_view(request):
    """
    Logs out the currently logged-in user.
    Redirects to login page after logout.
    """
    logout(request)
    return redirect('member_login')


# ==========================================================
# ADMIN VIEWS
# ==========================================================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """
    Admin dashboard view.
    Displays statistics such as:
    - Total members
    - Active members
    - Total loans
    - Pending loans
    - Total savings balance
    """
    total_members = Member.objects.count()
    active_members = Member.objects.filter(status='ACTIVE').count()
    total_loans = Loan.objects.count()
    pending_loans = Loan.objects.filter(status='pending').count()
    total_savings = SavingAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0

    context = {
        'total_members': total_members,
        'active_members': active_members,
        'total_loans': total_loans,
        'pending_loans': pending_loans,
        'total_savings': total_savings,
    }
    return render(request, 'admin/admin_dashboard.html', context)


# ----------------------------
# Admin: Quick Links (Notifications, Support, Logs)
# ----------------------------
@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    """
    View to display all notifications for admin.
    Sorted by most recent first.
    """
    notifications = Notification.objects.all().order_by('-timestamp')
    return render(request, 'admin/admin_notifications.html', {'notifications': notifications})


@login_required
@user_passes_test(is_admin)
def admin_support(request):
    """
    View to display all support tickets for admin.
    Here, support tickets are represented as notifications with `is_support=True`.
    """
    support_tickets = Notification.objects.filter(is_support=True).order_by('-timestamp')
    return render(request, 'admin/admin_support.html', {'support_tickets': support_tickets})


@login_required
@user_passes_test(is_admin)
def admin_activity_logs(request):
    """
    View to display all user activity logs for admin monitoring.
    Sorted by most recent first.
    """
    logs = UserActivityLog.objects.all().order_by('-timestamp')
    return render(request, 'admin/admin_activity_logs.html', {'logs': logs})


# ----------------------------
# Admin: Member Management
# ----------------------------
@login_required
@user_passes_test(is_admin)
def add_member(request):
    """
    Add a new member to the system.
    - Creates Member object
    - Optionally creates a linked system login for the member
    - Generates temporary password if new login is created
    """
    if request.method == "POST":
        form = AdminAddMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.status = 'ACTIVE'
            member.save()

            # Automatically create login user if member.user is None
            if not member.user:
                # Create username: firstname.lastname.last4ofID
                username = f"{member.first_name.lower()}.{member.last_name.lower()}.{member.member_id[-4:]}"
                tmp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                user = User.objects.create_user(
                    username=username,
                    email=member.email or '',
                    password=tmp_pass,
                    first_name=member.first_name,
                    last_name=member.last_name
                )

                # Assign member to "Member" group
                member_group, _ = Group.objects.get_or_create(name="Member")
                user.groups.add(member_group)

                # Link user to member
                member.user = user
                member.temp_password = True
                member.save()

                messages.success(request, f"Member created: {username} | Temp Password: {tmp_pass}")

            return redirect('admin_members_list')
    else:
        form = AdminAddMemberForm()

    return render(request, 'members/add_member.html', {'form': form})


@login_required
@user_passes_test(is_admin)
def members_list(request):
    """
    Admin view to list all members.
    """
    members = Member.objects.all()
    return render(request, 'members/members_list.html', {'members': members})


@login_required
@user_passes_test(is_admin)
def edit_member(request, member_id):
    """
    Admin view to edit a specific member's details.
    """
    member = get_object_or_404(Member, id=member_id)

    if request.method == "POST":
        form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{member.first_name} updated successfully!")
            return redirect('admin_members_list')
    else:
        form = MemberUpdateForm(instance=member)

    return render(request, 'members/edit_member.html', {'form': form, 'member': member})


# ----------------------------
# Admin: Loan Management
# ----------------------------
@login_required
@user_passes_test(is_admin)
def loan_applications(request):
    """
    View pending loan applications for admin review.
    """
    loans = Loan.objects.filter(status='pending').order_by('-start_date')
    return render(request, 'admin/loan_applications.html', {'loans': loans})


@login_required
@user_passes_test(is_admin)
def loans_list(request):
    """
    Admin view for listing all loans in the system.
    """
    loans = Loan.objects.all().order_by('-start_date')
    return render(request, 'admin/loans_list.html', {'loans': loans})


@login_required
@user_passes_test(is_admin)
def approve_loan(request, loan_id):
    """
    Approve a specific loan.
    """
    loan = get_object_or_404(Loan, id=loan_id)
    loan.status = 'approved'
    loan.save()
    messages.success(request, f"Loan approved for {loan.member.first_name}")
    return redirect('admin_loan_applications')


@login_required
@user_passes_test(is_admin)
def reject_loan(request, loan_id):
    """
    Reject a specific loan.
    """
    loan = get_object_or_404(Loan, id=loan_id)
    loan.status = 'rejected'
    loan.save()
    messages.success(request, f"Loan rejected for {loan.member.first_name}")
    return redirect('admin_loan_applications')


@login_required
@user_passes_test(is_admin)
def record_repayment(request, loan_id):
    """
    Record a repayment for a loan.
    Ensures amount is valid and within loan balance.
    """
    loan = get_object_or_404(Loan, id=loan_id)

    if request.method == "POST":
        amount = float(request.POST.get('amount'))
        if 0 < amount <= loan.current_balance:
            LoanRepayment.objects.create(loan=loan, amount_paid=amount)
            messages.success(request, "Repayment recorded")
        else:
            messages.error(request, "Invalid repayment amount")

        return redirect('admin_loans_list')

    return render(request, 'admin/record_repayment.html', {'loan': loan})


# ----------------------------
# Admin: Savings & Reports
# ----------------------------
@login_required
@user_passes_test(is_admin)
def savings_list(request):
    """List all savings accounts."""
    accounts = SavingAccount.objects.all()
    return render(request, 'admin/savings_list.html', {'accounts': accounts})


@login_required
@user_passes_test(is_admin)
def loan_reports(request):
    """View all loans for reporting purposes."""
    loans = Loan.objects.all()
    return render(request, 'admin/loan_reports.html', {'loans': loans})


@login_required
@user_passes_test(is_admin)
def savings_reports(request):
    """View all savings for reporting purposes."""
    accounts = SavingAccount.objects.all()
    return render(request, 'admin/savings_reports.html', {'accounts': accounts})


@login_required
@user_passes_test(is_admin)
def system_settings(request):
    """System settings page for admin."""
    admins = User.objects.filter(is_staff=True)
    groups = Group.objects.all()
    return render(request, 'admin/system_settings.html', {'admins': admins, 'groups': groups})


# ==========================================================
# MEMBER VIEWS
# ==========================================================
@login_required
def member_dashboard(request):
    """
    Member dashboard view.
    Shows:
    - Savings account and transactions
    - Recent activity logs
    - Loans, guarantors, repayments, interest
    """
    try:
        member = request.user.member
    except Member.DoesNotExist:
        return redirect('add_member')  # Member profile missing

    # Savings account & transactions
    account = getattr(member, 'savingaccount', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []
    recent_balance = transactions.last().balance_after_transaction if transactions else 0.0

    # Activity logs
    recent_logs = UserActivityLog.objects.filter(member=member).order_by('-timestamp')[:5] if member else []

    # Loan info
    loan = Loan.objects.filter(member=member).order_by('-start_date').first()
    guarantors = LoanGuarantor.objects.filter(loan=loan) if loan else None
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('-date_paid') if loan else None
    monthly_interest = loan.calculate_monthly_interest() if loan else 0

    context = {
        'member': member,
        'account': account,
        'transactions': transactions,
        'recent_balance': recent_balance,
        'recent_logs': recent_logs,
        'loan': loan,
        'guarantors': guarantors,
        'repayments': repayments,
        'monthly_interest': monthly_interest,
    }
    return render(request, 'members/member_dashboard.html', context)


@login_required
def member_profile(request):
    """Display member profile."""
    return render(request, 'members/member_profile.html', {'member': request.user.member})


@login_required
def change_password(request):
    """
    Allow members to change their password.
    Validates current password and matching new passwords.
    """
    user = request.user
    member = getattr(user, 'member', None)

    if request.method == "POST":
        current = request.POST.get('current_password')
        new = request.POST.get('new_password')
        confirm = request.POST.get('confirm_password')

        if not user.check_password(current):
            messages.error(request, "Wrong current password.")
        elif new != confirm:
            messages.error(request, "Passwords do not match.")
        else:
            user.set_password(new)
            user.save()
            update_session_auth_hash(request, user)

            # Disable temp password flag
            if member and member.temp_password:
                member.temp_password = False
                member.save()

            messages.success(request, "Password successfully changed")
            return redirect('member_dashboard')

    return render(request, 'members/change_password.html')


@login_required
def member_loans(request):
    """Display member's loans, guarantors, repayments, and monthly interest."""
    member = request.user.member
    loan = Loan.objects.filter(member=member).order_by('-start_date').first()
    guarantors = LoanGuarantor.objects.filter(loan=loan) if loan else None
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('-date_paid') if loan else None
    monthly_interest = loan.calculate_monthly_interest() if loan else 0

    context = {
        'member': member,
        'loan': loan,
        'guarantors': guarantors,
        'repayments': repayments,
        'monthly_interest': monthly_interest,
    }
    return render(request, 'members/member_loans.html', context)


@login_required
def member_savings(request):
    """Display member's savings account info."""
    member = request.user.member
    account = getattr(member, 'savingaccount', None)
    return render(request, 'members/member_savings.html', {'member': member, 'account': account})


@login_required
def member_transactions(request):
    """Display member's transaction history."""
    member = request.user.member
    account = getattr(member, 'savingaccount', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []
    return render(request, 'members/member_transactions.html', {'transactions': transactions})


@login_required
def member_support(request):
    """Display member support page."""
    return render(request, 'members/member_support.html', {'member': request.user.member})


@login_required
def mark_notification_read(request, notification_id):
    """Mark a specific notification as read for the logged-in member."""
    member = request.user.member
    try:
        notification = Notification.objects.get(id=notification_id, member=member)
        notification.is_read = True
        notification.save()
    except Notification.DoesNotExist:
        messages.error(request, "Notification does not exist.")
    return redirect('member_dashboard')


# ==========================================================
# ADMIN: Manage Users
# ==========================================================
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_manage_users(request):
    """View for admin to manage system users."""
    admins = User.objects.filter(is_staff=True)
    return render(request, 'admin/settings/manage_users.html', {'admins': admins})


# ==========================================================
# MEMBERS MANAGEMENT HOME
# ==========================================================
@login_required
@user_passes_test(is_admin)
def members_management_home(request):
    """Landing page for members management."""
    return render(request, "members/members_management_home.html")
