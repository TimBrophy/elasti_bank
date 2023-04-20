from django.db import models
from embed_video.fields import EmbedVideoField


class ContentSeries(models.Model):
    name = models.CharField(max_length=150, verbose_name='Series name')
    description = models.CharField(max_length=300, verbose_name='Description')
    image = models.ImageField(blank=True, upload_to='images')

    def __str__(self):
        return self.name

    class Meta:
        verbose_name_plural = "Content series"


class ContentItem(models.Model):
    name = models.CharField(max_length=150, verbose_name='Name')
    description = models.CharField(max_length=300, verbose_name='Description')
    series = models.ManyToManyField(ContentSeries)
    video = EmbedVideoField()
    featured = models.BooleanField(default=0)
    thumbnail = models.ImageField(blank=True)

    def __str__(self):
        return self.name

