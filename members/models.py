from django.db import models
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import random
import string
from decimal import Decimal
from django.core.exceptions import ValidationError
from django.utils import timezone
from decimal import Decimal, ROUND_HALF_UP


# ============================================================
#                       MEMBER MODEL
# ============================================================


class Member(models.Model):
    """
    Model representing a SACCO member.
    Each member may have a linked User account for authentication.
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    STATUS_CHOICES = [
        ("PENDING", "Pending Approval"),
        ("ACTIVE", "Active"),
        ("SUSPENDED", "Suspended"),
        ("EXITED", "Exited"),
    ]

    GENDER_CHOICES = [
        ("Male", "Male"),
        ("Female", "Female"),
        ("Other", "Other"),
        ("Prefer not to say", "Prefer not to say"),
    ]

    MARITAL_STATUS_CHOICES = [
        ("Single", "Single"),
        ("Married", "Married"),
        ("Divorced", "Divorced"),
        ("Widowed", "Widowed"),
    ]

    COMMUNICATION_CHOICES = [
        ("SMS", "SMS"),
        ("Call", "Call"),
        ("Email", "Email"),
        ("WhatsApp", "WhatsApp"),
    ]

    INCOME_RANGE_CHOICES = [
        ("Below 300,000", "Below 300,000"),
        ("300,000–600,000", "300,000–600,000"),
        ("600,000–1,000,000", "600,000–1,000,000"),
        ("Above 1,000,000", "Above 1,000,000"),
    ]

    profile_pic = models.ImageField(
        upload_to="profile_pics/", default="default-avatar.png", null=True, blank=True
    )
    national_id_copy = models.FileField(
        upload_to="national_ids/", blank=True, null=True, help_text="Upload National ID copy (PDF, PNG, JPG, JPEG)."
    )
    member_id = models.CharField(max_length=30, unique=True, blank=True)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    district_of_birth = models.CharField(max_length=50, blank=True)
    tribe = models.CharField(max_length=50, blank=True)

    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    preferred_contact = models.CharField(max_length=20, choices=COMMUNICATION_CHOICES, blank=True)

    national_id = models.CharField(max_length=20, unique=True)
    occupation = models.CharField(max_length=100, blank=True, null=True)
    employment_status = models.CharField(max_length=50, blank=True)
    employer_name = models.CharField(max_length=100, blank=True)
    employer_department = models.CharField(max_length=50, blank=True)
    employer_address = models.TextField(blank=True)
    work_phone = models.CharField(max_length=20, blank=True)
    income_range = models.CharField(max_length=50, choices=INCOME_RANGE_CHOICES, blank=True)
    source_of_income = models.CharField(max_length=50, blank=True)
    tin_number = models.CharField(max_length=50, blank=True, null=True)

    nok_name = models.CharField(max_length=100)
    nok_relationship = models.CharField(max_length=50)
    nok_phone = models.CharField(max_length=20)
    nok_email = models.EmailField(blank=True, null=True)
    nok_address = models.TextField(blank=True)

    preferred_saving = models.CharField(max_length=50, blank=True)
    membership_fee_paid = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="ACTIVE")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    temp_password = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]

    def save(self, *args, **kwargs):
        # Auto-generate member_id only once when creating
        if not self.member_id:
            year = datetime.now().year
            unique_number = uuid.uuid4().hex[:6].upper()
            self.member_id = f"DEV-{year}-{unique_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_id})"

    def get_balance(self):
        return self.savings_account.balance if hasattr(self, "savings_account") else Decimal("0.00")

    def recent_transactions(self, limit=5):
        if hasattr(self, "savings_account"):
            return self.savings_account.transactions.order_by("-transaction_date")[:limit]
        return []


# ============================================================
#                SAVING ACCOUNT & TRANSACTIONS
# ============================================================


class SavingAccount(models.Model):
    """Represents a member's saving account (one-to-one with Member)."""
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name="savings_account")
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    account_created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-account_created"]

    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - Balance: {self.balance}"


class SavingTransaction(models.Model):
    """Individual deposit or withdrawal linked to a SavingAccount."""

    TRANSACTION_TYPE_CHOICES = [
        ("DEPOSIT", "Deposit"),
        ("WITHDRAWAL", "Withdrawal"),
    ]

    account = models.ForeignKey(SavingAccount, on_delete=models.CASCADE, related_name="transactions")
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    description = models.TextField(blank=True)

    class Meta:
        ordering = ["-transaction_date"]

    def clean(self):
        if self.amount <= 0:
            raise ValidationError("Transaction amount must be greater than zero.")
        if self.transaction_type == "WITHDRAWAL" and self.amount > self.account.balance:
            raise ValidationError("Insufficient balance for withdrawal.")

    def save(self, *args, **kwargs):
        # Ensure validation is run
        self.clean()

        is_new = self.pk is None

        if is_new:
            amt = Decimal(self.amount)
            if self.transaction_type == "DEPOSIT":
                self.balance_after_transaction = self.account.balance + amt
                self.account.balance += amt
            else:  # WITHDRAWAL
                self.balance_after_transaction = self.account.balance - amt
                self.account.balance -= amt

            # Persist account balance first to avoid race conditions (ideally inside a transaction)
            self.account.save()

        super().save(*args, **kwargs)

        if is_new:
            # create admin notification - import locally to avoid circular imports
            from .models import AdminNotification  # noqa: F401 - local import

            AdminNotification.objects.create(
                message=(
                    f"{self.transaction_type.title()} of UGX {self.amount:,} by "
                    f"{self.account.member.first_name} {self.account.member.last_name} "
                    f"({self.account.member.member_id})"
                ),
                notif_type="saving",
                related_saving=self,
                related_member=self.account.member,
            )


# ============================================================
#                 USER ACTIVITY LOG
# ============================================================


class UserActivityLog(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="activity_logs")
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.member} - {self.action} at {self.timestamp}"


# ============================================================
#                     NOTIFICATIONS
# ============================================================


class Notification(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="notifications")
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)
    is_support = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.member.first_name} - {'Read' if self.is_read else 'Unread'}"


class AdminNotification(models.Model):
    NOTIF_TYPE_CHOICES = [
        ("member", "Member"),
        ("saving", "Saving"),
        ("loan", "Loan"),
        ("system", "System"),
        ("other", "Other"),
    ]

    message = models.TextField()
    notif_type = models.CharField(max_length=30, choices=NOTIF_TYPE_CHOICES, default="other")
    related_member = models.ForeignKey(
        "Member", on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_notifications"
    )
    related_loan = models.ForeignKey(
        "Loan", on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_notifications"
    )
    related_saving = models.ForeignKey(
        "SavingTransaction", on_delete=models.SET_NULL, null=True, blank=True, related_name="admin_notifications"
    )
    created_at = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        status = "Read" if self.is_read else "Unread"
        return f"[{self.get_notif_type_display()}] {status} - {self.message[:60]}"


# ============================================================
#                           LOANS
# ============================================================


LOAN_STATUS_CHOICES = [
    ("pending", "Pending"),
    ("approved", "Approved"),
    ("rejected", "Rejected"),
    ("completed", "Completed"),
]


class Loan(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name="loans")
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    interest_rate = models.DecimalField(max_digits=5, decimal_places=4, blank=True, null=True)  # e.g., 0.05 for 5%
    start_date = models.DateField(auto_now_add=True)
    loan_term = models.IntegerField(default=12, help_text="Loan term in months")
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default="pending")

    class Meta:
        ordering = ["-start_date"]

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        # Set default interest rate from system settings if not provided
        if is_new and (self.interest_rate is None):
            system_setting = SystemSetting.objects.first()
            self.interest_rate = Decimal(system_setting.default_loan_interest_rate / 100) if system_setting else Decimal("0.05")

        if is_new:
            self.current_balance = self.principal_amount
            if not self.end_date:
                # Approximate month by 30 days, or use dateutil.relativedelta for precise months
                self.end_date = self.start_date + timedelta(days=self.loan_term * 30)

        super().save(*args, **kwargs)

        if is_new:
            # Create admin notification
            AdminNotification.objects.create(
                message=(
                    f"Loan request: {self.member.first_name} {self.member.last_name} "
                    f"requested UGX {self.principal_amount:,}. Loan ID: {self.id}"
                ),
                notif_type="loan",
                related_loan=self,
                related_member=self.member,
            )

    # ===========================
    # Financial Methods
    # ===========================

    def calculate_monthly_interest(self):
        """
        Returns monthly interest as Decimal.
        """
        return (self.principal_amount * self.interest_rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def calculate_total_payable(self):
        """
        Returns total payable amount over the full loan term (principal + interest).
        """
        monthly_interest = self.calculate_monthly_interest()
        total_interest = monthly_interest * self.loan_term
        return (self.principal_amount + total_interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

    def remaining_balance(self, months_paid):
        """
        Returns remaining balance (principal + remaining interest) after given months paid.
        """
        if months_paid > self.loan_term:
            months_paid = self.loan_term

        monthly_interest = self.calculate_monthly_interest()
        principal_paid = (self.principal_amount / self.loan_term) * months_paid
        remaining_principal = self.principal_amount - principal_paid
        remaining_interest = monthly_interest * (self.loan_term - months_paid)
        return (remaining_principal + remaining_interest).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

class LoanRepayment(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="repayments")
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    receipt = models.FileField(upload_to="loan_receipts/", blank=True, null=True, help_text="Upload bank receipt (PDF, JPG, PNG)")
    date_paid = models.DateField(auto_now_add=True)
    balance_after_payment = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def save(self, *args, **kwargs):
        is_new = self.pk is None

        if is_new:
            self.balance_after_payment = self.loan.current_balance - self.amount_paid
            self.loan.current_balance -= self.amount_paid
            if self.loan.current_balance <= 0:
                self.loan.current_balance = Decimal("0.00")
                self.loan.status = "completed"
            self.loan.save()

        super().save(*args, **kwargs)

        if is_new:
            AdminNotification.objects.create(
                message=(
                    f"Loan repayment of UGX {self.amount_paid:,} for Loan #{self.loan.id} "
                    f"by {self.loan.member.first_name} {self.loan.member.last_name}."
                ),
                notif_type="loan",
                related_loan=self.loan,
                related_member=self.loan.member,
            )


class LoanGuarantor(models.Model):
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name="guarantors")
    guarantor = models.ForeignKey(Member, on_delete=models.CASCADE)

    def guarantor_name(self):
        return f"{self.guarantor.first_name} {self.guarantor.last_name}"

    def guarantor_phone(self):
        return self.guarantor.phone

    def guarantor_email(self):
        return self.guarantor.email

    def __str__(self):
        return f"{self.guarantor.first_name} guarantees {self.loan.member.first_name}"


# ============================================================
# MEMBER SUPPORT REQUEST
# ============================================================


class SupportRequest(models.Model):
    SUPPORT_CATEGORIES = [
        ("personal_info", "Updating Personal Information"),
        ("financial_guidance", "Financial Literacy / Guidance"),
        ("service_issue", "Service Issues"),
        ("transaction_error", "Incorrect Deductions or Errors"),
        ("staff_behavior", "Staff Behavior"),
        ("other", "Other / Miscellaneous"),
    ]

    member = models.ForeignKey("Member", on_delete=models.CASCADE, related_name="support_requests")
    category = models.CharField(max_length=50, choices=SUPPORT_CATEGORIES)
    question = models.TextField()
    response = models.TextField(blank=True, null=True)
    is_resolved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    responded_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.member} - {self.get_category_display()} - {'Resolved' if self.is_resolved else 'Pending'}"


# ============================================================
# MEMBER SYSTEM SETTINGS
# ============================================================


class SystemSetting(models.Model):
    sacco_name = models.CharField(max_length=255, default="Devroots SACCO")
    address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    logo = models.ImageField(upload_to="system_logos/", blank=True, null=True)
    default_membership_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    default_loan_interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=10.0)
    max_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, default=1000000)
    min_loan_amount = models.DecimalField(max_digits=15, decimal_places=2, default=10000)
    loan_repayment_period_days = models.IntegerField(default=90)
    notifications_enabled = models.BooleanField(default=True)

    def __str__(self):
        return "System Settings"


# ============================================================
# SYSTEM ROLES
# ============================================================


class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    permissions = models.JSONField(default=list, blank=True)

    def __str__(self):
        return self.name

    @property
    def permissions_list(self):
        return ", ".join(self.permissions)


class UserRole(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_role")
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True, related_name="users")

    def __str__(self):
        return f"{self.user.username} -> {self.role.name if self.role else 'No role'}"


# ============================================================
# SIGNALS: create SavingAccount and User on Member creation
# ============================================================


@receiver(post_save, sender=Member)
def create_member_accounts(sender, instance, created, **kwargs):
    """Automatically create saving account and system user when a member is created.

    Uses get_or_create for the saving account to avoid UNIQUE constraint errors.
    """
    if created:
        # create or get saving account (safe even if another process already created it)
        SavingAccount.objects.get_or_create(member=instance)

        # create User account if not exists
        if not instance.user:
            temp_password = "".join(random.choices(string.ascii_letters + string.digits, k=8))
            username = f"{instance.first_name.lower()}.{instance.last_name.lower()}.{instance.member_id[-6:]}"
            user = User.objects.create_user(
                username=username,
                email=instance.email or "",
                password=temp_password,
                first_name=instance.first_name,
                last_name=instance.last_name,
            )
            # assign user and update instance without triggering full recursive flow
            Member.objects.filter(pk=instance.pk).update(user=user, temp_password=True)
