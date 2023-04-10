from django.shortcuts import render
from .utils import create_report_status_entry, is_report_gen_finished, REPORT_PATH
from django.http import HttpResponse, HttpResponseNotFound
import os
from .tasks import generate_report_task
from django import forms

class ReportForm(forms.Form):
	id = forms.IntegerField()

	def __init__(self, *args, **kwargs):
		super().__init__(*args, **kwargs)
		self.fields['id'].widget.attrs.update({'type': 'number', 'min': 1})

def trigger_report_generation(request):
	report_id = create_report_status_entry()
	generate_report_task.delay(report_id)
	return HttpResponse(report_id)

def get_report(request):
	if request.method == 'POST':
		form = ReportForm(request.POST)
		if form.is_valid():
			id = form.cleaned_data['id']
			if not is_report_gen_finished(id):
				return HttpResponse('Running')
			filepath = os.path.join(REPORT_PATH, str(id) + '.csv')
			if not os.path.exists(filepath):
				return HttpResponseNotFound('The requested file does not exist.')
			with open(filepath) as file:
				response = HttpResponse(file, content_type='text/csv')
				response['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
				return response
	else:
		form = ReportForm()
	
	return render(request, 'get_report.html', {'form': form})