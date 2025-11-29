from django.db import models
from datetime import datetime, timedelta
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import random
import string

# ============================================================
#                       MEMBER MODEL
# ============================================================

class Member(models.Model):
    """
    Model representing a SACCO member.
    Each member may have a linked User account for authentication.
    """

    # -----------------------------
    # User Account (optional)
    # -----------------------------
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

    # -----------------------------
    # Choices for member fields
    # -----------------------------
    STATUS_CHOICES = [
        ('PENDING', 'Pending Approval'),
        ('ACTIVE', 'Active'),
        ('SUSPENDED', 'Suspended'),
        ('EXITED', 'Exited'),
    ]

    GENDER_CHOICES = [
        ('Male', 'Male'),
        ('Female', 'Female'),
        ('Other', 'Other'),
        ('Prefer not to say', 'Prefer not to say'),
    ]

    MARITAL_STATUS_CHOICES = [
        ('Single', 'Single'),
        ('Married', 'Married'),
        ('Divorced', 'Divorced'),
        ('Widowed', 'Widowed'),
    ]

    COMMUNICATION_CHOICES = [
        ('SMS', 'SMS'),
        ('Call', 'Call'),
        ('Email', 'Email'),
        ('WhatsApp', 'WhatsApp'),
    ]

    INCOME_RANGE_CHOICES = [
        ('Below 300,000', 'Below 300,000'),
        ('300,000–600,000', '300,000–600,000'),
        ('600,000–1,000,000', '600,000–1,000,000'),
        ('Above 1,000,000', 'Above 1,000,000'),
    ]

    # -----------------------------
    # Profile & KYC
    # -----------------------------
    profile_pic = models.ImageField(upload_to="profile_pics/", default="default-avatar.png",
                                    null=True, blank=True)
    national_id_copy = models.FileField(upload_to='national_ids/', blank=True, null=True,
                                        help_text='Upload National ID copy (PDF, PNG, JPG, JPEG).')
    member_id = models.CharField(max_length=20, unique=True, blank=True)  # Auto-generated

    # -----------------------------
    # Personal Information
    # -----------------------------
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    district_of_birth = models.CharField(max_length=50, blank=True)
    tribe = models.CharField(max_length=50, blank=True)

    # -----------------------------
    # Contact Information
    # -----------------------------
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    preferred_contact = models.CharField(max_length=20, choices=COMMUNICATION_CHOICES, blank=True)

    # -----------------------------
    # Employment & KYC
    # -----------------------------
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

    # -----------------------------
    # Next of Kin
    # -----------------------------
    nok_name = models.CharField(max_length=100)
    nok_relationship = models.CharField(max_length=50)
    nok_phone = models.CharField(max_length=20)
    nok_email = models.EmailField(blank=True, null=True)
    nok_address = models.TextField(blank=True)

    # -----------------------------
    # Membership & Savings
    # -----------------------------
    preferred_saving = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    membership_fee_paid = models.DecimalField(max_digits=12, decimal_places=2, default=20000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # -----------------------------
    # System fields
    # -----------------------------
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    temp_password = models.BooleanField(default=True)

    # -----------------------------
    # Save override: Auto-generate member_id
    # -----------------------------
    def save(self, *args, **kwargs):
        if not self.member_id:
            year = datetime.now().year
            unique_number = uuid.uuid4().hex[:4].upper()
            self.member_id = f"DEV-{year}-{unique_number}"
        super().save(*args, **kwargs)

    # -----------------------------
    # String representation
    # -----------------------------
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_id})"

    # -----------------------------
    # Helper Methods
    # -----------------------------
    def get_balance(self):
        """Return current saving account balance."""
        return self.savings_account.balance if hasattr(self, 'savings_account') else 0

    def recent_transactions(self, limit=5):
        """Return last N transactions for member's saving account."""
        if hasattr(self, 'savings_account'):
            return self.savings_account.transactions.order_by('-transaction_date')[:limit]
        return []

# ============================================================
#                SAVING ACCOUNT & TRANSACTIONS
# ============================================================

class SavingAccount(models.Model):
    """Represents a member's saving account."""
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='savings_account')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    account_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - Balance: {self.balance}"


class SavingTransaction(models.Model):
    """Individual deposit or withdrawal linked to a SavingAccount."""
    TRANSACTION_TYPE_CHOICES = [
        ('DEPOSIT', 'Deposit'),
        ('WITHDRAWAL', 'Withdrawal'),
    ]

    account = models.ForeignKey(SavingAccount, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_date = models.DateTimeField(auto_now_add=True)
    balance_after_transaction = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    description = models.TextField(blank=True)

    def save(self, *args, **kwargs):
        """Update account balance automatically on save."""
        if not self.pk:  # Only on creation
            if self.transaction_type == 'DEPOSIT':
                self.balance_after_transaction = self.account.balance + self.amount
                self.account.balance += self.amount
            else:  # Withdrawal
                self.balance_after_transaction = self.account.balance - self.amount
                self.account.balance -= self.amount
            self.account.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} on {self.transaction_date.strftime('%Y-%m-%d')}"

# ============================================================
#                 USER ACTIVITY LOG
# ============================================================

class UserActivityLog(models.Model):
    """Log member actions for auditing."""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.member} - {self.action} at {self.timestamp}"

# ============================================================
#                     NOTIFICATIONS
# ============================================================

class Notification(models.Model):
    """Member notifications for system updates or support."""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='notifications')
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.first_name} - {'Read' if self.is_read else 'Unread'}"

# ============================================================
#                      SIGNALS
# ============================================================

@receiver(post_save, sender=Member)
def create_member_accounts(sender, instance, created, **kwargs):
    """Automatically create saving account and system user when a member is created."""
    if created:
        # Create Saving Account
        SavingAccount.objects.create(member=instance)

        # Create User account if not exists
        if not instance.user:
            temp_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            username = f"{instance.first_name.lower()}.{instance.last_name.lower()}.{instance.member_id[-4:]}"
            user = User.objects.create_user(
                username=username,
                email=instance.email or "",
                password=temp_password,
                first_name=instance.first_name,
                last_name=instance.last_name,
            )
            instance.user = user
            instance.temp_password = True
            instance.save()

# ============================================================
#                           LOANS
# ============================================================

LOAN_STATUS_CHOICES = [
    ('pending', 'Pending'),
    ('approved', 'Approved'),
    ('rejected', 'Rejected'),
    ('completed', 'Completed'),
]

class Loan(models.Model):
    """Represents a loan taken by a member."""
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='loans')
    principal_amount = models.DecimalField(max_digits=12, decimal_places=2)
    current_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    interest_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0.05)
    start_date = models.DateField(auto_now_add=True)
    loan_term = models.IntegerField(default=12, help_text="Loan term in months")
    end_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=LOAN_STATUS_CHOICES, default='pending')

    def save(self, *args, **kwargs):
        """Set initial balance and end date on creation."""
        if not self.pk:
            self.current_balance = self.principal_amount
            if not self.end_date:
                self.end_date = self.start_date + timedelta(days=self.loan_term*30)
        super().save(*args, **kwargs)

    def calculate_monthly_interest(self):
        """Return monthly interest for the current balance."""
        rate = self.interest_rate / 100
        return self.current_balance * rate

    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - Loan {self.principal_amount}"


class LoanRepayment(models.Model):
    """Represents a repayment made towards a loan."""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='repayments')
    amount_paid = models.DecimalField(max_digits=12, decimal_places=2)
    date_paid = models.DateField(auto_now_add=True)
    balance_after_payment = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    def save(self, *args, **kwargs):
        """Update loan balance and status on repayment."""
        if not self.pk:
            self.balance_after_payment = self.loan.current_balance - self.amount_paid
            self.loan.current_balance -= self.amount_paid
            if self.loan.current_balance <= 0:
                self.loan.current_balance = 0
                self.loan.status = "completed"
            self.loan.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.loan.member.first_name} paid {self.amount_paid} on {self.date_paid}"


class LoanGuarantor(models.Model):
    """Represents a guarantor for a member's loan."""
    loan = models.ForeignKey(Loan, on_delete=models.CASCADE, related_name='guarantors')
    guarantor = models.ForeignKey(Member, on_delete=models.CASCADE)

    # Helper methods
    def guarantor_name(self):
        return f"{self.guarantor.first_name} {self.guarantor.last_name}"

    def guarantor_phone(self):
        return self.guarantor.phone

    def guarantor_email(self):
        return self.guarantor.email

    def __str__(self):
        return f"{self.guarantor.first_name} guarantees {self.loan.member.first_name}"

