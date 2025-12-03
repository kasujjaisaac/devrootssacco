from django.contrib import admin
from .models import (
    Member, SavingAccount, SavingTransaction,
    Loan, LoanRepayment, LoanGuarantor
)

# ============================================================
# INLINE MODELS
# ============================================================

class SavingTransactionInline(admin.TabularInline):
    """Inline for transactions inside SavingAccount admin"""
    model = SavingTransaction
    extra = 0
    readonly_fields = ('balance_after_transaction', 'transaction_date')
    fields = ('transaction_type', 'amount', 'balance_after_transaction', 'transaction_date', 'description')
    can_delete = False
    verbose_name_plural = "Transactions"

class SavingAccountInline(admin.StackedInline):
    """Inline for SavingAccount inside Member admin"""
    model = SavingAccount
    readonly_fields = ('balance', 'account_created')
    extra = 0
    # Transactions are handled separately in SavingAccountAdmin

class LoanGuarantorInline(admin.TabularInline):
    """Inline for guarantors inside Loan admin"""
    model = LoanGuarantor
    extra = 3

class LoanRepaymentInline(admin.TabularInline):
    """Inline for repayments inside Loan admin"""
    model = LoanRepayment
    extra = 0
    readonly_fields = ('date_paid',)


# ============================================================
# MEMBER ADMIN
# ============================================================

@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'first_name', 'last_name', 'gender', 'status', 'membership_fee_paid', 'created_at')
    search_fields = ('member_id', 'first_name', 'last_name', 'national_id', 'phone', 'email')
    list_filter = ('status', 'gender', 'marital_status', 'preferred_contact')
    readonly_fields = ('member_id', 'created_at', 'updated_at')

    fieldsets = (
        ('Member Info', {'fields': ('member_id', 'status'), 'classes': ('collapse',)}),
        ('Personal Info', {'fields': (
            'first_name', 'last_name', 'gender', 'date_of_birth', 'marital_status',
            'nationality', 'district_of_birth', 'tribe', 'profile_pic', 'national_id_copy'),
            'classes': ('collapse',)
        }),
        ('Contact Info', {'fields': ('phone', 'email', 'address', 'preferred_contact'), 'classes': ('collapse',)}),
        ('KYC & Employment Info', {'fields': (
            'national_id', 'occupation', 'employment_status', 'employer_name',
            'employer_department', 'employer_address', 'work_phone', 'income_range',
            'source_of_income', 'tin_number'),
            'classes': ('collapse',)
        }),
        ('Next of Kin', {'fields': ('nok_name', 'nok_relationship', 'nok_phone', 'nok_email', 'nok_address'),
                         'classes': ('collapse',)}),
        ('Membership & Savings', {'fields': ('preferred_saving', 'membership_fee_paid'), 'classes': ('collapse',)}),
        ('System Info', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    inlines = [SavingAccountInline]


# ============================================================
# SAVING ACCOUNT ADMIN
# ============================================================

@admin.register(SavingAccount)
class SavingAccountAdmin(admin.ModelAdmin):
    list_display = ('member', 'balance', 'account_created')
    search_fields = ('member__member_id', 'member__first_name', 'member__last_name')
    readonly_fields = ('balance', 'account_created')
    inlines = [SavingTransactionInline]


# ============================================================
# SAVING TRANSACTION ADMIN
# ============================================================

@admin.register(SavingTransaction)
class SavingTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction_type', 'amount', 'balance_after_transaction', 'transaction_date')
    list_filter = ('transaction_type',)
    search_fields = ('account__member__member_id', 'account__member__first_name', 'account__member__last_name')
    readonly_fields = ('balance_after_transaction', 'transaction_date')


# ============================================================
# LOAN ADMIN
# ============================================================

@admin.register(Loan)
class LoanAdmin(admin.ModelAdmin):
    list_display = ('member', 'principal_amount', 'current_balance', 'status', 'interest_rate', 'start_date')
    search_fields = ('member__member_id', 'member__first_name', 'member__last_name')
    list_filter = ('status',)
    inlines = [LoanGuarantorInline, LoanRepaymentInline]


# ============================================================
# LOAN REPAYMENT ADMIN
# ============================================================

@admin.register(LoanRepayment)
class LoanRepaymentAdmin(admin.ModelAdmin):
    list_display = ('loan', 'amount_paid', 'date_paid')
    search_fields = ('loan__member__first_name', 'loan__member__last_name')
    readonly_fields = ('date_paid',)


# ============================================================
# LOAN GUARANTOR ADMIN
# ============================================================

@admin.register(LoanGuarantor)
class LoanGuarantorAdmin(admin.ModelAdmin):
    list_display = ('loan', 'guarantor_name', 'guarantor_phone', 'guarantor_email')
    search_fields = ('loan__member__first_name', 'loan__member__last_name', 'guarantor_name')
