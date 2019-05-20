import requests
from bs4 import BeautifulSoup
import datetime

'''
Parse in a groundwater site's NWISWeb measurement table using requests and BeautifulSoup. 
'''

station = '393928113522601'

mmts_url = f'https://nwis.waterdata.usgs.gov/nwis/gwlevels?site_no={station}&agency_cd=USGS&format=html'
mmts_page = requests.get(mmts_url)
mmts_soup = BeautifulSoup(mmts_page.text, 'html.parser')


'''
Save a recent_mmts dict with {date string: [datetime object, value]} pairs for measurements within 120 days of current date.
'''

recent_mmts = {}
mmts = mmts_soup.find_all("tr", align="right")

for mmt in mmts:
  mmt_d = mmt.find_all("td")[0].get_text()
  mmt_t = mmt.find_all("td")[1].get_text() 
  mmt_d_dt = datetime.datetime.strptime(mmt_d, '%Y-%m-%d')
  d = datetime.datetime.now() - datetime.timedelta(days=120)
  if mmt_d_dt > d:
    wl = mmt.find_all("td")[3].get_text()
    recent_mmts.update({mmt_d: [mmt_t, wl]})
    print(f"A water level depth of {wl} was measured on {mmt_d} at {mmt_t}.")
  

'''
For each recent measurement, parse in NWISWeb iv table for date of mmt using requests and BeautifulSoup. 
Save an iv_items dict with time:wl pairs.
Determine iv closest to time of mmt and save to var nearest_time. 
Determine time series wl value for closest iv. Calculate difference from mmt value and issue a warning if plots out of range. 
'''

messages = []

for mmt_date in recent_mmts.keys():
  iv_url = f'https://waterdata.usgs.gov/nwis/uv?cb_72019=on&format=html&site_no={station}&period=&begin_date={mmt_date}&end_date={mmt_date}'
  iv_page = requests.get(iv_url)
  iv_soup = BeautifulSoup(iv_page.text, 'html.parser')

  iv_items = {}

  iv_table = iv_soup.find_all("tbody")[2]
  iv_rows = iv_table.find_all("tr", align="center")
  for row in iv_rows:
    iv_time = row.find_all("td")[0].get_text()

    iv_time_fmt = iv_time[0:5]
    iv_date_time_fmt = f"{mmt_date} {iv_time_fmt}"
    iv_date_time_dt = datetime.datetime.strptime(iv_date_time_fmt, '%Y-%m-%d %H:%M')
    iv_wl = row.find_all("td")[1]
    iv_wl_val = iv_wl.find_all("span")[0].get_text()
    if iv_wl_val != '\xa0':
      iv_items.update({iv_date_time_dt: iv_wl_val})

  mmt_date_time_fmt = f"{mmt_date} {recent_mmts[mmt_date][0][0:5]}"
  print(mmt_date_time_fmt)
  mmt_date_time_dt = datetime.datetime.strptime(mmt_date_time_fmt, '%Y-%m-%d %H:%M')
  nearest_time = min(iv_items, key=lambda x: abs(x - mmt_date_time_dt))
  print(nearest_time)

  nearest_iv_wl = iv_items[nearest_time]
  print(nearest_iv_wl)

  wl = recent_mmts[mmt_date][1]
  print(wl)

  if abs(float(nearest_iv_wl) - float(wl)) > 0.02:
    messages.append(f"Time series not corrected for discrete water level measured on {mmt_date}.")
  else:
    messages.append(f"Water level measured on {mmt_date} plots within error of corrected time series.")

print(f'\nFor Station {station}:\n')
for message in messages:
  print(f"{message}\n")
