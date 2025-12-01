from django import forms
from .models import Member, Loan
from .models import LoanRepayment
from .models import SystemSetting
from members.models import Role


# ---------------------------------------------------
# Admin Add Member Form  (with validations)
# ---------------------------------------------------
class AdminAddMemberForm(forms.ModelForm):

    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'gender', 'date_of_birth', 'marital_status',
            'nationality', 'district_of_birth', 'tribe', 'profile_pic', 'national_id',
            'national_id_copy', 'phone', 'email', 'address', 'preferred_contact',
            'occupation', 'employment_status', 'employer_name', 'employer_department',
            'employer_address', 'work_phone', 'income_range', 'source_of_income',
            'tin_number', 'nok_name', 'nok_relationship', 'nok_phone', 'nok_email',
            'nok_address', 'preferred_saving', 'membership_fee_paid'
        ]

        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.Select(attrs={'class': 'form-select'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'marital_status': forms.Select(attrs={'class': 'form-select'}),
            'nationality': forms.TextInput(attrs={'class': 'form-control'}),
            'district_of_birth': forms.TextInput(attrs={'class': 'form-control'}),
            'tribe': forms.TextInput(attrs={'class': 'form-control'}),

            'profile_pic': forms.FileInput(attrs={'class': 'form-control'}),
            'national_id': forms.TextInput(attrs={'class': 'form-control'}),
            'national_id_copy': forms.FileInput(attrs={'class': 'form-control'}),

            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'preferred_contact': forms.Select(attrs={'class': 'form-select'}),

            'occupation': forms.TextInput(attrs={'class': 'form-control'}),
            'employment_status': forms.TextInput(attrs={'class': 'form-control'}),  # ✔ textbox

            'employer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employer_department': forms.TextInput(attrs={'class': 'form-control'}),
            'employer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'work_phone': forms.TextInput(attrs={'class': 'form-control'}),

            'income_range': forms.Select(attrs={'class': 'form-select'}),  # ✔ dropdown

            'source_of_income': forms.TextInput(attrs={'class': 'form-control'}),
            'tin_number': forms.TextInput(attrs={'class': 'form-control'}),

            'nok_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nok_relationship': forms.TextInput(attrs={'class': 'form-control'}),
            'nok_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'nok_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nok_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),

            'preferred_saving': forms.TextInput(attrs={'class': 'form-control'}),  # ✔ textbox

            'membership_fee_paid': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    # ---------------------------------------------------
    # FIELD-LEVEL VALIDATION (clear error messages)
    # ---------------------------------------------------

    def clean_phone(self):
        phone = self.cleaned_data.get("phone")
        if phone and not phone.isdigit():
            raise forms.ValidationError("Phone number must contain digits only.")
        if phone and len(phone) < 10:
            raise forms.ValidationError("Phone number must be at least 10 digits.")
        return phone

    def clean_work_phone(self):
        work_phone = self.cleaned_data.get("work_phone")
        if work_phone and not work_phone.isdigit():
            raise forms.ValidationError("Work phone must contain digits only.")
        return work_phone

    def clean_national_id(self):
        nin = self.cleaned_data.get("national_id")
        if nin and len(nin) < 13:
            raise forms.ValidationError("National ID (NIN) must be at least 13 characters.")
        return nin

    def clean_nok_phone(self):
        phone = self.cleaned_data.get("nok_phone")
        if phone and not phone.isdigit():
            raise forms.ValidationError("Next of Kin phone must contain digits only.")
        return phone

    def clean_preferred_saving(self):
        saving = self.cleaned_data.get("preferred_saving")
        if saving:
            try:
                float(saving)
            except ValueError:
                raise forms.ValidationError("Preferred saving must be a valid number.")
        return saving

    # ---------------------------------------------------
    # FORM-WIDE VALIDATION
    # ---------------------------------------------------
    def clean(self):
        cleaned_data = super().clean()

        employment_status = cleaned_data.get("employment_status")
        if employment_status and len(employment_status) < 3:
            self.add_error(
                "employment_status",
                "Employment status must be at least 3 characters long."
            )

        return cleaned_data


# ---------------------------------------------------
# Admin Update Form (inherits validations)
# ---------------------------------------------------
class MemberUpdateForm(AdminAddMemberForm):
    class Meta(AdminAddMemberForm.Meta):
        fields = AdminAddMemberForm.Meta.fields + ['status']
        widgets = AdminAddMemberForm.Meta.widgets.copy()
        widgets['status'] = forms.Select(attrs={'class': 'form-select'})


# ---------------------------------------------------
# Loan Form
# ---------------------------------------------------
class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['member', 'principal_amount', 'interest_rate', 'status', 'end_date']
        widgets = {
            'member': forms.Select(attrs={'class': 'form-select'}),
            'principal_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-select'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }
class LoanGuarantorForm(forms.Form):
    guarantor1 = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Guarantor 1"
    )
    guarantor2 = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Guarantor 2"
    )
    guarantor3 = forms.ModelChoiceField(
        queryset=Member.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Guarantor 3"
    )

class LoanRepaymentForm(forms.ModelForm):
    class Meta:
        model = LoanRepayment
        fields = ['loan', 'amount_paid', 'receipt']
        widgets = {
            'loan': forms.Select(attrs={'class': 'form-select'}),
            'amount_paid': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter repayment amount',
                'step': '0.01'
            }),
            'receipt': forms.FileInput(attrs={'class': 'form-control'}),
        }
        help_texts = {
            'receipt': 'Upload a bank payment receipt (PDF, JPG, PNG).',
        }

    def clean_amount_paid(self):
        amount = self.cleaned_data.get('amount_paid')
        if amount <= 0:
            raise forms.ValidationError("Repayment amount must be greater than zero.")
        return amount

    def clean_receipt(self):
        receipt = self.cleaned_data.get('receipt')
        if not receipt:
            raise forms.ValidationError("Please upload the bank payment receipt.")
        return receipt
    
# ---------------------------------------------------
# System Settings Form
# ---------------------------------------------------
class SystemSettingForm(forms.ModelForm):
    class Meta:
        model = SystemSetting
        fields = '__all__'
        widgets = {
            'address': forms.Textarea(attrs={'rows': 3}),
        }

# ---------------------------------------------------
# Roles Form
# ---------------------------------------------------
PERMISSION_CHOICES = [
    ("view_dashboard", "View Dashboard"),
    ("manage_members", "Manage Members"),
    ("manage_savings", "Manage Savings"),
    ("manage_loans", "Manage Loans"),
    ("manage_reports", "View Reports"),
    ("manage_support", "Support & Tickets"),
    ("manage_settings", "System Settings"),
]

class RoleForm(forms.ModelForm):
    permissions = forms.MultipleChoiceField(
        choices=PERMISSION_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Permissions"
    )

    class Meta:
        model = Role
        fields = ["name", "description", "permissions"]

    def clean_permissions(self):
        return self.cleaned_data.get("permissions", [])
