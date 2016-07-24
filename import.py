import csv, json
from datetime import datetime, timedelta
from pytz import utc

google_doc_events = {}
bm_events = {}
bm_camps = {}
bm_art = {}

with open('googlesheet.csv') as csvfile:
    reader = csv.DictReader(csvfile)
    for row in reader:
        proper_format = {}
        proper_format["event_source"] = "google_sheet"
        proper_format["title"] = row["title"]
        proper_format["desc"] = row["desc"]
        proper_format["event_type"] = {"id": "8732", "label": "Fun", "abbr": "fun"}
        #proper_format["all_day"] = int(row["anytime"])
        proper_format["occurrence_set"] = []
        if len(row['startDate']) > 1 and len(row['endDate']) > 1:
            start_date = utc.localize(datetime.strptime(row['startDate'],"%Y-%m-%d")) # times are NOT in UTC.
            end_date = utc.localize(datetime.strptime(row['endDate'],"%Y-%m-%d"))     # but BMapi falsely returns UTC so we make these UTC for consistency
            day = start_date
            if len(row['startTime']) > 1 and len(row['endTime']) > 1:
                start_time = datetime.strptime(row['startTime'], "%H:%M")
                end_time = datetime.strptime(row['endTime'], "%H:%M") 
                while day <= end_date:
                    start = day + timedelta(hours=start_time.hour, minutes=start_time.minute)
                    end = day + timedelta(hours=end_time.hour, minutes=end_time.minute)
                    proper_format['occurrence_set'].append({"start_time": start.isoformat(), "end_time": end.isoformat()})
                    day = day + timedelta(days=1)
            elif len(row['anytime']) and int(row['anytime']) == 1:
                while day <= end_date:
                    start = day
                    end = day + timedelta(hours=23, minutes=59)
                    proper_format['occurrence_set'].append({"start_time": start.isoformat(), "end_time": end.isoformat()})
                    day = day + timedelta(days=1)
                
        google_doc_events[row.pop("id")] = proper_format

with open('BM_Art_2016.json') as json_file:
    array = json.loads(json_file.read())
    for entry in array:
        uid = entry.pop('uid')
        bm_art[uid] = entry

with open('BM_Camps_2016.json') as json_file:
    array = json.loads(json_file.read())
    for entry in array:
        uid = entry.pop('uid')
        bm_camps[uid] = entry
        
with open('BM_Events_2016.json') as json_file:
    array = json.loads(json_file.read())
    for entry in array:
        entry['event_source'] = 'bmapi'
        entry['desc'] = entry.pop('description')
        uid = entry.pop('uid')
        camp = entry['hosted_by_camp']
        if camp:
            entry['location'] = bm_camps[camp]['name']
        art = entry['located_at_art']
        if art:
            entry['location'] = bm_art[art]['name']
        if art and camp:
            print("uh oh: %s[%s] has both art and camp" % (entry['title'], entry['uid']))
        bm_events[uid] = entry

all_events = {}
all_events.update(google_doc_events)
all_events.update(bm_events)

with open("./all_events.json", "w") as json_file:
    json_file.write(json.dumps(all_events, sort_keys=True, indent=4))

def active(event, time=None):
    if not time:
        time = datetime.now()
    for occurrence in event['occurrence_set']:
        start = datetime.strptime(occurrence['start_time'][:-6], "%Y-%m-%dT%H:%M:%S") 
        end = datetime.strptime(occurrence['end_time'][:-6], "%Y-%m-%dT%H:%M:%S") 
        if (time > start) and (time < end): return True
    return False