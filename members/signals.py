from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import models
from django.contrib.auth.models import User, Group
from django.utils import timezone

from .models import LoanRepayment, Loan, Member, SavingAccount, AdminNotification

import string
import random

# ==========================================================
# LOAN REPAYMENT SIGNALS
# ==========================================================
@receiver(post_save, sender=LoanRepayment)
def update_loan_balance_on_save(sender, instance, **kwargs):
    """
    Automatically update loan balance when a repayment is added.
    Mark loan as 'paid' if fully repaid.
    """
    loan = instance.loan
    total_repaid = loan.repayments.aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0
    loan.current_balance = max(loan.principal_amount - total_repaid, 0)

    if loan.current_balance == 0 and loan.status == 'approved':
        loan.status = 'paid'

    loan.save()


@receiver(post_delete, sender=LoanRepayment)
def update_loan_balance_on_delete(sender, instance, **kwargs):
    """
    Automatically update loan balance when a repayment is deleted.
    Revert loan status to 'approved' if balance > 0.
    """
    loan = instance.loan
    total_repaid = loan.repayments.aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0
    loan.current_balance = max(loan.principal_amount - total_repaid, 0)

    if loan.current_balance > 0 and loan.status == 'paid':
        loan.status = 'approved'

    loan.save()


# ==========================================================
# ADMIN NOTIFICATIONS SIGNALS
# ==========================================================
@receiver(post_save, sender=Member)
def notify_admin_on_new_member(sender, instance, created, **kwargs):
    """
    Notify admin when a new member is created.
    Does NOT create saving accounts or user accounts (handled in views).
    """
    if created:
        AdminNotification.objects.create(
            message=f"New member registered: {instance.first_name} {instance.last_name} ({instance.member_id})",
            notif_type='member',
            related_member=instance
        )
