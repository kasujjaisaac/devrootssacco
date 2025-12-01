from django.db import models
from django.contrib.auth.models import User

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # JSON list of permissions
    permissions = models.JSONField(default=list)

    def __str__(self):
        return self.name

    def permissions_list(self):
        return ", ".join(self.permissions)
    

class UserRole(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True)

    def __str__(self):
        return f"{self.user.username} → {self.role.name}"
