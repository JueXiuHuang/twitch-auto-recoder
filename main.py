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
browser.maximize_window()

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
    is_mature = result['data'][0]['is_mature']
    return True, is_mature
  else:
    print('Offline')
    return False, False

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

def open_browser(is_mature):
  browser.get(configs['twitch_url'])

  if is_mature:
    print('Stream contains mature.')
    start_watch_btn = WebDriverWait(browser, 60, 0.5)\
                        .until(EC.presence_of_element_located((By.XPATH,
                          '//*[@id="root"]/div/div[2]/div/main/div[1]/\
                          div[3]/div/div/div[2]/div/div[2]/div/div[2]/div\
                          /div/div[7]/div/div[3]/button')))
    start_watch_btn.click()

  try:
    theatre_btn = WebDriverWait(browser, 60, 0.5)\
                        .until(EC.presence_of_element_located((By.XPATH,
                          '//*[@id="channel-player"]/div/div[2]/div[4]/button')))
    theatre_btn.click()
  except:
    print('No theatre mode.')

  try:
    fold_chat_btn = WebDriverWait(browser, 60, 0.5)\
                      .until(EC.presence_of_element_located((By.XPATH,
                            "//*[@aria-label='Collapse Chat']")))
    fold_chat_btn.click()
  except:
    print('No fold btn.')

  try:
    side_btn = browser.find_element(By.XPATH,
                        "//*[@aria-label='Collapse Side Nav']")
    side_btn.click()
  except:
    print('No side nav.')

  
  
  voice_btn = WebDriverWait(browser, 60, 0.5).until(EC.presence_of_element_located((By.XPATH,
                          "//*[@id='channel-player']/div/div[1]/div[2]/div/div[1]/button")))
  try:
    getMute = browser.find_element(By.XPATH, "//*[@aria-label='Unmute (m)']")
    voice_btn.click()
    print('Unmute.')
  except:
    print('No mute.')

while True:
  is_online, is_mature = check_onlline(configs)
  obs_recording = loop.run_until_complete(make_obs_request('GetRecordStatus'))['outputActive']
  
  if is_online and not obs_recording:
    open_browser(is_mature)
    loop.run_until_complete(make_obs_request('StartRecord'))
  elif not is_online and obs_recording:
    loop.run_until_complete(make_obs_request('StopRecord'))
    browser.close()
  
  time.sleep(int(configs['delay'])*60)