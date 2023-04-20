from django.contrib import admin
from django.urls import path

from .views import PhotosListView, RandomPhotosTemplateView

app_name = 'unsplash_photos'
urlpatterns = [
	path('', PhotosListView.as_view(), name='photos-list'),
	path('random-photos/<int:num>', RandomPhotosTemplateView.as_view(), name='random-photos')
]