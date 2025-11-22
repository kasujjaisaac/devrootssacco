from django import forms
from .models import Member, Loan

# ------------------------------
# Admin Add Member Form
# ------------------------------
class AdminAddMemberForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'date_of_birth',
            'address', 'nok_name', 'nok_phone', 'nok_address',
            'employer_name', 'employer_address'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'date_of_birth': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nok_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nok_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'nok_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# ------------------------------
# Admin Update Member Form
# ------------------------------
class MemberUpdateForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = [
            'first_name', 'last_name', 'email', 'phone', 'status',
            'address', 'nok_name', 'nok_phone', 'nok_address',
            'employer_name', 'employer_address'
        ]
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}), 
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'nok_name': forms.TextInput(attrs={'class': 'form-control'}),
            'nok_phone': forms.TextInput(attrs={'class': 'form-control'}),
            'nok_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'employer_name': forms.TextInput(attrs={'class': 'form-control'}),
            'employer_address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

# ------------------------------
# Loan Form
# ------------------------------
class LoanForm(forms.ModelForm):
    class Meta:
        model = Loan
        fields = ['member', 'principal_amount', 'interest_rate', 'status', 'end_date']  # only real fields
        widgets = {
            'member': forms.Select(attrs={'class': 'form-control'}),
            'principal_amount': forms.NumberInput(attrs={'class': 'form-control'}),
            'interest_rate': forms.NumberInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'start_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'end_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
        }

