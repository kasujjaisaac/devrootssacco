from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import AdminAddMemberForm
from .models import Member, SavingAccount, SavingTransaction, UserActivityLog, Notification
import random
import string


# ==========================
# Helper function: Get client IP
# ==========================
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ==========================
# ADMIN: Add Member
# ==========================
@staff_member_required
def add_member(request):
    if request.method == "POST":
        form = AdminAddMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.status = 'ACTIVE'
            member.save()

            if not member.user:
                username = f"{member.first_name.lower()}.{member.last_name.lower()}.{member.member_id[-4:]}"
                otp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                user = User.objects.create_user(
                    username=username,
                    email=member.email or '',
                    password=otp_password,
                    first_name=member.first_name,
                    last_name=member.last_name
                )

                # Use Member.temp_password instead of patching User
                member.user = user
                member.temp_password = True
                member.save()

                messages.success(
                    request,
                    f"Member added successfully! Username: {username}, One-time Password: {otp_password}"
                )
            return redirect('members_list')
    else:
        form = AdminAddMemberForm()

    return render(request, 'members/add_member.html', {'form': form})


# ==========================
# MEMBER LOGIN
# ==========================
def member_login(request):
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'member'):
                login(request, user)

                # Log activity
                UserActivityLog.objects.create(
                    member=user.member,
                    action='Logged in',
                    ip_address=get_client_ip(request)
                )

                # Force password change if temporary
                if getattr(user.member, 'temp_password', False):
                    messages.info(request, "You must change your password on first login.")
                    return redirect('change_password')

                return redirect('dashboard')
            else:
                messages.error(request, "This user is not a registered SACCO member.")
        else:
            messages.error(request, "Invalid username or password.")

        return redirect('member_login')

    return render(request, 'members/login.html')


# ==========================
# MEMBER DASHBOARD
# ==========================
@login_required
def member_dashboard(request):
    member = request.user.member

    # Savings account & transactions
    account = getattr(member, 'savings_account', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []

    # Recent balance
    recent_balance = 0
    if transactions.exists():
        recent_balance = transactions.first().balance_after_transaction
    elif account:
        recent_balance = account.balance

    # Recent activity logs
    recent_logs = UserActivityLog.objects.filter(member=member).order_by('-timestamp')[:5]

    # Notifications
    unread_notifications_count = member.notifications.filter(is_read=False).count()
    recent_notifications = member.notifications.order_by('-timestamp')[:5]

    context = {
        'member': member,
        'account': account,
        'transactions': transactions,
        'recent_balance': recent_balance,
        'recent_logs': recent_logs,
        'unread_notifications_count': unread_notifications_count,
        'recent_notifications': recent_notifications,
    }
    return render(request, 'members/dashboard.html', context)


# ==========================
# MEMBER PROFILE
# ==========================
@login_required
def member_profile(request):
    member = request.user.member
    return render(request, 'members/profile.html', {'member': member})


# ==========================
# MEMBER LOGOUT
# ==========================
@login_required
def member_logout(request):
    member = getattr(request.user, 'member', None)
    if member:
        UserActivityLog.objects.create(
            member=member,
            action='Logged out',
            ip_address=get_client_ip(request)
        )
    logout(request)
    return redirect('member_login')


# ==========================
# CHANGE PASSWORD
# ==========================
@login_required
def change_password(request):
    user = request.user
    member = getattr(user, 'member', None)

    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
        else:
            user.set_password(new_password)
            user.save()
            update_session_auth_hash(request, user)

            # Mark temp_password as False after first change
            if member and member.temp_password:
                member.temp_password = False
                member.save()

            messages.success(request, "Password changed successfully!")
            return redirect('dashboard')

    return render(request, 'members/change_password.html')


# ==========================
# MEMBER LOANS
# ==========================
@login_required
def member_loans(request):
    member = request.user.member
    loans = []  # Replace with actual Loan model query
    return render(request, 'members/loans.html', {'member': member, 'loans': loans})


# ==========================
# MEMBER SAVINGS
# ==========================
@login_required
def member_savings(request):
    member = request.user.member
    account = getattr(member, 'savings_account', None)
    return render(request, 'members/savings.html', {'member': member, 'account': account})


# ==========================
# MEMBER TRANSACTIONS
# ==========================
@login_required
def member_transactions(request):
    member = request.user.member
    account = getattr(member, 'savings_account', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []
    return render(request, 'members/transactions.html', {'member': member, 'transactions': transactions})


# ==========================
# MEMBER SUPPORT
# ==========================
@login_required
def member_support(request):
    member = request.user.member
    return render(request, 'members/support.html', {'member': member})

# ==========================
# LIST ALL MEMBERS
# ==========================
@staff_member_required
def members_list(request):
    members = Member.objects.all()
    return render(request, 'members/members_list.html', {'members': members})


# ==========================
# MARK NOTIFICATION AS READ (AJAX)
# ==========================
@login_required
def mark_notification_read(request, notification_id):
    member = request.user.member
    try:
        notification = Notification.objects.get(id=notification_id, member=member)
        notification.is_read = True
        notification.save()
        return redirect('dashboard')  # or return JsonResponse({'status': 'ok'})
    except Notification.DoesNotExist:
        messages.error(request, "Notification not found.")
        return redirect('dashboard')
