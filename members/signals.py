from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import LoanRepayment, Loan

# Update loan balance after repayment is added
@receiver(post_save, sender=LoanRepayment)
def update_loan_balance_on_save(sender, instance, **kwargs):
    loan = instance.loan
    total_repaid = loan.repayments.aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0
    loan.current_balance = max(loan.principal_amount - total_repaid, 0)
    
    # Automatically mark as paid if fully repaid
    if loan.current_balance == 0 and loan.status == 'approved':
        loan.status = 'paid'
    
    loan.save()


# Update loan balance if a repayment is deleted
@receiver(post_delete, sender=LoanRepayment)
def update_loan_balance_on_delete(sender, instance, **kwargs):
    loan = instance.loan
    total_repaid = loan.repayments.aggregate(models.Sum('amount_paid'))['amount_paid__sum'] or 0
    loan.current_balance = max(loan.principal_amount - total_repaid, 0)
    
    # Revert status if balance > 0
    if loan.current_balance > 0 and loan.status == 'paid':
        loan.status = 'approved'
    
    loan.save()
