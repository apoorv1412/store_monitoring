'''
This file contains the strategies used for extrapolation. There is the main
ExtrapolationStrategy abstract class which all other strategy classes inherit
from. 
'''

from abc import ABC, abstractmethod
from .utils import Status
import bisect, datetime
from dateutil import tz

class ExtrapolationStrategy(ABC):
	@abstractmethod
	def get_stats_in_minutes(self, start_time, end_time, store_status, business_hours, time_zone):
		pass

'''
This is the strategy that is used. Given two timestamps, the status of the 
restaurant between the two timestamps is governed by the earlier timestamp. 
If the earlier timestamp is not available, the status is judged on the basis
of the later timestamp
'''
class EndpointStrategy(ExtrapolationStrategy):
	def get_stats_in_minutes(self, start_time, end_time, store_status, business_hours, time_zone):
		'''
		The store_status objects are sorted on the basis of timestamps. The first 
		timestamp is in consideration and the last timestamp in consideration is 
		computed here. 
		'''
		ptr1 = bisect.bisect_left(store_status, Status(start_time, 'active'))
		if ptr1 < len(store_status) and store_status[store_status[ptr1].timestamp < start_time]:
			ptr1 += 1
		if ptr1 >= len(store_status):
			return 0,0
		ptr2 = bisect.bisect_right(store_status, Status(end_time, 'active'))
		
		uptime, downtime = 0, 0
		
		if ptr1 >= ptr2:
			'''
			Case 1: No timestamps can be included in the window
			'''
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
			'''
			Case 2: Timestamps are present in the window
			'''
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