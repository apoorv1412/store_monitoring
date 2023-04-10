from .models import StoreStatusDB, StoreTimezoneMapping, StoreBusinessHours, MonitoringReport
from dateutil import tz
import datetime, bisect, csv

import os
from django.conf import settings

REPORT_PATH = os.path.join(settings.BASE_DIR, 'reports/')

class Status:
	def __init__(self, timestamp, status):
		self.timestamp = timestamp
		self.status = status

	def __lt__(self, other):
		return self.timestamp < other.timestamp
	
	def __str__(self):
		return 'Timestamp: ' + str(self.timestamp) +  '\nStatus: ' + self.status + '\n'

class Report_Entry:
	def __init__(self, store_id=None, uptime_last_hour=None, uptime_last_day=None, uptime_last_week=None, downtime_last_hour=None, downtime_last_day=None, downtime_last_week=None):
		self.store_id = store_id
		self.uptime_last_hour = uptime_last_hour
		self.uptime_last_day = uptime_last_day
		self.uptime_last_week = uptime_last_week
		self.downtime_last_hour = downtime_last_hour
		self.downtime_last_day = downtime_last_day
		self.downtime_last_week = downtime_last_week

def write_to_csv(restaurant_stats, report_id):
	# filepath = REPORT_PATH + str(report_id) + '.csv'
	filepath = os.path.join(REPORT_PATH, str(report_id) + '.csv')
	with open(filepath, 'w', newline='') as csvfile:
		writer = csv.writer(csvfile)
		writer.writerow([
			'Store ID', 
			'Uptime Last Hour', 
			'Uptime Last Day', 
			'Uptime Last Week', 
			'Downtime Last Hour', 
			'Downtime Last Day', 
			'Downtime Last Week'
		])
		for stat in restaurant_stats:
			writer.writerow([
				stat.store_id,
				stat.uptime_last_hour,
				stat.uptime_last_day,
				stat.uptime_last_week,
				stat.downtime_last_hour,
				stat.downtime_last_day,
				stat.downtime_last_week,
			])

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

def get_stats_in_minutes(start_time, end_time, store_status, business_hours, time_zone):
	ptr1 = bisect.bisect_left(store_status, Status(start_time, 'active'))
	if ptr1 < len(store_status) and store_status[store_status[ptr1].timestamp < start_time]:
		ptr1 += 1
	if ptr1 >= len(store_status):
		return 0,0
	ptr2 = bisect.bisect_right(store_status, Status(end_time, 'active'))
	
	uptime, downtime = 0, 0
	
	if ptr1 >= ptr2:
		time_diff = int((store_status[ptr1].timestamp - store_status[ptr1-1].timestamp).total_seconds()/60)
		if ptr1 > 0:
			if store_status[ptr1-1].status == 'inactive':
				downtime += time_diff
			else:
				uptime += time_diff
		elif ptr1+1 < len(store_status):
			if store_status[ptr1+1].status == 'inactive':
				downtime += time_diff
			else:
				uptime += time_diff
	else:
		day_of_week = store_status[ptr1].timestamp.weekday()
		current_date = store_status[ptr1].timestamp.date()
		store_start_time = datetime.datetime.combine(current_date, datetime.time(0, 0, 0,  tzinfo=tz.gettz(time_zone)))
		store_end_time = datetime.datetime.combine(current_date, datetime.time(23, 59, 59,  tzinfo=tz.gettz(time_zone)))
		while ptr1 < ptr2:
			day_of_week = store_status[ptr1].timestamp.weekday()
			current_date = store_status[ptr1].timestamp.date()
			store_start_time = datetime.datetime.combine(current_date, datetime.time(0, 0, 0,  tzinfo=tz.gettz(time_zone)))
			store_end_time = datetime.datetime.combine(current_date, datetime.time(23, 59, 59,  tzinfo=tz.gettz(time_zone)))
			if day_of_week in business_hours:
				store_start_time = datetime.datetime.combine(current_date, business_hours[day_of_week].start_time_local, tz.gettz(time_zone))
				store_end_time = datetime.datetime.combine(current_date, business_hours[day_of_week].end_time_local, tz.gettz(time_zone))
				# store_start_time = pytz.timezone(time_zone).localize(store_start_time)
				# store_end_time = pytz.timezone(time_zone).localize(store_end_time)
				

			while ptr1 < ptr2 and store_status[ptr1].timestamp.date() == current_date:
				if ptr1 > 0:
					time_diff = int((store_status[ptr1].timestamp - store_status[ptr1-1].timestamp).total_seconds()/60)
					if store_status[ptr1-1].status == 'inactive':
						downtime += time_diff
					else:
						uptime += time_diff
				else:
					prev_time = store_start_time
					time_diff = int((store_status[ptr1].timestamp - prev_time).total_seconds()/60)
					if store_status[ptr1].status == 'inactive':
						downtime += time_diff
					else:
						uptime += time_diff
				ptr1 += 1
		curr_time = store_end_time
		time_diff = int((curr_time - store_status[ptr1-1].timestamp).total_seconds()/60)
		if store_status[ptr1-1].status == 'inactive':
			downtime += time_diff
		else:
			uptime += time_diff

	return uptime, downtime 

def generate_report(date, store_status_mapping, store_business_hours, store_timezone_mapping, report_id):
	restaurant_stats = []

	from_zone = tz.gettz('UTC')
	for store_status_ID in store_status_mapping:
		business_hours = {}
		if store_status_ID in store_business_hours:
			for a in store_business_hours[store_status_ID]:
				business_hours[a.day] = a
		store_status = store_status_mapping[store_status_ID]

		report_entry = Report_Entry(store_id=store_status_ID)
		
		end_time = date
		timezone = 'America/Chicago'
		if store_status_ID in store_timezone_mapping:
			timezone = store_timezone_mapping[store_status_ID]
		to_zone = tz.gettz(timezone)
		end_time = end_time.replace(tzinfo=from_zone).astimezone(to_zone)
		
		start_time = date - datetime.timedelta(days=7)
		uptime, downtime = get_stats_in_minutes(start_time, end_time, store_status, business_hours, timezone)
		report_entry.uptime_last_week = uptime/60
		report_entry.downtime_last_week = downtime/60

		start_time = date - datetime.timedelta(days=1)
		uptime, downtime = get_stats_in_minutes(start_time, end_time, store_status, business_hours, timezone)
		report_entry.uptime_last_day = uptime/60
		report_entry.downtime_last_day = downtime/60

		start_time = date - datetime.timedelta(hours=1)
		uptime, downtime = get_stats_in_minutes(start_time, end_time, store_status, business_hours, timezone)
		report_entry.uptime_last_hour = uptime
		report_entry.downtime_last_hour = downtime

		restaurant_stats.append(report_entry)

	write_to_csv(restaurant_stats, report_id)

	report = MonitoringReport.objects.get(pk=report_id)
	report.status = MonitoringReport.ReportStatus.COMPLETED
	report.save()

def create_report_status_entry():
	report = MonitoringReport(status=MonitoringReport.ReportStatus.RUNNING)
	report.save()
	return report.id

def is_report_gen_finished(report_id):
	report = MonitoringReport.objects.get(pk=report_id)
	return report.status == MonitoringReport.ReportStatus.COMPLETED

def func(report_id):
	report = MonitoringReport.objects.get(pk=report_id)
	report.status = MonitoringReport.ReportStatus.COMPLETED
	report.save()