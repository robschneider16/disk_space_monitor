#!/usr/bin/env python

import argparse
import os
import json
import subprocess
import re
from datetime import datetime

MONITOR_DISKS2 = ['/data/oco3-geos5',\
                 '/workspace/jpl',\
                 '/scf-p2',\
                 '/oco3-preflt',\
                 '/oco3-transfer',\
                 '/groups',\
                 '/scratch-science',\
                 '/workspace/pld',\
                 '/ecmwf',\
                 '/ecmwf2',\
                 '/acos/product',\
                 '/acos/ingest',\
                 '/acos/ingest2',\
                 '/oco2-d2',\
                 '/oco2-p2',\
                 '/oco2-p3',\
                 '/oco2-p4',\
                 '/scratch-sdos',\
                 '/oco3-TVACResults0',\
                 '/oco3-TVACResults1',\
                 '/oco3-TVACResults2',\
                 '/oco3-TVACResults3',\
                 '/deploy',\
                 '/TVACResults',\
                 '/scf_archive/oco2',\
                 '/scf-p1',\
                 '/cal-sandbox',\
                 '/transfer',\
                 '/TVACResults3',\
                 '/scf_ops',\
                 '/TVACResults2',\
                 '/oco2-d1',\
                 '/oco2-p1',\
                 '/oco2-p5',\
                 '/oco2-p6',\
                 '/oco2-p7',\
                 '/oco2-p8',\
                 '/oco2',\
                 '/pcs',\
                 '/oco3',\
                 '/oco3-pcs',\
                 '/scf_archive/acos',\
                 '/data/oco2',\
                 '/data/acos',\
                 '/cal-sandbox3',\
                 '/workspace/aws',\
                 '/scf-p3',\
                 '/home/oco2op',\
                 '/backup',\
                 '/scratch-science2',\
                 '/oco3-d1',\
                 '/oco3-p1',\
                 '/oco3-p2']

MONITOR_DISKS = ['/oco2-p5']

MONITOR_THRESHOLD = 10
# What unit (in bytes) to use 
BYTE_UNIT = "G"

HR_DT = "%Y-%m-%dT%H:%M:%SZ"
NUM_DT = "%y%m%d%H%M%S"

def get_curr_disk_usage():
  '''
  Get the current disk usage on the system using the GNU df command
  '''

  df = subprocess.Popen(["df","-PB"+BYTE_UNIT.lower()], stdout=subprocess.PIPE)
  out, err = df.communicate()
  disk_usage = []

  # Get the current time
  now = int(datetime.utcnow().strftime("%y%m%d%H%M%S"))

  # Loop through each line of the output from the df process
  for l in out.split('\n'):

    # Split the line into a list
    du = l.split()
    # Only proceed if the line if the right format and contains a valid disk
    if len(du) == 6 and du[5] in MONITOR_DISKS:
      space_used = int(du[2].strip(BYTE_UNIT.upper()))
      space_left = int(du[3].strip(BYTE_UNIT.upper()))
      disk_name = str(du[5])
      disk_cap = space_used + space_left
      perc_full = int(du[4].strip("%")) 
      new_entry = {"name":disk_name, "capacity":disk_cap, "percentage":perc_full, "increase":0, "usage":[space_used], "dates":[now]}
      disk_usage.append(new_entry)
  #Return the new dictionary of disk usage
  return disk_usage



def update_disk_usage_hist(curr_usage, hist_usage):
  '''
  Add the recent disk usage data to the historical disk usage records file 
  '''
  # Get the current disk usage dictionary, and update it with data from the history file
  # By starting with curr_usage and adding hist info to it, you maintain updates to the system:
  # When a disk that is unmounted, it will be removed from the report
  # Any disk whos capacity is increased will be reflected in the histry 

  # List of dictionarys to store what will be the new updated historical disk usage json file
  new_hist_usage = []
  # Loop through all the disk in the currect report
  for du in curr_usage:
    cap = du['capacity']
    name = du['name']
    usage = du['usage']
    dates = du['dates']
    perc = du['percentage']
    # For each disk, try and find it in the historical data
    for hu in hist_usage:

      # If the hist data has the disk name
      if name == str(hu['name']):

        #Calculate the increase since since last historical usage reading
        usage_increase = usage[0] - hu['usage'][0]

        # Take the hist data and add current report data overwriting dupes if needed
        usage.extend(hu['usage'])
        dates.extend(hu['dates'])

    # Add the updated disk usage to the new historical usage dictionary
    new_hist_usage.append({"name":name, "capacity":cap, "percentage":perc, "increase":usage_increase,"usage":usage, "dates":dates})
  return new_hist_usage



def notify_disk_crit(hist_usage):
  '''
  Looks at the historical disk usage and notifies the user if the disk is almost full
  Will not notify usage has not changed since previous check
  '''
  # Check the percentage and usage increase for each disk, and notify if its bad 
  for du in hist_usage:
    if du['percentage'] >= MONITOR_THRESHOLD and du['increase'] > 0:
      print "Disk {} is close to capacity".format(du['name'])
      print "{} full at time {}".format(du['percentage'], datetime.strptime(str(du['dates'][0]), NUM_DT).strftime(HR_DT))
      print "{}{}B used out of {}{}B".format(du['usage'][0],BYTE_UNIT,du['capacity'],BYTE_UNIT)
      print "{}{}B increase since {}".format(du['increase'], BYTE_UNIT, datetime.strptime(str(du['dates'][1]), NUM_DT).strftime(HR_DT))



if __name__ == '__main__':
  ap = argparse.ArgumentParser(description=__doc__)
  ap.add_argument('--history',
      type=str,
      help='The path to historical disk usage json file'
  )
  ap.add_argument('--update',
      action='store_true',
      help='If specified, New current disk usage data will be added to the historical disk usage json file provided'
  )
  ap.add_argument('--monitor',
      action='store_true',
      help='If the user want to be notified of disks that are close to capacity'
  )
  args = ap.parse_args()
 
  # Get the current usage
  curr_usage = get_curr_disk_usage()

  # If user specifies the history file, read it in
  if args.history:
    with open(args.history) as json_file:
      hist_usage = json.load(json_file)

    # If user says to update the history file, lets update it
    hist_usage_new = update_disk_usage_hist(curr_usage, hist_usage)
    if args.update:
      with open(args.history, 'w') as outfile:
        json.dump(hist_usage_new, outfile)

    # If the user specifies the monitor argument, then notify users if disk space is close to cap
    if args.monitor:
      notify_disk_crit(hist_usage_new)
  else:
    print json.dumps(curr_usage)






