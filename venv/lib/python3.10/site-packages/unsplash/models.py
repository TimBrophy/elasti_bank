from django.db import models
from django.contrib.staticfiles.templatetags.staticfiles import static
from django.core.validators import MinValueValidator

from unsplashpy import Photo
import os
import requests

from PIL import Image
import io

class UnsplashPhoto(models.Model):
	IMAGE_SIZES = (
		('full', 'Full'),
		('regular', 'Regular'),
		('small', 'Small'),
		('thumb', 'Thumb')
	)

	photo_id = models.CharField(max_length=11)
	photo_size = models.CharField(max_length=7, choices=IMAGE_SIZES, default='regular')
	photo_alias = models.CharField(max_length=30)
	photo_url = models.URLField(editable=False)
	downloaded = models.BooleanField(default=False)

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.previous_alias = self.photo_alias
		self.previous_size = self.photo_size
		self.was_downloaded = self.downloaded

	@property
	def url(self):
		if not self.downloaded:
			return self.photo_url
		
		if os.path.isfile(static(os.path.join('unsplash', self.photo_alias + '.jpg'))[1:]):
			return static(os.path.join('unsplash', self.photo_alias + '.jpg'))

		return static(os.path.join('unsplash', self.photo_alias + '.webp'))

	def save_photo(self, photo_path):
		if not os.path.isdir(os.path.dirname(photo_path)):
			os.makedirs(os.path.dirname(photo_path))
			
		# with open(photo_path, 'wb') as pf:
		# 	pf.write(requests.get(self.photo_url).content)

		# im = Image.open(photo_path)
		# im.save(os.path.join(os.path.dirname(photo_path), 'webp_'+os.path.splitext(os.path.basename(photo_path))[0]+'.webp'), 'webp', quality=70)
		im = Image.open(io.BytesIO(requests.get(self.photo_url).content))
		width, height = im.size

		if width > 2400:
			im = im.resize((2400, int(height * 2400 / width)))

		im.save(photo_path, 'webp', quality=80)

	def remove_photo(self, photo_path):
		if os.path.isfile(photo_path):
			os.remove(photo_path)

	def rename_photo(self, original_path, new_path):
		if os.path.isfile(original_path):
			os.rename(original_path, new_path)
	
	def save(self, *args, **kwargs):
		self.photo_url = Photo(self.photo_id).urls._asdict()[self.photo_size]

		filename = os.path.join('static', 'unsplash/{}.webp'.format(self.photo_alias))

		if self.previous_alias != self.photo_alias and self.previous_alias != '':
			previous_path = os.path.join('static', 'unsplash/{}.webp'.format(self.previous_alias))

			if self.previous_size != self.photo_size:
				self.remove_photo(previous_path)
				self.save_photo(filename)
			else:
				self.rename_photo(previous_path, filename)
		else:
			if self.downloaded:
				if not os.path.isfile(filename):
					self.save_photo(filename)
				elif self.photo_size != self.previous_size:
					self.save_photo(filename)
			else:
				self.remove_photo(filename)

		super().save(*args, **kwargs)

	def delete(self):
		if self.downloaded:
			filename = os.path.join('static', 'unsplash/{}.webp'.format(self.photo_alias))
			self.remove_photo(filename)

		super().delete()
	
	@classmethod
	def random(cls, size):
		random_p = Photo.random()
		return cls(photo_id=random_p.id, photo_size=size, photo_alias='', photo_url=random_p.urls._asdict()[size])

	def __str__(self):
		return 'Photo(id="{}", size="{}", alias="{}")'.format(self.photo_id, self.photo_size, self.photo_alias)

class PhotoGroup(models.Model):
	name = models.CharField(max_length=30, blank=False, null=False)
	photos = models.ManyToManyField(UnsplashPhoto)

class Slide(models.Model):
	photos = models.ManyToManyField(UnsplashPhoto)
	ken_burns_effect = models.BooleanField(default=False)
	content_overlay_html = models.TextField(blank=True, null=True)
	fixed = models.BooleanField(default=False)
	parallax = models.IntegerField(default=0, help_text='''
		Positive values will make the slide to go down while scrolling, the opposite for negative values. Let it on zero if
		you don't want parallax effect.
	''')
	background_position_y = models.IntegerField(default=0, help_text='''
		Positive values will make the background to go up, the opposite for negative values. This feature won't work for slide with multiple photos
	''')

	@property
	def style(self):
		attrs = {}

		if self.photos.count() == 1:	
			attrs['position'] = 'absolute'
			attrs['top'] = 0
			attrs['left'] = 0
			attrs['right'] = 0
			attrs['background-image'] = 'url(\'{}\')'.format(self.photos.first().url)
			attrs['background-size'] = 'cover'
			# attrs['background-position'] = 'center'
			attrs['background-repeat'] = 'no-repeat'
			attrs['height'] = '100%'
			if self.background_position_y != 0:
				attrs['background-position-y'] = '{}px'.format(self.background_position_y)
			if self.fixed:
				attrs['background-attachment'] = 'fixed'
			return ';'.join(['{}: {}'.format(sk, sv) for sk, sv in attrs.items()])+';'

	def __str__(self):
		return '[{}]'.format('; '.join([str(p) for p in self.photos.all()]))

class SeparatorSVG(models.Model):
	svg_file = models.FileField(upload_to='unsplash_django/svg_separators')

	def __str__(self):
		return os.path.basename(self.svg_file.name)

class Separator(models.Model):
	name = models.CharField(max_length=30)
	svg_file = models.ForeignKey(SeparatorSVG, on_delete=models.CASCADE)
	css = models.TextField(blank=True, null=True)

	def __str__(self):
		return self.name

class Slideshow(models.Model):

	ANIMATIONS = [
		['slide', 'Slide'],
		['fade', 'Fade'],
		['scale', 'Scale'],
		['pull', 'Pull'],
		['push', 'Push'],
	]

	name = models.CharField(max_length=30, blank=False, null=False, unique=True)
	slides = models.ManyToManyField(Slide, through='SlideshowSlide')
	id_attr = models.CharField(max_length=30, blank=False, null=True)
	animation = models.CharField(max_length=30, blank=False, null=False, choices=ANIMATIONS, default='slide')
	autoplay = models.BooleanField(blank=False, null=False, default=False)
	autoplay_interval = models.PositiveIntegerField(blank=True, null=True, validators=(MinValueValidator(1000), ), help_text='Interval in milliseconds between switching slides')
	finite = models.BooleanField(blank=False, null=False, default=False)
	min_height = models.IntegerField(blank=False, null=False, default=0)
	max_height = models.IntegerField(blank=False, null=False)
	full_height = models.BooleanField(default=False, help_text='''
		By enabling this feature, "min_height" and "max_height" will be ignored
	''')
	top_separator = models.ForeignKey(Separator, blank=True, null=True, on_delete=models.CASCADE, related_name='top_separator')
	bot_separator = models.ForeignKey(Separator, blank=True, null=True, on_delete=models.CASCADE, related_name='bot_separator')

	@property
	def style(self):
		attrs = dict()

		if self.animation:
			attrs['animation'] = self.animation
		if self.autoplay:
			attrs['autoplay'] = 'true'
		if self.finite:
			attrs['finite'] = 'true'
		if not self.full_height:
			if self.min_height:
				attrs['min-height'] = self.min_height
			if self.max_height:
				attrs['max-height'] = self.max_height
		else:
			attrs['height'] = '100vh'
		if self.autoplay_interval:
			attrs['autoplay-interval'] = self.autoplay_interval

		return ';'.join(['{}: {}'.format(sk, sv) for sk, sv in attrs.items()])+';'

	def __str__(self):
		return self.name
	
class SlideshowSlide(models.Model):
	slide = models.ForeignKey(Slide, on_delete=models.CASCADE)
	slideshow = models.ForeignKey(Slideshow, on_delete=models.CASCADE)
	order = models.IntegerField()

	class Meta:
		ordering = ('order', )

	def __str__(self):
		return str(self.slide)