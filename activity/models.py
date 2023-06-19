from django.db import models
from accounts.models import CustomUser


class ActivityType(models.Model):
    name = models.CharField(max_length=52, null=False)
    class Meta:
        verbose_name_plural = "Activity types"
    def __str__(self):
        return self.name



class Activity(models.Model):
    activitytype = models.ForeignKey(ActivityType, on_delete=models.CASCADE, null=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    activity_log_message = models.CharField(max_length=256, null=True)
    location = models.CharField(max_length=256, null=True)

    class Meta:
        verbose_name_plural = "Activities"

    def __str__(self):
        return self.activitytype, self.user
