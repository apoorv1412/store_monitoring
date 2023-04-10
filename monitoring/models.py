from django.db import models

class StoreStatusDB(models.Model):
	class StoreStatus(models.TextChoices):
		ACTIVE = 'active'
		INACTIVE = 'inactive'
	store_id = models.CharField(
		max_length=25
	)
	status = models.CharField(
		choices=StoreStatus.choices,
		default=StoreStatus.ACTIVE,
		max_length=8
	)
	timestamp_utc = models.DateTimeField(
		max_length=6
	)

class StoreTimezoneMapping(models.Model):
	store_id = models.CharField(
		max_length=25,
		primary_key=True
	)
	timezone_str = models.CharField(
		max_length=50
	)

class StoreBusinessHours(models.Model):
	store_id = models.CharField(
		max_length=25,
	)
	day = models.IntegerField()
	start_time_local = models.TimeField()
	end_time_local = models.TimeField()

class MonitoringReport(models.Model):
	class ReportStatus(models.TextChoices):
		RUNNING = 'running'
		FAILED = 'failed'
		COMPLETED = 'completed'

	status = models.CharField(
		choices=ReportStatus.choices,
		default=ReportStatus.RUNNING,
		max_length=9
	) 



	