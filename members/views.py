from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Sum
from .forms import AdminAddMemberForm, MemberUpdateForm, LoanForm
from .models import (
    Member, SavingAccount, SavingTransaction, UserActivityLog, Notification,
    Loan, LoanRepayment, LoanGuarantor
)
import random
import string
from datetime import date

# ==========================================================
# Helper: Get Client IP Address
# ==========================================================
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')

# ==========================================================
# Helper: Check Admin Role
# ==========================================================
def is_admin(user):
    return user.groups.filter(name="Admin").exists() or user.is_staff


# ==========================================================
# LOGIN (Admin + Member)
# ==========================================================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username').strip()
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)

            # Redirect Admin
            if is_admin(user):
                return redirect('admin_dashboard')

            # Redirect Member
            return redirect('member_dashboard')

        messages.error(request, "Invalid username or password")

    return render(request, 'members/login.html')


# ==========================================================
# LOGOUT
# ==========================================================
@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ==========================================================
# ADMIN DASHBOARD
# ==========================================================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
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



# ==========================================================
# ADMIN: Quick Links Views
# ==========================================================
@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    notifications = Notification.objects.all().order_by('-timestamp')
    return render(request, 'admin/admin_notifications.html', {'notifications': notifications})

@login_required
@user_passes_test(is_admin)
def admin_support(request):
    # For simplicity, assuming support tickets are saved as Notifications
    support_tickets = Notification.objects.filter(is_support=True).order_by('-timestamp')
    return render(request, 'admin/admin_support.html', {'support_tickets': support_tickets})

@login_required
@user_passes_test(is_admin)
def admin_activity_logs(request):
    logs = UserActivityLog.objects.all().order_by('-timestamp')
    return render(request, 'admin/admin_activity_logs.html', {'logs': logs})


# ==========================================================
# ADMIN: Add Member
# ==========================================================
@login_required
@user_passes_test(is_admin)
def add_member(request):
    if request.method == "POST":
        form = AdminAddMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.status = 'ACTIVE'
            member.save()

            # Create system login for member
            if not member.user:
                username = f"{member.first_name.lower()}.{member.last_name.lower()}.{member.member_id[-4:]}"
                tmp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                user = User.objects.create_user(
                    username=username,
                    email=member.email or '',
                    password=tmp_pass,
                    first_name=member.first_name,
                    last_name=member.last_name,
                )

                # Add to Member group
                member_group, created = Group.objects.get_or_create(name="Member")
                user.groups.add(member_group)

                member.user = user
                member.temp_password = True
                member.save()

                messages.success(request, f"Member created: {username} | Temp Password: {tmp_pass}")

            # FIXED URL NAME
            return redirect('admin_members_list')

    else:
        form = AdminAddMemberForm()

    return render(request, 'members/add_member.html', {'form': form})


# ==========================================================
# ADMIN: List Members
# ==========================================================
@login_required
@user_passes_test(is_admin)
def members_list(request):
    members = Member.objects.all()
    return render(request, 'members/members_list.html', {'members': members})


# ==========================================================
# ADMIN: Edit Member
# ==========================================================
@login_required
@user_passes_test(is_admin)
def edit_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)

    if request.method == "POST":
        form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            messages.success(request, f"{member.first_name} updated successfully!")

            # FIXED URL NAME
            return redirect('admin_members_list')

    else:
        form = MemberUpdateForm(instance=member)

    return render(request, 'members/edit_member.html', {'form': form, 'member': member})


# ==========================================================
# ADMIN: Loan Management
# ==========================================================
@login_required
@user_passes_test(is_admin)
def loan_applications(request):
    loans = Loan.objects.filter(status='pending').order_by('-start_date')
    return render(request, 'admin/loan_applications.html', {'loans': loans})


@login_required
@user_passes_test(is_admin)
def loans_list(request):
    loans = Loan.objects.all().order_by('-start_date')
    return render(request, 'admin/loans_list.html', {'loans': loans})


@login_required
@user_passes_test(is_admin)
def approve_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    loan.status = 'approved'
    loan.save()
    messages.success(request, f"Loan approved for {loan.member.first_name}")
    return redirect('admin_loan_applications')

# Loan applications list
@login_required
@user_passes_test(is_admin)
def admin_loan_applications_list(request):
    """
    Display all pending loan applications for admin to review.
    """
    loans = Loan.objects.filter(status='pending').order_by('-start_date')
    context = {
        'loans': loans
    }
    return render(request, 'admin/admin_loan_applications_list.html', context)

@login_required
@user_passes_test(is_admin)
def reject_loan(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    loan.status = 'rejected'
    loan.save()
    messages.success(request, f"Loan rejected for {loan.member.first_name}")

    # FIXED URL NAME
    return redirect('admin_loan_applications')


@login_required
@user_passes_test(is_admin)
def record_repayment(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)

    if request.method == "POST":
        amount = float(request.POST.get('amount'))

        if 0 < amount <= loan.current_balance:
            LoanRepayment.objects.create(loan=loan, amount_paid=amount)
            messages.success(request, "Repayment recorded")
        else:
            messages.error(request, "Invalid repayment amount")

        # FIXED URL NAME
        return redirect('admin_loans_list')

    return render(request, 'admin/record_repayment.html', {'loan': loan})


# ==========================================================
# ADMIN: Guarantors
# ==========================================================
@login_required
@user_passes_test(is_admin)
def guarantors_list(request):
    guarantors = LoanGuarantor.objects.all()
    return render(request, 'admin/guarantors_list.html', {'guarantors': guarantors})


# ==========================================================
# ADMIN: Savings & Reports
# ==========================================================
@login_required
@user_passes_test(is_admin)
def savings_list(request):
    accounts = SavingAccount.objects.all()
    return render(request, 'admin/savings_list.html', {'accounts': accounts})


@login_required
@user_passes_test(is_admin)
def loan_reports(request):
    loans = Loan.objects.all()
    return render(request, 'admin/loan_reports.html', {'loans': loans})


@login_required
@user_passes_test(is_admin)
def savings_reports(request):
    accounts = SavingAccount.objects.all()
    return render(request, 'admin/savings_reports.html', {'accounts': accounts})


# ==========================================================
# ADMIN: System Settings
# ==========================================================
@login_required
@user_passes_test(is_admin)
def system_settings(request):
    admins = User.objects.filter(is_staff=True)
    groups = Group.objects.all()
    return render(request, 'admin/system_settings.html', {'admins': admins, 'groups': groups})


# ==========================================================
# MEMBER DASHBOARD
# ==========================================================
@login_required
def member_dashboard(request):
    member = request.user.member

    # Savings Data
    account = getattr(member, 'savings_account', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []
    recent_balance = (
        transactions.first().balance_after_transaction
        if transactions
        else account.balance if account else 0
    )

    logs = UserActivityLog.objects.filter(member=member).order_by('-timestamp')[:5]
    unread_count = member.notifications.filter(is_read=False).count()
    notifications = member.notifications.order_by('-timestamp')[:5]

    # Loan data
    loan = Loan.objects.filter(member=member).order_by('-start_date').first()
    guarantors = LoanGuarantor.objects.filter(loan=loan) if loan else None
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('-date_paid') if loan else None
    monthly_interest = loan.calculate_monthly_interest() if loan else 0

    context = {
        'member': member,
        'account': account,
        'transactions': transactions,
        'recent_balance': recent_balance,
        'recent_logs': logs,
        'unread_notifications_count': unread_count,
        'recent_notifications': notifications,
        'loan': loan,
        'guarantors': guarantors,
        'repayments': repayments,
        'monthly_interest': monthly_interest,
    }
    return render(request, 'members/member_dashboard.html', context)


# ==========================================================
# MEMBER: Profile
# ==========================================================
@login_required
def member_profile(request):
    return render(request, 'members/member_profile.html', {'member': request.user.member})


# ==========================================================
# MEMBER: Change Password
# ==========================================================
@login_required
def change_password(request):
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

            if member and member.temp_password:
                member.temp_password = False
                member.save()

            messages.success(request, "Password successfully changed")

            return redirect('member_dashboard')

    return render(request, 'members/change_password.html')


# ==========================================================
# MEMBER: Loans, Savings, Transactions, Support
# ==========================================================
@login_required
def member_loans(request):
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
    member = request.user.member
    account = getattr(member, 'savings_account', None)
    return render(request, 'members/member_savings.html', {'member': member, 'account': account})


@login_required
def member_transactions(request):
    member = request.user.member
    account = getattr(member, 'savings_account', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []
    return render(request, 'members/member_transactions.html', {'transactions': transactions})


@login_required
def member_support(request):
    return render(request, 'members/member_support.html', {'member': request.user.member})


# ==========================================================
# AJAX: Mark Notification As Read
# ==========================================================
@login_required
def mark_notification_read(request, notification_id):
    member = request.user.member
    try:
        notification = Notification.objects.get(id=notification_id, member=member)
        notification.is_read = True
        notification.save()
    except Notification.DoesNotExist:
        messages.error(request, "Notification does not exist.")

    return redirect('member_dashboard')
