# ==========================================================
# IMPORTS
# ==========================================================
from datetime import date
import random
import string
from django.utils import timezone
from django.db import transaction
from .forms import LoanRepaymentForm

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.db.models import Sum
from .forms import LoanForm, LoanGuarantorForm
from django.db import IntegrityError
from members.models import Notification
from .forms import AdminAddMemberForm, MemberUpdateForm, LoanForm
from .models import (Member, SavingAccount, SavingTransaction,Loan, LoanRepayment, LoanGuarantor,UserActivityLog, Notification)
from django.db.models import Sum, Count, Q, F
from datetime import datetime, timedelta

# ==========================================================
# HELPER FUNCTIONS
# ==========================================================
def get_client_ip(request):
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    return x_forwarded_for.split(',')[0] if x_forwarded_for else request.META.get('REMOTE_ADDR')


def is_admin(user):
    return user.groups.filter(name="Admin").exists() or user.is_staff


def create_savings_account(member):
    """Ensure a SavingAccount exists for a member safely."""
    return SavingAccount.objects.get_or_create(
        member=member,
        defaults={'account_number': f"SA-{member.id:06d}", 'balance': 0.0}
    )


def create_member_user(member):
    """Ensure a linked User exists for a member safely."""
    if member.user:
        return member.user, None  # Already exists

    username = f"{member.first_name.lower()}.{member.last_name.lower()}.{member.member_id[-4:]}"
    tmp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
    user = User.objects.create_user(
        username=username,
        email=member.email or '',
        password=tmp_pass,
        first_name=member.first_name,
        last_name=member.last_name
    )
    member_group, _ = Group.objects.get_or_create(name="Member")
    user.groups.add(member_group)
    member.user = user
    member.temp_password = True
    member.save()
    return user, tmp_pass


# ==========================================================
# AUTHENTICATION VIEWS
# ==========================================================
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)

        if user:
            login(request, user)
            return redirect('admin_dashboard') if is_admin(user) else redirect('member_dashboard')

        messages.error(request, "Invalid username or password")

    return render(request, 'members/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('member_login')


# ==========================================================
# ADMIN VIEWS
# ==========================================================
@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_members = Member.objects.count()
    active_members = Member.objects.filter(status='ACTIVE').count()
    total_loans = Loan.objects.count()
    pending_loans = Loan.objects.filter(status='pending').count()
    total_savings = SavingAccount.objects.aggregate(Sum('balance'))['balance__sum'] or 0

    return render(request, 'admin/admin_dashboard.html', {
        'total_members': total_members,
        'active_members': active_members,
        'total_loans': total_loans,
        'pending_loans': pending_loans,
        'total_savings': total_savings,
    })


@login_required
@user_passes_test(is_admin)
def admin_notifications(request):
    notifications = Notification.objects.all().order_by('-timestamp')
    return render(request, 'admin/admin_notifications.html', {'notifications': notifications})


@login_required
@user_passes_test(is_admin)
def admin_support(request):
    support_tickets = Notification.objects.filter(is_support=True).order_by('-timestamp')
    return render(request, 'admin/admin_support.html', {'support_tickets': support_tickets})


@login_required
@user_passes_test(is_admin)
def admin_activity_logs(request):
    logs = UserActivityLog.objects.all().order_by('-timestamp')
    return render(request, 'admin/admin_activity_logs.html', {'logs': logs})


# ==========================================================
# Admin: Add Member
# ==========================================================
from django.contrib import messages

@login_required
@user_passes_test(is_admin)
def add_member(request):
    if request.method == "POST":
        form = AdminAddMemberForm(request.POST, request.FILES)
        if form.is_valid():
            member = form.save(commit=False)
            member.status = 'ACTIVE'
            member.save()

            # Create SavingAccount safely
            saving_account, _ = SavingAccount.objects.get_or_create(
                member=member,
                defaults={'account_number': f"SA-{member.id:06d}", 'balance': 0.0}
            )

            # Create linked User safely
            if not member.user:
                base_username = f"{member.first_name.lower()}.{member.last_name.lower()}.{member.member_id[-4:]}"
                username = base_username
                counter = 1
                while User.objects.filter(username=username).exists():
                    username = f"{base_username}{counter}"
                    counter += 1

                tmp_pass = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
                user = User.objects.create_user(
                    username=username,
                    email=member.email or "",
                    password=tmp_pass,
                    first_name=member.first_name,
                    last_name=member.last_name,
                )

                member_group, _ = Group.objects.get_or_create(name="Member")
                user.groups.add(member_group)
                member.user = user
                member.temp_password = True
                member.save()

                # Save temp password info in messages
                messages.success(request, f"Member {member.first_name} {member.last_name} added successfully!")
                messages.info(request, f"Username: {user.username} | Temporary Password: {tmp_pass}")

            else:
                messages.success(request, f"Member {member.first_name} {member.last_name} added successfully!")

            # Redirect to the same page to avoid resubmission
            return redirect('add_member')

    else:
        form = AdminAddMemberForm()

    return render(request, 'admin/add_member.html', {'form': form})

# ==========================================================
# Admin: Edit Member
# ==========================================================
@login_required
@user_passes_test(is_admin)
def edit_member(request, member_id):
    member = get_object_or_404(Member, id=member_id)

    if request.method == "POST":
        form = MemberUpdateForm(request.POST, request.FILES, instance=member)
        if form.is_valid():
            form.save()
            # Ensure SavingAccount exists after edit
            create_savings_account(member)
            messages.success(request, f"{member.first_name} updated successfully!")
            return redirect('admin_members_list')
    else:
        form = MemberUpdateForm(instance=member)

    return render(request, 'admin/admin_edit_members.html', {'form': form, 'member': member})


# ==========================================================
# Admin: Members List
# ==========================================================
@login_required
@user_passes_test(is_admin)
def members_list(request):
    members = Member.objects.all()
    unread_notifications = Notification.objects.filter(is_read=False, member__isnull=True).count()
    return render(request, 'admin/members_list.html', {'members': members, 'unread_notifications': unread_notifications})


# ==========================================================
# Admin: Member Profile
# ==========================================================
@login_required
@user_passes_test(is_admin)
def admin_member_profile(request, member_id):
    member = get_object_or_404(Member, id=member_id)
    create_savings_account(member)  # Ensure account exists
    create_member_user(member)      # Ensure linked user exists
    return render(request, 'admin/admin_member_profile.html', {'member': member})


# ==========================================================
# Admin: Loan Management
# ==========================================================
@login_required
@user_passes_test(is_admin)
def loans_list(request):
    # ------------------------------
    # 1. Search & Filtering
    # ------------------------------
    search_query = request.GET.get("search", "").strip()
    status_filter = request.GET.get("status", "").strip()

    loans = Loan.objects.all().order_by("-start_date")

    # Filter by search
    if search_query:
        loans = loans.filter(
            member__first_name__icontains=search_query
        ) | loans.filter(
            member__last_name__icontains=search_query
        ) | loans.filter(
            loan_id__icontains=search_query
        )

    # Filter by status
    if status_filter:
        loans = loans.filter(status=status_filter)

    # ------------------------------
    # 2. Sorting Logic
    # ------------------------------
    sort_option = request.GET.get("sort", "recent")

    if sort_option == "amount_high":
        loans = loans.order_by("-amount")
    elif sort_option == "amount_low":
        loans = loans.order_by("-principal_amount")
    elif sort_option == "oldest":
        loans = loans.order_by("-principal_amount")
    else:
        loans = loans.order_by("-start_date")  # default

    # ------------------------------
    # 3. Pagination
    # ------------------------------
    from django.core.paginator import Paginator

    paginator = Paginator(loans, 10)  # 10 loans per page
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    # ------------------------------
    # 4. UI Enhancements (Statistics)
    # ------------------------------
    total_loans = Loan.objects.count()
    total_active = Loan.objects.filter(status="approved").count()
    total_pending = Loan.objects.filter(status="pending").count()
    total_amount = Loan.objects.aggregate(Sum("principal_amount"))["principal_amount__sum"] or 0
    context = {
        "loans": page_obj,
        "page_obj": page_obj,
        "total_loans": total_loans,
        "total_active": total_active,
        "total_pending": total_pending,
        "total_amount": total_amount,
        "search_query": search_query,
        "status_filter": status_filter,
        "sort_option": sort_option,
    }

    return render(request, "admin/admin_loans_list.html", context)

@login_required
def add_loan(request):
    if request.method == "POST":
        form = LoanForm(request.POST)
        if form.is_valid():
            loan = form.save(commit=False)
            loan.start_date = timezone.now().date()  # auto set today
            loan.current_balance = loan.principal_amount  # starting balance
            loan.save()

            messages.success(request, "Loan successfully added!")
            return redirect("admin_loans_list")
    else:
        form = LoanForm()

    context = {
        "form": form,
    }
    return render(request, "admin/admin_add_loan.html", context)

@login_required
@user_passes_test(is_admin)
def add_loan(request):
    if request.method == "POST":
        loan_form = LoanForm(request.POST)
        guarantor_form = LoanGuarantorForm(request.POST)

        if loan_form.is_valid() and guarantor_form.is_valid():
            loan = loan_form.save(commit=False)
            loan.start_date = timezone.now().date()
            loan.current_balance = loan.principal_amount
            loan.save()

            g1 = guarantor_form.cleaned_data['guarantor1']
            g2 = guarantor_form.cleaned_data['guarantor2']
            g3 = guarantor_form.cleaned_data['guarantor3']

            if len({g1, g2, g3}) != 3:
                messages.error(request, "Guarantors must be three different members.")
                context = {'loan_form': loan_form, 'guarantor_form': guarantor_form}
                return render(request, "admin/admin_add_loan.html", context)

            LoanGuarantor.objects.create(loan=loan, guarantor=g1)
            LoanGuarantor.objects.create(loan=loan, guarantor=g2)
            LoanGuarantor.objects.create(loan=loan, guarantor=g3)

            messages.success(request, "Loan created successfully with 3 guarantors.")
            return redirect("admin_loans_list")
    else:
        loan_form = LoanForm()
        guarantor_form = LoanGuarantorForm()

    context = {
        'loan_form': loan_form,
        'guarantor_form': guarantor_form,
    }
    return render(request, "admin/admin_add_loan.html", context)

@login_required
@user_passes_test(is_admin)
def loan_profile(request, loan_id):
    loan = get_object_or_404(Loan, id=loan_id)
    member = loan.member
    guarantors = LoanGuarantor.objects.filter(loan=loan)
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('-date_paid')
    monthly_interest = loan.calculate_monthly_interest() if hasattr(loan, 'calculate_monthly_interest') else 0

    # Total paid
    total_paid = repayments.aggregate(total=Sum('amount_paid'))['total'] or 0

    context = {
        'loan': loan,
        'member': member,
        'guarantors': guarantors,
        'repayments': repayments,
        'monthly_interest': monthly_interest,
        'total_paid': total_paid,
    }
    return render(request, 'admin/loan_profile.html', context)


@login_required
@user_passes_test(is_admin)
def loan_repayment_view(request, loan_id):
    """
    Admin view to see a loan and add repayments.
    """
    loan = get_object_or_404(Loan, id=loan_id)
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('-date_paid')

    if request.method == "POST":
        form = LoanRepaymentForm(request.POST)
        if form.is_valid():
            with transaction.atomic():  # ensure balance updates safely
                repayment = form.save(commit=False)
                repayment.loan = loan
                repayment.date_paid = timezone.now()
                repayment.save()

                # Update loan balance
                loan.current_balance -= repayment.amount
                if loan.current_balance <= 0:
                    loan.current_balance = 0
                    loan.status = "paid"
                loan.save()

                messages.success(request, f"Repayment of {repayment.amount} added successfully.")
                return redirect('loan_repayment', loan_id=loan.id)
    else:
        form = LoanRepaymentForm()

    context = {
        'loan': loan,
        'repayments': repayments,
        'form': form,
    }
    return render(request, 'admin/loan_repayment.html', context)

# ==========================================================
# Admin: Savings
# ==========================================================
@login_required
@user_passes_test(is_admin)
def savings_list(request):
    # Only accounts that exist
    savings = SavingAccount.objects.select_related('member').all()
    total_saved = sum(s.balance for s in savings)
    active_accounts = savings.count()

    context = {
        'savings': savings,
        'total_saved': total_saved,
        'active_accounts': active_accounts,
    }
    return render(request, 'admin/admin_savings_list.html', context)

@login_required
@user_passes_test(is_admin)
def savings_profile(request, saving_id):
    saving = get_object_or_404(SavingAccount, pk=saving_id)
    transactions = saving.transactions.all().order_by('-transaction_date')
    
    context = {
        'saving': saving,
        'transactions': transactions
    }
    return render(request, 'admin/admin_savings_profile.html', context)


@login_required
@user_passes_test(is_admin)
def add_saving(request):
    members_without_savings = Member.objects.filter(savings_account__isnull=True)
    if request.method == "POST":
        member_id = request.POST.get('member')
        member = get_object_or_404(Member, id=member_id)
        SavingAccount.objects.create(member=member)
        return redirect('admin/admin_savings_list')
    
    context = {
        'members': members_without_savings
    }
    return render(request, 'admin/admin_add_saving.html', context)

# ==========================================================
# Admin: Add Transactions
# ==========================================================
@login_required
@user_passes_test(is_admin)
def add_transaction(request, saving_id):
    saving_account = get_object_or_404(SavingAccount, pk=saving_id)

    if request.method == "POST":
        transaction_type = request.POST.get('transaction_type')
        amount = request.POST.get('amount')
        description = request.POST.get('description', '')

        if transaction_type and amount:
            amount = float(amount)
            transaction = SavingTransaction.objects.create(
                account=saving_account,
                transaction_type=transaction_type,
                amount=amount,
                description=description
            )
            messages.success(request, f"{transaction_type} of ${amount} added successfully!")
            return redirect('admin_savings_profile', saving_id=saving_account.id)
        else:
            messages.error(request, "Please provide both transaction type and amount.")

    return render(request, 'admin/admin_add_transaction.html', {'account': saving_account})

# ==========================================================
# Admin: Reports
# ==========================================================
def admin_reports(request):
    # ------------------ Member Metrics ------------------
    total_members = Member.objects.count()
    active_members = Member.objects.filter(status='ACTIVE').count()
    pending_members = Member.objects.filter(status='PENDING').count()
    suspended_members = Member.objects.filter(status='SUSPENDED').count()
    exited_members = Member.objects.filter(status='EXITED').count()
    new_members_month = Member.objects.filter(created_at__month=datetime.now().month).count()

    # ------------------ Savings Metrics ------------------
    total_savings = SavingAccount.objects.aggregate(total=Sum('balance'))['total'] or 0
    average_savings = total_savings / total_members if total_members else 0
    highest_saving = SavingAccount.objects.order_by('-balance').first().balance if total_members else 0
    lowest_saving = SavingAccount.objects.order_by('balance').first().balance if total_members else 0

    # Example: Savings Growth per month (last 6 months)
    months = []
    savings_growth = []
    for i in range(5, -1, -1):
        month = (datetime.now() - timedelta(days=i*30)).strftime('%b')
        months.append(month)
        month_total = SavingTransaction.objects.filter(
            transaction_date__month=(datetime.now() - timedelta(days=i*30)).month,
            transaction_type='DEPOSIT'
        ).aggregate(total=Sum('amount'))['total'] or 0
        savings_growth.append(float(month_total))

    # ------------------ Loan Metrics ------------------
    total_loans = Loan.objects.aggregate(total=Sum('principal_amount'))['total'] or 0
    outstanding_loans = Loan.objects.filter(status='approved').aggregate(total=Sum('current_balance'))['total'] or 0
    loan_repayments = LoanRepayment.objects.aggregate(total=Sum('amount_paid'))['total'] or 0
    loans_pending = Loan.objects.filter(status='pending').count()
    loans_approved = Loan.objects.filter(status='approved').count()
    loans_rejected = Loan.objects.filter(status='rejected').count()
    loans_completed = Loan.objects.filter(status='completed').count()

    # Loans approaching due (next 7 days)
    approaching_due_date = datetime.now() + timedelta(days=7)
    loans_approaching_due = Loan.objects.filter(end_date__lte=approaching_due_date, status='approved').count()
    loans_overdue = Loan.objects.filter(end_date__lt=datetime.now(), status='approved').count()

    # ------------------ Financial Metrics ------------------
    # Example profits: sum of interest collected
    profits_made = Loan.objects.aggregate(
        total=Sum(F('principal_amount') * F('interest_rate') / 100)
    )['total'] or 0

    # Membership fees collected
    membership_fees = Member.objects.aggregate(total=Sum('membership_fee_paid'))['total'] or 0

    # Net assets (simplified)
    net_assets = total_savings + outstanding_loans  # adjust for liabilities if you have

    # ------------------ Transaction Metrics ------------------
    recent_transactions = SavingTransaction.objects.order_by('-transaction_date')[:10]

    context = {
        'total_members': total_members,
        'active_members': active_members,
        'pending_members': pending_members,
        'suspended_members': suspended_members,
        'exited_members': exited_members,
        'new_members_month': new_members_month,
        'total_savings': total_savings,
        'average_savings': average_savings,
        'highest_saving': highest_saving,
        'lowest_saving': lowest_saving,
        'months': months,
        'savings_growth': savings_growth,
        'total_loans': total_loans,
        'outstanding_loans': outstanding_loans,
        'loan_repayments': loan_repayments,
        'loans_pending': loans_pending,
        'loans_approved': loans_approved,
        'loans_rejected': loans_rejected,
        'loans_completed': loans_completed,
        'loans_overdue': loans_overdue,
        'loans_approaching_due': loans_approaching_due,
        'profits_made': profits_made,
        'membership_fees': membership_fees,
        'net_assets': net_assets,
        'recent_transactions': recent_transactions,
    }

    return render(request, "admin/admin_reports.html", context)


# ==========================================================
# MEMBER VIEWS
# ==========================================================
@login_required
def member_dashboard(request):
    try:
        member = request.user.member
    except Member.DoesNotExist:
        return redirect('add_member')

    create_savings_account(member)
    create_member_user(member)

    account = getattr(member, 'savingaccount', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []
    recent_balance = transactions.last().balance_after_transaction if transactions else 0.0
    recent_logs = UserActivityLog.objects.filter(member=member).order_by('-timestamp')[:5]
    loan = Loan.objects.filter(member=member).order_by('-start_date').first()
    guarantors = LoanGuarantor.objects.filter(loan=loan) if loan else None
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('-date_paid') if loan else None
    monthly_interest = loan.calculate_monthly_interest() if loan else 0

    return render(request, 'members/member_dashboard.html', {
        'member': member,
        'account': account,
        'transactions': transactions,
        'recent_balance': recent_balance,
        'recent_logs': recent_logs,
        'loan': loan,
        'guarantors': guarantors,
        'repayments': repayments,
        'monthly_interest': monthly_interest,
    })


@login_required
def member_profile(request):
    member = request.user.member
    create_savings_account(member)
    create_member_user(member)
    return render(request, 'members/member_profile.html', {'member': member})


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


@login_required
def member_loans(request):
    member = request.user.member
    loan = Loan.objects.filter(member=member).order_by('-start_date').first()
    guarantors = LoanGuarantor.objects.filter(loan=loan) if loan else None
    repayments = LoanRepayment.objects.filter(loan=loan).order_by('-date_paid') if loan else None
    monthly_interest = loan.calculate_monthly_interest() if loan else 0

    return render(request, 'members/member_loans.html', {
        'member': member,
        'loan': loan,
        'guarantors': guarantors,
        'repayments': repayments,
        'monthly_interest': monthly_interest,
    })


@login_required
def member_savings(request):
    member = request.user.member
    create_savings_account(member)
    account = getattr(member, 'savingaccount', None)
    return render(request, 'members/member_savings.html', {'member': member, 'account': account})


@login_required
def member_transactions(request):
    member = request.user.member
    create_savings_account(member)
    account = getattr(member, 'savingaccount', None)
    transactions = account.transactions.order_by('-transaction_date') if account else []
    return render(request, 'members/member_transactions.html', {'transactions': transactions})


@login_required
def member_support(request):
    member = request.user.member
    return render(request, 'members/member_support.html', {'member': member})


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


# ==========================================================
# ADMIN: Manage Users
# ==========================================================
@login_required
@user_passes_test(lambda u: u.is_staff)
def admin_manage_users(request):
    admins = User.objects.filter(is_staff=True)
    return render(request, 'admin/settings/manage_users.html', {'admins': admins})


# ==========================================================
# MEMBERS MANAGEMENT HOME
# ==========================================================
@login_required
@user_passes_test(is_admin)
def members_management_home(request):
    return render(request, "members/members_management_home.html")
