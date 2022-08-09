from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains

options = Options()
options.add_extension('./uBlock-Origin.crx')
options.add_experimental_option('prefs', {'intl.accept_languages': 'en,en_US'})
browser = webdriver.Chrome('./chromedriver.exe', options=options)

# browser = webdriver.Chrome(param["chrome_path"])
browser.get('https://www.twitch.tv/beryl_lulu')

full_screen_btn = WebDriverWait(browser, 60, 0.5).until(EC.presence_of_element_located((By.CSS_SELECTOR,
                        '#channel-player > div > div.Layout-sc-nxg1ff-0.dIyPHK.player-controls__right-control-group > \
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

