import requests
import json
import datetime
import dateutil.parser


'''
Define variables for url parsing.
'''

stations_list = ['373830109283201', '375050109034801', '390925111455301', '393928113522601', '402312109545701', '414236112101201'] # List from https://groundwaterwatch.usgs.gov/NetMapT1L2.asp?sc=49&ncd=rtn

end_date = datetime.date.today()
end_date_iso = end_date.isoformat()
end_time = datetime.datetime.now().time().strftime('%H:%M')
start_date = datetime.date.today() - datetime.timedelta(days=120)
start_date_iso = start_date.isoformat()

print('----------------------------------------')
print(f'Results on {end_date_iso} at {end_time}:\n\n')

'''
Create log file.
'''

f = open("GW_TS_C_JSON_Utah_logs.txt", "a")
f.write('\n----------------------------------------')
f.write(f'\nResults on {end_date_iso} at {end_time}:\n\n')

'''
Define counter variables for table outputs. 
'''

flags = 0
observations = 0
sites = len(stations_list)
sites_obs = 0
days_since_last = []
diffs = []

for station in stations_list:

  '''
  Parse in a dict of groundwater site's measurements for the last 120 days using requests and json libraries and convert to list. Each recent mmt is one dictionary in list: [{'value': <str>, 'qualifiers': [], 'dateTime': <str>},]
  '''

  messages = []
  wls = requests.get(f'https://waterservices.usgs.gov/nwis/gwlevels/?format=json&sites={station}&startDT={start_date_iso}&endDT={end_date_iso}&siteStatus=all')
  wls_dict = json.loads(wls.text)
  #wls_str = json.dumps(wls_dict, indent=4)  # For debug purposes.

  values_list = wls_dict['value']['timeSeries']
  wl_obs = True
  for value in values_list:
    if value['values'][0]['value']:
      wls_list = value['values'][0]['value']
      wl_obs = True
    else:
      wl_obs = False
  if wl_obs == True:
    sites_obs += 1
  last_wl_dt_iso = wls_list[-1]['dateTime']
  last_wl_datetime_obj = dateutil.parser.parse(last_wl_dt_iso)
  last_wl_date_obj = last_wl_datetime_obj.date()
  days_since_last.append(int((datetime.datetime.now().date() - last_wl_date_obj)/ datetime.timedelta(days=1)))

  '''
  For each recent measurement, parse dict of iv's for date of mmt using requests and json libraries and convert to list. Each iv is one dictionary in list: [{'value': <str>, 'qualifiers': [], 'dateTime': <str>},]
  Determine closest iv times before and after time of mmt and save to dict nearest. 
  Determine time series wl value for closest iv time. Calculate difference from mmt value and issue a warning if plots out of range. 
  '''

  for i, mmt in enumerate(wls_list):

    mmt_datetime_iso = mmt['dateTime']  # Type string
    mmt_datetime_obj = dateutil.parser.parse(mmt_datetime_iso)  # Type datetime obj
    mmt_date_iso = mmt_datetime_iso[:10]  # Type string
    mmt_wl = mmt['value']
    iv_url = f'https://nwis.waterservices.usgs.gov/nwis/iv/?format=json&sites={station}&startDT={mmt_date_iso}&endDT={mmt_date_iso}&siteStatus=all'
    iv_page = requests.get(iv_url)
    iv_dict = json.loads(iv_page.text)
    #iv_str = json.dumps(iv_dict, indent=4)  # For debug purposes.

    iv_list = iv_dict['value']['timeSeries'][0]['values'][0]['value']

    if iv_list:
      nearest = {}  #{'before': [datetime_iso, datetime_obj, wl], 'after': [datetime_iso, datetime_obj, wl]}

      for i, iv in enumerate(iv_list):
        iv_datetime_obj = dateutil.parser.parse(iv['dateTime'])
        iv_datetime_obj_naive = iv_datetime_obj.replace(tzinfo=None)
        if iv_datetime_obj_naive > mmt_datetime_obj:
          nearest.update({'after': [iv_datetime_obj_naive, iv['dateTime'], iv['value']]})
          nearest.update({'before': [dateutil.parser.parse(iv_list[i-1]['dateTime']).replace(tzinfo=None), iv_list[i-1]['dateTime'], iv_list[i-1]['value']]})
          break

      diff = abs(float(mmt_wl) - float(nearest['after'][2]))
      diffs.append(diff)
      if diff > 0.02:
        messages.append(f"Time series not corrected for discrete water level measured on {mmt_date_iso}.")
        flags += 1
      else:
        messages.append(f"Water level measured on {mmt_date_iso} plots within error of corrected time series.")
        observations += 1
    else:
      messages.append(f'A measurement was made on {mmt_date_iso} but no time series data exists for this date.')
      observations += 1



  print(f'\nFor Station {station}:\n')
  for message in messages:
    print(f"{message}\n")

  '''
  Write results to a file.
  '''

  #f.write(f'\nFor Station {station}:\n')
  #for message in messages:
    #f.write(f'{message}\n')

percent_flagged = round(flags/observations, 1)
mean_obs = round(observations/sites, 1)
mean_days_since_last = int(sum(days_since_last)/len(days_since_last))
max_days_since_last = max(days_since_last)
max_diff = round(max(diffs), 2)
abs_diffs = []
for diff in diffs:
  abs_diffs.append(abs(diff))
mean_diff = round(sum(abs_diffs)/len(diffs), 3)
print(f'Total water level observations flagged with issues: {flags}')
print(f'Total water level observations made: {observations}')
print(f'Percent water level observations flagged with issues: {percent_flagged}')
print(f'Total stations with water level observations made: {sites_obs}')
print(f'Total number of real-time water level stations: {sites}')
print(f'Mean water level observations per real-time station: {mean_obs}')
print(f'Mean number of days since last observation at real-time stations: {mean_days_since_last}')
print(f'Max number of days since last observation at real-time stations: {max_days_since_last}')
print(f'Max time series difference from observed water level: {max_diff}')
print(f'Mean time series difference from observed water level: {mean_diff}')

f.write(f'''\n\nFor sites in the state of Utah:
Total water level observations flagged with issues: {flags}
Total water level observations made: {observations}
Percent water level observations flagged with issues: {percent_flagged}
Total stations with water level observations made: {sites_obs}
Total number of real-time water level stations: {sites}
Mean water level observations per real-time station: {mean_obs}
Mean number of days since last observation at real-time stations: {mean_days_since_last}
Max number of days since last observation at real-time stations: {max_days_since_last}
Max time series difference from observed water level: {max_diff}
Mean time series difference from observed water level: {mean_diff}''')
f.close()