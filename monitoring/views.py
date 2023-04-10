from django.shortcuts import render
from .utils import get_store_timezone_mapping, get_store_status_mapping, get_store_id_to_business_hours_mapping, get_date, generate_report, create_report_status_entry, is_report_gen_finished, func, REPORT_PATH
from django.http import HttpResponse, HttpResponseNotFound, FileResponse
import os

def trigger_report_generation(request):
	report_id = create_report_status_entry()
	store_timezone_mapping = get_store_timezone_mapping()
	store_status_mapping = get_store_status_mapping(store_timezone_mapping)
	store_id_to_business_hours_mapping = get_store_id_to_business_hours_mapping()
	date = get_date()
	generate_report(date, store_status_mapping, store_id_to_business_hours_mapping, store_timezone_mapping, report_id)
	return HttpResponse(report_id)

def get_report(request, id):
	if not is_report_gen_finished(id):
		return HttpResponse('Running')
	
	filepath = os.path.join(REPORT_PATH, str(id) + '.csv')
	if not os.path.exists(filepath):
		return HttpResponseNotFound('The requested file does not exist.')

	response = HttpResponse('Completed', content_type='text/plain')
	with open(filepath) as file:
		response['Content-Disposition'] = f'attachment; filename="{os.path.basename(filepath)}"'
		
	return response


	
	