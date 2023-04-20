from django.shortcuts import render, get_object_or_404
from content.models import ContentSeries, ContentItem
from activity.models import Activity,ActivityType
from django.contrib.auth.decorators import login_required
from accounts.models import CustomUser
from activity.models import ContentItem
from datetime import datetime, timezone

def content_home(request):
    series_list = ContentSeries.objects.all()
    return render(request, 'content/home.html', {'series_list': series_list})


@login_required
def content_list(request, id):
    content_items = ContentItem.objects.filter(series=id)
    series = ContentSeries.objects.get(id=id)
    return render(request, 'content/list.html', {'content_items': content_items, 'series': series})


@login_required
def content_detail(request, id):
    content_item = ContentItem.objects.get(id=id)
    activity_log_message = "Viewed: {}".format(ContentItem.objects.get(id=id))
    activity_type = ActivityType.objects.get(id=1)
    activity_entry = Activity(user=request.user, activity_log_message=activity_log_message,
                              created_at=datetime.now(tz=timezone.utc), activitytype=activity_type)
    activity_entry.save()
    return render(request, 'content/detail.html', {'content_item': content_item})