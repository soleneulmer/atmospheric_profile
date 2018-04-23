import requests
from bs4 import BeautifulSoup
import shutil
from captcha_solver import CaptchaSolver
import sys

# ---------------------------------------------------------
# TelFit download atmospheric profiles
# ---------------------------------------------------------
# url for latitude = -24.62 and longitude = -70.40
# the User ID need to be modified, get a new one by visiting the website
# https://ready.arl.noaa.gov/READYamet.php

userid = '229'
year = '2017'
month = '08'
day = '03'
hour = '00'

for i, arg in enumerate(sys.argv):
    if i == 1:
        userid = sys.argv[1]
    if i == 2:
        year = sys.argv[2]
    if i == 3:
        month = sys.argv[3]
    if i == 4:
        day = sys.argv[4]
    if i == 5:
        hour = sys.argv[5]

print('\nDownloading atmospheric profile from Air Resources Laboratory database')
print('Userid:', userid,
      '\nRequested profile',
      '\nYear:', year, '\nMonth:', month,
      '\nDay:', day, '\nHour:', hour)


def make_metfile(year=year, month=month, day=day):
    return '%s%s%s_gdas0p5' % (year, month, day)


def make_payload(metfile, userid, lat=-24.62, lon=-70.40):
    payload = dict(
        userid=userid,
        metdata="GDAS0P5",
        metdatasm="gdas0p5",
        mdatacfg="GDAS0P5",
        Lat=lat,
        Lon=lon,
        sid="",
        elev="",
        sname="",
        state="",
        cntry="",
        map="WORLD",
        x="-1",
        y="-1",
        metfile=metfile,
    )
    return payload


def make_payload2(metfile, proc, code, userid, year="2018", month="01", day="24", hour="00", lat=-24.62, lon=-70.40):
    payload2 = dict(
        userid=userid,
        metdata="GDAS0P5",
        mdatacfg="GDAS0P5",
        metdatasm="gdas0p5",
        Lat=lat,
        Lon=lon,
        sid="",
        elev="",
        sname="",
        state="",
        cntry="",
        map="WORLD",
        metdir="/pub/archives/gdas0p5/",
        metfil=metfile,
        Month=month,
        Day=day,
        Hour=hour,
        type="0",
        nhrs="24",
        hgt="0",
        textonly="Yes",
        skewt="1",
        gsize="96",
        pdf="No",
        password1=code,
        Year=year,
        proc=proc
    )
    return payload2

entry_url = 'https://ready.arl.noaa.gov/READYamet.php'
url = "https://ready.arl.noaa.gov/ready2-bin/profile1a.pl"
metfile = make_metfile(year=year, month=month, day=day)
payload = make_payload(metfile, userid=userid, lat=-24.62, lon=-70.40)

result = requests.post(url, data=payload)
soup = BeautifulSoup(result.text, 'lxml')

if 'expired' in str(soup.find_all('h2')):
    print('Your userid', userid, 'is not valid')
    print('Choose another one by login in', entry_url)
    sys.exit()

# extract link to captcha
imgs = soup.find_all("img")
gif_id = [img['src'] for img in imgs if 'Security' in str(img)][0]
gif = 'https://ready.arl.noaa.gov' + gif_id

# download captcha, save
result = requests.get(gif, stream=True)
with open('captcha.png', 'wb') as out_file:
    shutil.copyfileobj(result.raw, out_file)

# Solve captcha
solver = CaptchaSolver('browser')
raw_data = open('captcha.png', 'rb').read()
code = solver.solve_captcha(raw_data)

# Get proc number
inputs = soup.find_all('input')
proc = [inp['value'] for inp in inputs if 'proc' in str(inp)][0]
profile = metfile
payload2 = make_payload2(metfile, proc, code, userid=userid,
                         year=year, month=month, day=day,
                         hour=hour, lat=-24.62, lon=-70.40)

url2 = 'https://ready.arl.noaa.gov/ready2-bin/profile2a.pl'
result = requests.post(url2, data=payload2)
soup = BeautifulSoup(result.text, 'lxml')
pre = soup.find('pre').contents[0]
atm = pre[pre.find('PRESS HGT(MSL) TEMP DEW PT  WND DIR  WND SPD'):pre.find(profile)]

with open('%s_%s.telfit' % (profile, hour), 'w') as p:
    p.write(atm)
print('Writing file:', profile.strip(), '_', hour.strip(), '.telfit', sep="")
