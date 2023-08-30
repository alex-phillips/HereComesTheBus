#!/usr/bin/env python3
import re
import os
import json
import requests
import mechanicalsoup
import argparse

parser = argparse.ArgumentParser(description="Fetch current location of the bus")
parser.add_argument(
    "-u", "--username", help="Username",
)
parser.add_argument(
    "-p", "--password", help="Password",
)
parser.add_argument(
    "-c", "--code", help="School code",
)
parser.add_argument(
    "-e", "--endpoint", help='Endpoint to send coordinates to (POST, payload: {"loc": [lat, lon]})',
)
args = parser.parse_args()

session = mechanicalsoup.StatefulBrowser()
# session.session.headers.update(headers)
browser = None

cookies = {}
# cookies_file = f"{os.getenv('HOME')}/.hctb.cookies"
# if os.path.isfile(cookies_file):
#     with open(cookies_file, 'r') as fh:
#         cookies = json.loads(fh.read())

if len(cookies.keys()) > 0:
    print("Using existing cookies")
    requests.utils.add_dict_to_cookiejar(session.session.cookies, cookies)

    url = 'https://login.herecomesthebus.com/Map.aspx'
    session.open(url)
else:
    url = 'https://login.herecomesthebus.com/Authenticate.aspx'
    session.open(url)

    form = session.select_form(selector='#aspnetForm')
    form['ctl00$ctl00$cphWrapper$cphContent$tbxUserName'] = args.username
    form['ctl00$ctl00$cphWrapper$cphContent$tbxPassword'] = args.password
    form['ctl00$ctl00$cphWrapper$cphContent$tbxAccountNumber'] = args.code

    response = session.submit_selected()

with open(cookies_file, 'w') as fh:
    fh.write(json.dumps(session.session.cookies.get_dict()))

passenger_id = session.page.find('div', id='pickPassenger').find('option')['value']
passenger_name = session.page.find('div', id='pickPassenger').find('option').text
time_of_day = session.page.find('div', id='pickTimeOfDay').find('option', selected="selected")['value']

map_resp = session.post("https://login.herecomesthebus.com/Map.aspx/RefreshMap", json={
    "legacyID": f"{passenger_id}",
    "name": f"{passenger_name}",
    "timeSpanId": f"{time_of_day}",
    "wait": "false",
}).json()

try:
    coords = re.search(r"SetBusPushPin\((\d+\.\d+),(-\d+\.\d+)", map_resp["d"])
    print(f"{coords.group(1)}, {coords.group(2)}")
    if args.endpoint:
        requests.post(args.endpoint, json={"loc": [coords.group(1), coords.group(2)]})
except Exception as e:
    print(e)
    print("ERROR: Bus may not be running?")
