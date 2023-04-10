from celery import shared_task
from .utils import get_store_timezone_mapping, get_store_status_mapping, get_store_id_to_business_hours_mapping, get_date, generate_report
from .strategies import EndpointStrategy

@shared_task
def generate_report_task(report_id):
	store_timezone_mapping = get_store_timezone_mapping()
	store_status_mapping = get_store_status_mapping(store_timezone_mapping)
	store_id_to_business_hours_mapping = get_store_id_to_business_hours_mapping()
	date = get_date()
	generate_report(date, store_status_mapping, store_id_to_business_hours_mapping, store_timezone_mapping, report_id, EndpointStrategy())