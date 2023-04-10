from .models import StoreStatusDB, StoreTimezoneMapping, StoreBusinessHours, MonitoringReport
from dateutil import tz
import datetime 

class Status:
	def __init__(self, timestamp, status):
		self.timestamp = timestamp
		self.status = status

	def __lt__(self, other):
		return self.timestamp < other.timestamp
	
	def __str__(self):
		return 'Timestamp: ' + str(self.timestamp) +  '\nStatus: ' + self.status + '\n'
	
def get_date():
	return datetime.datetime(2023, 1, 24, 12, 23, 0, tzinfo=tz.UTC)

def get_store_timezone_mapping():
	store_timezone_mapping_objects = StoreTimezoneMapping.objects.all()
	store_timezone_mapping = {}
	for store_timezone_mapping_object in store_timezone_mapping_objects: 
		store_timezone_mapping[store_timezone_mapping_object.store_id] = store_timezone_mapping_object.timezone_str
	return store_timezone_mapping

def get_store_status_mapping(store_timezone_mapping):
	store_status = StoreStatusDB.objects.all()
	store_status_mapping = {}
	from_zone = tz.gettz('UTC')
	for status in store_status: 
		if status.store_id not in store_status_mapping: 
			store_status_mapping[status.store_id] = []
		timezone = 'America/Chicago'
		if status.store_id in store_timezone_mapping:
			timezone = store_timezone_mapping[status.store_id]
		to_zone = tz.gettz(timezone)
		local_time = status.timestamp_utc.replace(tzinfo=from_zone).astimezone(to_zone)
		store_status_mapping[status.store_id].append(Status(local_time, status.status))
		store_status_mapping[status.store_id].append(Status(status.timestamp_utc, status.status))
	for store in store_status_mapping:
		store_status_mapping[store].sort(key=lambda x : x.timestamp)
	return store_status_mapping

def get_store_id_to_business_hours_mapping():
	store_business_hours = StoreBusinessHours.objects.all()
	store_id_to_business_hours_mapping = {}
	for business_hours in store_business_hours:
		if business_hours.store_id not in store_id_to_business_hours_mapping:
			store_id_to_business_hours_mapping[business_hours.store_id] = []
		store_id_to_business_hours_mapping[business_hours.store_id].append(business_hours) 
	return store_id_to_business_hours_mapping
