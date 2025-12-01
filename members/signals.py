from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User, Group

from .models import LoanRepayment, Loan, Member, SavingAccount

import string
import random
from django.db.models.signals import post_save
from django.dispatch import receiver


# -----------------------------------------------
#  LOAN REPAYMENT SIGNALS
# -----------------------------------------------

@receiver(post_save, sender=LoanRepayment)
def update_loan_balance_on_save(sender, instance, **kwargs):
    loan = instance.loan
    total_repaid = loan.repayments.aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0
    loan.current_balance = max(loan.principal_amount - total_repaid, 0)

    # Automatically mark as paid if fully repaid
    if loan.current_balance == 0 and loan.status == 'approved':
        loan.status = 'paid'

    loan.save()


@receiver(post_delete, sender=LoanRepayment)
def update_loan_balance_on_delete(sender, instance, **kwargs):
    loan = instance.loan
    total_repaid = loan.repayments.aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0
    loan.current_balance = max(loan.principal_amount - total_repaid, 0)

    # Revert status if balance > 0
    if loan.current_balance > 0 and loan.status == 'paid':
        loan.status = 'approved'

    loan.save()


# -----------------------------------------------
#  MEMBER CREATION SIGNALS
# -----------------------------------------------

@receiver(post_save, sender=Member)
def create_member_accounts(sender, instance, created, **kwargs):
    if created:

        # Create Saving Account for the member only if it doesn't exist
        SavingAccount.objects.get_or_create(member=instance)

        # Create system user if not existing
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

            # Assign Member group
            member_group, _ = Group.objects.get_or_create(name='Member')
            user.groups.add(member_group)

            instance.user = user
            instance.temp_password = True
            instance.save()


# -----------------------------------------------
#  ADMIN NOTIFICATIONS SIGNALS
# -----------------------------------------------
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

        # create admin notification (import inside to avoid circular import issues)
        from .models import AdminNotification  # local import
        AdminNotification.objects.create(
            message=f"New member registered: {instance.first_name} {instance.last_name} ({instance.member_id})",
            notif_type='member',
            related_member=instance)