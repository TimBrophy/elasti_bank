from django.db import models
from django.contrib.auth.models import AbstractUser

class IncomeLevel(models.Model):
    category = models.CharField(max_length=56, null=False)
    lower = models.IntegerField(null=False)
    upper = models.IntegerField(null=False)


class CustomUser(AbstractUser):
    phone_number = models.CharField(max_length=20, null=True, blank=True)
    birthdate = models.DateField(null=True, blank=True)
    income_level = models.ForeignKey(IncomeLevel, on_delete=models.CASCADE, null=False)

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return self.email
