from django.contrib import admin
from django.utils.html import mark_safe
from django.template.loader import render_to_string

from sass_processor.processor import sass_processor

from . import models
from . import forms

class UnsplashPhotoAdmin(admin.ModelAdmin):

	readonly_fields = ('image_preview', )

	def image_preview(self, obj):
		return mark_safe('<img src="{}" width="{}" />'.format(
			obj.photo_url,
			'30%'
		))

class SlideshowSlideAdmin(admin.TabularInline):
	model = models.SlideshowSlide
	extra = 1

class SlideshowAdmin(admin.ModelAdmin):
	model = models.Slideshow
	inlines = (SlideshowSlideAdmin, )

	readonly_fields = ('slideshow_preview', )

	class Media:
		css = {
			 'all': (
				 sass_processor('unsplash/scss/index.scss'), 
				 'https://cdnjs.cloudflare.com/ajax/libs/uikit/3.0.0-rc.20/css/uikit.min.css', )
		}

		js = (
				'https://cdnjs.cloudflare.com/ajax/libs/uikit/3.0.0-rc.20/js/uikit.min.js',
			)

	def slideshow_preview(self, obj):
		return render_to_string('includes/slideshow.html', {
			'slideshow': obj,
			'slides': obj.slides.order_by('slideshowslide'),
		})

class SlideAdmin(admin.ModelAdmin):
	model = models.Slide
	form = forms.SlideForm

	readonly_fields = ('slide_preview', )

	class Media:
		css = {
			 'all': (
				 sass_processor('unsplash/scss/index.scss'), 
				 sass_processor('unsplash/scss/slide-admin.scss'),
				 'https://cdnjs.cloudflare.com/ajax/libs/uikit/3.0.0-rc.20/css/uikit.min.css', )
		}

		js = (
				'https://cdnjs.cloudflare.com/ajax/libs/uikit/3.0.0-rc.20/js/uikit.min.js',
			)

	def slide_preview(self, obj):
		return render_to_string('includes/slide-admin.html', {
			'slide': obj
		})
		
# Register your models here.
admin.site.register(models.UnsplashPhoto, UnsplashPhotoAdmin)
admin.site.register(models.PhotoGroup)
admin.site.register(models.Slide, SlideAdmin)
admin.site.register(models.Slideshow, SlideshowAdmin)
admin.site.register(models.SeparatorSVG)
admin.site.register(models.Separator)