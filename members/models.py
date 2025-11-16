from django.db import models
from datetime import datetime
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
import uuid
import random
import string
import os

# -------------------- MEMBER MODEL --------------------
class Member(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)

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

    # PROFILE PIC
    profile_pic = models.ImageField(
        upload_to="profile_pics/",
        default="default-avatar.png",
        null=True,
        blank=True
    )

    # NATIONAL ID COPY
    national_id_copy = models.FileField(
        upload_to='national_ids/',
        blank=True,
        null=True,
        help_text='Upload National ID copy (PDF, PNG, JPG, JPEG).'
    )


    # Auto-generated Member ID
    member_id = models.CharField(max_length=20, unique=True, blank=True)

    # Personal Information
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES)
    date_of_birth = models.DateField()
    marital_status = models.CharField(max_length=20, choices=MARITAL_STATUS_CHOICES, blank=True)
    nationality = models.CharField(max_length=50, blank=True)
    district_of_birth = models.CharField(max_length=50, blank=True)
    tribe = models.CharField(max_length=50, blank=True)

    # Contact
    phone = models.CharField(max_length=20)
    email = models.EmailField(blank=True, null=True)
    address = models.TextField()
    preferred_contact = models.CharField(max_length=20, choices=COMMUNICATION_CHOICES, blank=True)

    # KYC / Employment Info
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

    # Next of Kin
    nok_name = models.CharField(max_length=100)
    nok_relationship = models.CharField(max_length=50)
    nok_phone = models.CharField(max_length=20)
    nok_email = models.EmailField(blank=True, null=True)
    nok_address = models.TextField(blank=True)

    # Membership & Savings
    preferred_saving = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    membership_fee_paid = models.DecimalField(max_digits=12, decimal_places=2, default=20000)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='ACTIVE')

    # System Info
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    temp_password = models.BooleanField(default=True)  # Track if password is temporary

    # Auto-generate member ID
    def save(self, *args, **kwargs):
        if not self.member_id:
            year = datetime.now().year
            unique_number = str(uuid.uuid4().int)[:4]
            self.member_id = f"DEV-{year}-{unique_number}"
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.member_id})"

    # Helper Methods
    def get_balance(self):
        if hasattr(self, 'savings_account'):
            return self.savings_account.balance
        return 0

    def recent_transactions(self, limit=5):
        if hasattr(self, 'savings_account'):
            return self.savings_account.transactions.order_by('-transaction_date')[:limit]
        return []

# -------------------- SAVINGS MODELS --------------------
class SavingAccount(models.Model):
    member = models.OneToOneField(Member, on_delete=models.CASCADE, related_name='savings_account')
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    account_created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.member.first_name} {self.member.last_name} - Balance: {self.balance}"


class SavingTransaction(models.Model):
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
        if not self.pk:  # Only calculate on creation
            if self.transaction_type == 'DEPOSIT':
                self.balance_after_transaction = self.account.balance + self.amount
                self.account.balance += self.amount
            elif self.transaction_type == 'WITHDRAWAL':
                self.balance_after_transaction = self.account.balance - self.amount
                self.account.balance -= self.amount
            self.account.save()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} on {self.transaction_date.strftime('%Y-%m-%d')}"

# -------------------- USER ACTIVITY LOG --------------------
class UserActivityLog(models.Model):
    member = models.ForeignKey(Member, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=255)
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __str__(self):
        return f"{self.member} - {self.action} at {self.timestamp}"

# -------------------- SIGNALS --------------------
# Automatically create SavingAccount and Django User with temporary password when a new Member is created
@receiver(post_save, sender=Member)
def create_member_related(sender, instance, created, **kwargs):
    if created:
        # Create SavingAccount
        SavingAccount.objects.create(member=instance)

        # Create Django User if not exists
        if not instance.user:
            password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
            username = f"{instance.first_name.lower()}.{instance.last_name.lower()}.{instance.member_id[-4:]}"
            user = User.objects.create_user(
                username=username,
                email=instance.email or '',
                password=password,
                first_name=instance.first_name,
                last_name=instance.last_name
            )
            instance.user = user
            instance.temp_password = True
            instance.save()
            print(f"Created user for {instance}: username={username}, temp_password={password}")
