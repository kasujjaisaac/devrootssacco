from django import forms
from .models import Member

class AdminAddMemberForm(forms.ModelForm):
    class Meta:
        model = Member
        # Exclude fields that admin shouldn't fill manually
        exclude = ('user', 'member_id', 'created_at', 'updated_at', 'status', 'membership_fee_paid')
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows':3}),
            'nok_address': forms.Textarea(attrs={'rows':3}),
            'employer_address': forms.Textarea(attrs={'rows':3}),
        }
