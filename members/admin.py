from django.contrib import admin
from .models import Member, SavingAccount, SavingTransaction

# -------------------- INLINE TRANSACTIONS --------------------
class SavingTransactionInline(admin.TabularInline):
    model = SavingTransaction
    extra = 0
    readonly_fields = ('balance_after_transaction', 'transaction_date')
    fields = ('transaction_type', 'amount', 'balance_after_transaction', 'transaction_date', 'description')
    can_delete = False
    verbose_name_plural = "Transactions"

# -------------------- INLINE SAVING ACCOUNT --------------------
class SavingAccountInline(admin.StackedInline):
    model = SavingAccount
    readonly_fields = ('balance', 'account_created')
    extra = 0
    inlines = [SavingTransactionInline]  # Transactions inline under account

# -------------------- MEMBER ADMIN --------------------
@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    list_display = ('member_id', 'first_name', 'last_name', 'gender', 'status', 'membership_fee_paid', 'created_at')
    search_fields = ('member_id', 'first_name', 'last_name', 'national_id', 'phone', 'email')
    list_filter = ('status', 'gender', 'marital_status', 'preferred_contact')
    readonly_fields = ('member_id', 'created_at', 'updated_at')

    fieldsets = (
        ('Member Info', {'fields': ('member_id', 'status'), 'classes': ('collapse',)}),
        ('Personal Info', {
            'fields': ('first_name', 'last_name', 'gender', 'date_of_birth', 'marital_status', 'nationality', 'district_of_birth', 'tribe','profile_pic', 'national_id_copy'),
            'classes': ('collapse',)
        }),
        ('Contact Info', {'fields': ('phone', 'email', 'address', 'preferred_contact'), 'classes': ('collapse',)}),
        ('KYC & Employment Info', {
            'fields': (
                'national_id', 'occupation', 'employment_status', 'employer_name', 'employer_department',
                'employer_address', 'work_phone', 'income_range', 'source_of_income', 'tin_number'
            ),
            'classes': ('collapse',)
        }),
        ('Next of Kin', {'fields': ('nok_name', 'nok_relationship', 'nok_phone', 'nok_email', 'nok_address'), 'classes': ('collapse',)}),
        ('Membership & Savings', {'fields': ('preferred_saving', 'membership_fee_paid'), 'classes': ('collapse',)}),
        ('System Info', {'fields': ('created_at', 'updated_at'), 'classes': ('collapse',)}),
    )

    inlines = [SavingAccountInline]  # Display member’s saving account and transactions inline

# -------------------- SAVING ACCOUNT ADMIN --------------------
@admin.register(SavingAccount)
class SavingAccountAdmin(admin.ModelAdmin):
    list_display = ('member', 'balance', 'account_created')
    search_fields = ('member__member_id', 'member__first_name', 'member__last_name')
    readonly_fields = ('balance', 'account_created')
    inlines = [SavingTransactionInline]  # Show transactions inline under account

# -------------------- SAVING TRANSACTION ADMIN --------------------
@admin.register(SavingTransaction)
class SavingTransactionAdmin(admin.ModelAdmin):
    list_display = ('account', 'transaction_type', 'amount', 'balance_after_transaction', 'transaction_date')
    list_filter = ('transaction_type',)
    search_fields = ('account__member__member_id', 'account__member__first_name', 'account__member__last_name')
    readonly_fields = ('balance_after_transaction', 'transaction_date')
