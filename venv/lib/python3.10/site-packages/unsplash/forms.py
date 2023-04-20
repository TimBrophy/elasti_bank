from django import forms
from . import models

class SlideForm(forms.ModelForm):

	class Meta:
		model = models.Slide
		fields = '__all__'

	def clean(self,):
		if self.cleaned_data.get('photos').count() > 4:
			raise forms.ValidationError({
				'photos': 'You can\'t select more than four photos'
			})

		return self.cleaned_data
