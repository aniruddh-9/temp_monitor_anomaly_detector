import conf,json,requests,math,statistics
import time
from boltiot import Bolt

PARAMS={'status': "undefined"}

def trigger_integromat_webhook(state):
	PARAMS['status']=state
	URL = conf.INTEGROMAT_URL
	response = requests.get(URL, PARAMS)
	print (response.text)

def compute_bounds(history_data,frame_size,factor) :
	if(len(history_data)<frame_size) :
		return None
	if(len(history_data)>frame_size) :
		del history_data[0:len(history_data)-frame_size]
	Mn=statistics.mean(history_data)
	Variance=0
	for data in history_data :
		Variance += math.pow((data-Mn),2)
	Zn = factor * math.sqrt(Variance / frame_size)
	High_bound = history_data[frame_size-1]+Zn
	Low_bound = history_data[frame_size-1]-Zn
	return [High_bound,Low_bound]

mybolt = Bolt(conf.API_KEY,conf.DEVICE_ID)
history_data=[]
# these thresholds are set using the data collected from 2 Hours
max_threshold = 5
min_threshold = 0

while True:
	response = mybolt.analogRead('A0')
	data = json.loads(response)
	if data['success'] != 1:
		print("There was an error whilst retrieving the data")
		print("This is the temperature" + data['value'])
		time.sleep(10)
		continue
	try:
		sensor_value = int(data['value'])
		sensor_value = sensor_value/10.24
		print("The Temperature is ",round(sensor_value,2),"degree Celsius")
	except e:
		print("There was an error while parsing the response: ",e)
		continue

	if sensor_value > max_threshold:
		# temperature is beyond required maximum
		trigger_integromat_webhook("MAX")
	elif sensor_value < min_threshold:
		# temperature is below required minimum
		trigger_integromat_webhook("MIN")

	bound = compute_bounds(history_data,conf.FRAME_SIZE,conf.MUL_FACTOR)
	if not bound:
		required_data_count = conf.FRAME_SIZE-len(history_data)
		print("Not enough data to compute Z-Score. Need ",required_data_count, "more data points")
		history_data.append(int(data['value']))
		time.sleep(10)
		continue
	try:
		# If temperature rises abnormally --> DOOR IS OPEN
		if sensor_value > bound[0]:
			trigger_integromat_webhook("OPEN")
		history_data.append(sensor_value)
	except Exception as e:
		print("Error",e)
	time.sleep(5)

