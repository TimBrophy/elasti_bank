from django.shortcuts import render
from django.views.generic import ListView, TemplateView

from .models import UnsplashPhoto
from threading import Thread, Lock
from timeit import timeit
import time

class PhotosListView(ListView):
	model = UnsplashPhoto
	template_name = 'unsplash/index.html'
	context_object_name = 'photos'

class RandomPhotosTemplateView(TemplateView):
	template_name = 'unsplash/random_photos.html'

	def get_context_data(self, **kwargs):
		print('Give me {} random photos'.format(kwargs.get('num')))
		kwargs['random_photos'] = [UnsplashPhoto.random('full') for _ in range(kwargs.get('num'))]
		return kwargs