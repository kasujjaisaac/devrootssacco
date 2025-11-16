from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User
from django.contrib import messages
from .forms import AdminAddMemberForm
from .models import Member, SavingAccount, SavingTransaction
import random
import string

# -------------------- ADMIN: ADD MEMBER --------------------
@staff_member_required
def add_member(request):
    """
    Admin can add a new member. This automatically creates a linked Django user
    with a random one-time password.
    """
    if request.method == "POST":
        form = AdminAddMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.status = 'ACTIVE'
            member.save()

            # Create Django user if it does not exist
            if not member.user:
                username = f"{member.first_name.lower()}.{member.last_name.lower()}.{member.member_id[-4:]}"
                otp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                user = User.objects.create_user(
                    username=username,
                    email=member.email or '',
                    password=otp_password,
                    first_name=member.first_name,
                    last_name=member.last_name,
                )
                # Flag to force password change on first login
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


# -------------------- ADMIN: LIST MEMBERS --------------------
@staff_member_required
def members_list(request):
    members = Member.objects.all()
    return render(request, 'members/members_list.html', {'members': members})


# -------------------- MEMBER LOGIN --------------------
def member_login(request):
    """
    Handles member login. If user has a 'force password change' flag, redirect to change password.
    """
    if request.method == "POST":
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            # Check if linked to a member
            if hasattr(user, 'member'):
                login(request, user)
                # Force password change if flagged
                if getattr(user, 'profile_force_password_change', False):
                    messages.info(request, "You must change your password on first login.")
                    return redirect('change_password')
                return redirect('member_dashboard')
            else:
                error = "This user is not a registered member."
        else:
            error = "Invalid username or password."
        return render(request, 'members/login.html', {'error': error})
    return render(request, 'members/login.html')


# -------------------- MEMBER DASHBOARD --------------------
@login_required
def member_dashboard(request):
    try:
        member = request.user.member
    except AttributeError:
        messages.error(request, "Your member profile is not yet created.")
        return redirect('member_login')

    account = getattr(member, 'savings_account', None)
    transactions = account.transactions.all() if account else []

    context = {
        'member': member,
        'account': account,
        'transactions': transactions,
    }
    return render(request, 'members/dashboard.html', context)


# -------------------- MEMBER LOGOUT --------------------
@login_required
def member_logout(request):
    logout(request)
    return redirect('member_login')


# -------------------- CHANGE PASSWORD --------------------
@login_required
def change_password(request):
    """
    Allows member to change password on first login or anytime.
    """
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
            # Remove the force password change flag
            if hasattr(user, 'profile_force_password_change'):
                user.profile_force_password_change = False
            user.save()
            update_session_auth_hash(request, user)  # Keep user logged in
            messages.success(request, "Password changed successfully!")
            return redirect('member_dashboard')

    return render(request, 'members/change_password.html')
