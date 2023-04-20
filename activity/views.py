from django.shortcuts import render
from .models import Activity


def activity_home(request):
    my_activities = Activity.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'activity/home.html', {'activity_items': my_activities})


