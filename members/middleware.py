from django.shortcuts import redirect
from django.urls import reverse

class ForcePasswordChangeMiddleware:
    """
    Force users with temp_password=True to change password
    before accessing any page except logout and change_password.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            member = getattr(request.user, 'member', None)
            if member and getattr(member, 'temp_password', False):
                allowed_paths = [reverse('change_password'), reverse('member_logout')]
                if request.path not in allowed_paths:
                    return redirect('change_password')
        return self.get_response(request)
