import requests
import json
import simpleobsws
import asyncio
import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# load config file
configs = {}
with open('config.txt', 'r', encoding='utf-8') as f:
  lines = f.readlines()
  for line in lines:
    line = line.replace('\n', '')
    key, value = line.split('=')
    configs[key] = value

# setup OBS websocket
parameters = simpleobsws.IdentificationParameters(ignoreNonFatalRequestChecks = False)
ws = simpleobsws.WebSocketClient(url = 'ws://localhost:%s' % configs['obs_port'],
                                  identification_parameters = parameters)
loop = asyncio.get_event_loop()

# setup selenium
options = Options()
options.add_extension('./uBlock-Origin.crx')
options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
browser = webdriver.Chrome('./chromedriver.exe', options=options)

def check_onlline(configs):
  # get Authorization token
  r = requests.post('https://id.twitch.tv/oauth2/token',
                    data={'client_id':configs['client_id'],
                    'client_secret':configs['client_secret'],
                    'grant_type':'client_credentials'})
  access_token = r.json()['access_token']
  
  # get streamer ID
  headers = {'Authorization':'Bearer %s'%access_token,
            'Client-Id':configs['client_id']}
  r = requests.get('https://api.twitch.tv/helix/users?login=%s'%configs['streamer_name'],
                  headers=headers)
  streamer_id = r.json()['data'][0]['id']
  
  # check streamer is online or not
  headers = {'Authorization':'Bearer %s'%access_token,
            'Client-Id':configs['client_id']}
  r = requests.get('https://api.twitch.tv/helix/streams?user_id=%s'%streamer_id,
                  headers=headers)
  
  result = r.json()
  
  if len(result['data']) != 0:
    print('Online')
    return True
  else:
    print('Offline')
    return False

async def make_obs_request(request_str):
  await ws.connect()
  await ws.wait_until_identified()
  request = simpleobsws.Request(request_str) # use StartRecord and StopRecord to control obs

  ret = await ws.call(request) # Perform the request
  if ret.ok(): # Check if the request succeeded
    print('Request succeeded!')
    return ret.responseData
  else:
    print(ret)

def open_browser():
  browser.get(configs['twitch_url'])

  full_screen_btn = WebDriverWait(browser, 60, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                          '#channel-player > div > \
                          div.Layout-sc-nxg1ff-0.dIyPHK.player-controls__right-control-group > \
                          div:nth-child(6) > button')))

  full_screen_btn.click()
  
  voice_btn = WebDriverWait(browser, 60, 0.5).until(EC.presence_of_element_located((By.XPATH,
                          "//*[@id='channel-player']/div/div[1]/div[2]/div/div[1]/button")))
  try:
    getMute = browser.find_element(By.XPATH, "//*[@aria-label='Unmute (m)']")
    voice_btn.click()
    print('unmute')
  except:
    print('no mute')

while True:
  is_online = check_onlline(configs)
  obs_recording = loop.run_until_complete(make_obs_request('GetRecordStatus'))['outputActive']
  
  if is_online and not obs_recording:
    open_browser()
    loop.run_until_complete(make_obs_request('StartRecord'))
  elif not is_online and obs_recording:
    loop.run_until_complete(make_obs_request('StopRecord'))
    browser.close()
  
  time.sleep(int(configs['delay'])*60)