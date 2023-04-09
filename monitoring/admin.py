from django.contrib import admin
from monitoring.models import StoreStatusDB, StoreTimezoneMapping, StoreBusinessHours

# Register your models here.
admin.site.register(StoreStatusDB)
admin.site.register(StoreTimezoneMapping)
admin.site.register(StoreBusinessHours)
