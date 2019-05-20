import requests
from bs4 import BeautifulSoup
import datetime

'''
Parse in a site's NWISWeb measurement table using requests and BeautifulSoup. 
'''

station = '09261700'

mmts_url = f'https://waterdata.usgs.gov/ut/nwis/measurements/?site_no={station}&agency_cd=USGS'
mmts_page = requests.get(mmts_url)
mmts_soup = BeautifulSoup(mmts_page.text, 'html.parser')

'''
Save a recent_mmts dict with {number: [date string, datetime object, value]} pairs for measurements within 120 days of current date.
'''

recent_mmts = {}
mmts = mmts_soup.find_all("tr", align="right")

for mmt in mmts:
  mmt_num = mmt.find_all("td")[0].get_text()
  mmt_datetime = mmt.find_all("td")[1].get_text()
  mmt_d = mmt_datetime[0:10] #Can replace indexing with a regex method to ensure dates and times get detected correctly.
  mmt_d_dt = datetime.datetime.strptime(mmt_d, '%Y-%m-%d')
  d = datetime.datetime.now() - datetime.timedelta(days=120)
  if mmt_d_dt > d:
    try:
      mmt_datetime_dt = datetime.datetime.strptime(mmt_datetime, '%Y-%m-%d %H:%M:%S')
    except:
      mmt_datetime_dt = datetime.datetime.strptime(mmt_datetime, '%Y-%m-%d %H:%M')
    q = mmt.find_all("td")[6].get_text()
    recent_mmts.update({mmt_num: [mmt_d, mmt_datetime_dt, q]})
    
'''
For each recent measurement, parse in NWISWeb iv table for date of mmt using requests and BeautifulSoup. 
Save an iv_items dict with time:q pairs.
Determine iv closest to time of mmt and save to var nearest_time. 
Determine computed q value for closest iv. Calculate percent difference from mmt value and issue a warning if plots out of range. 
'''

messages = []

for mmt in recent_mmts.keys():
  mmt_date = recent_mmts[mmt][0]
  iv_url = f'https://waterdata.usgs.gov/ut/nwis/uv?cb_00010=on&cb_00060=on&cb_00065=on&format=html&site_no={station}&period=&begin_date={mmt_date}&end_date={mmt_date}'
  iv_page = requests.get(iv_url)
  iv_soup = BeautifulSoup(iv_page.text, 'html.parser')

  iv_items = {}
  iv_head = iv_soup.find_all("thead")[1]
  iv_heads = iv_head.find_all("th")
  for idx, header in enumerate(iv_heads):
    if "ft3/s" in header.get_text():
      q_idx = idx
      break
  iv_table = iv_soup.find_all("tbody")[1]
  iv_rows = iv_table.find_all("tr", align="center")
  for row in iv_rows:
    iv_date_time = row.find_all("td")[0].get_text()
    iv_date_time_fmt = iv_date_time[1:17]
    iv_date_time_dt = datetime.datetime.strptime(iv_date_time_fmt, '%m/%d/%Y %H:%M')
    iv_q = row.find_all("td")[q_idx]
    iv_q_val = iv_q.find_all("span")[0].get_text()
    if iv_q_val != '\xa0':
      iv_items.update({iv_date_time_dt: iv_q_val})


  mmt_date_time_dt = recent_mmts[mmt][1]
  nearest_time = min(iv_items, key=lambda x: abs(x - mmt_date_time_dt))


  nearest_iv_q = iv_items[nearest_time]
  print(nearest_iv_q)
  q = recent_mmts[mmt][2]
  print(q)
  try:
    diff = int(nearest_iv_q.replace(',', '')) - int(q)
  except:
    diff = float(nearest_iv_q) - float(q)
  try:
    lesser_q = min(int(nearest_iv_q.replace(',', '')), int(q))
  except:
    lesser_q = min(float(nearest_iv_q), float(q))

  if diff/lesser_q > 0.05*lesser_q:
    messages.append(f"Shift not applied for measurement {mmt} made on {mmt_date}.")
  else:
    messages.append(f'Measurement {mmt} made on {mmt_date} plots within error of shifted rating.')

print(f'\nFor Station {station}:\n')
for message in messages:
  print(f"{message}\n")