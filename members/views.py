from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import AdminAddMemberForm
from .models import Member, SavingAccount, SavingTransaction, UserActivityLog
import random
import string


# ============================================================
# Helper function: Get client IP
# ============================================================
def get_client_ip(request):
    """Return the client's IP address."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# ============================================================
# ADMIN: Add Member
# ============================================================
@staff_member_required
def add_member(request):
    """Admin registers a new SACCO member and auto-creates a Django User."""
    if request.method == "POST":
        form = AdminAddMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.status = 'ACTIVE'
            member.save()

            if not member.user:
                # Generate username and one-time password
                username = f"{member.first_name.lower()}.{member.last_name.lower()}.{member.member_id[-4:]}"
                otp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))

                user = User.objects.create_user(
                    username=username,
                    email=member.email or '',
                    password=otp_password,
                    first_name=member.first_name,
                    last_name=member.last_name
                )

                # Force password change on first login
                user.profile_force_password_change = True
                user.save()

                member.user = user
                member.save()

                messages.success(
                    request,
                    f"Member added successfully! Username: {username}, One-time Password: {otp_password}"
                )
            return redirect('members_list')
    else:
        form = AdminAddMemberForm()

    return render(request, 'members/add_member.html', {'form': form})


# ============================================================
# ADMIN: List Members
# ============================================================
@staff_member_required
def members_list(request):
    members = Member.objects.all().order_by('-created_at')
    return render(request, 'members/members_list.html', {'members': members})


# ============================================================
# MEMBER LOGIN
# ============================================================
def member_login(request):
    """Login for members only (users linked to a Member profile) and log activity."""
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            if hasattr(user, 'member'):
                login(request, user)

                # Log the login activity
                UserActivityLog.objects.create(
                    member=user.member,
                    action='Logged in',
                    ip_address=get_client_ip(request)
                )

                if getattr(user, 'profile_force_password_change', False):
                    messages.info(request, "You must change your password on first login.")
                    return redirect('change_password')

                return redirect('member_dashboard')
            else:
                messages.error(request, "This user is not a registered SACCO member.")
        else:
            messages.error(request, "Invalid username or password.")

        return redirect('member_login')

    return render(request, 'members/login.html')


# ============================================================
# MEMBER DASHBOARD
# ============================================================
@login_required
def member_dashboard(request):
    """Display the member dashboard with account info, transactions, and recent activity."""
    try:
        member = request.user.member
    except AttributeError:
        messages.error(request, "Your member profile is not found.")
        return redirect('member_login')

    account = getattr(member, 'savings_account', None)

    # Transactions sorted newest first
    transactions = account.transactions.order_by('-transaction_date') if account else []

    # Recent balance (before last transaction)
    recent_balance = 0
    if transactions.exists():
        last_tx = transactions.first()  # newest transaction
        if transactions.count() > 1:
            recent_balance = transactions[1].balance_after_transaction  # second newest
        else:
            recent_balance = 0
    elif account:
        recent_balance = account.balance

    # Fetch latest 5 activity logs
    recent_logs = UserActivityLog.objects.filter(member=member).order_by('-timestamp')[:5]

    context = {
        'member': member,
        'account': account,
        'transactions': transactions,
        'recent_balance': recent_balance,
        'recent_logs': recent_logs,
    }

    return render(request, 'members/dashboard.html', context)


# ============================================================
# MEMBER LOGOUT
# ============================================================
@login_required
def member_logout(request):
    """Log out the member and store a logout activity entry."""
    if hasattr(request.user, 'member'):
        UserActivityLog.objects.create(
            member=request.user.member,
            action='Logged out',
            ip_address=get_client_ip(request)
        )

    logout(request)
    return redirect('member_login')


# ============================================================
# CHANGE PASSWORD
# ============================================================
@login_required
def change_password(request):
    """Member changes password. Required on first login if forced."""
    if request.method == "POST":
        current_password = request.POST.get('current_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')

        user = request.user

        if not user.check_password(current_password):
            messages.error(request, "Current password is incorrect.")
        elif new_password != confirm_password:
            messages.error(request, "New password and confirm password do not match.")
        else:
            user.set_password(new_password)
            # Remove the force password change flag if exists
            if hasattr(user, 'profile_force_password_change'):
                user.profile_force_password_change = False
            user.save()
            update_session_auth_hash(request, user)
            messages.success(request, "Password changed successfully!")
            return redirect('member_dashboard')

    return render(request, 'members/change_password.html')
