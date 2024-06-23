import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from seleniumbase import Driver
from nordvpn_switcher.nordvpn_switch import initialize_VPN, rotate_VPN
from selenium.webdriver.support import expected_conditions as EC
from Functions import close_all_chrome_instances

def initialize_unibet():
    is_driver = False
    while is_driver == False:
        driver = Driver(uc=True, headless2=False, incognito=True)
        driver.get('https://www.unibet.fr/sport')
        time.sleep(2)
        try:
            if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'headlines-content'))):
                is_driver = True
                return driver
        except:
            driver.quit()
            close_all_chrome_instances()

#urls = {'Japan': 'https://www.unibet.fr/sport/football/japon/j1-league'}

def scrapp_unibet_url(urls):
    dic = {}
    driver = initialize_unibet()
    for pay, url in urls.items():
        try:
            driver.get(url)
            time.sleep(2)
            list_url = []
            for match in WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'eventsdays_content'))).find_elements(By.CLASS_NAME, 'eventcard--toplight'):
                try:
                    teams = match.find_element(By.CLASS_NAME, 'eventcard-team-name-desktop').text
                    driver.execute_script("arguments[0].click();", match)
                    time.sleep(2)
                    list_url.append({teams: driver.current_url})
                    driver.back()
                    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'eventsdays_content')))
                    time.sleep(1)
                except:
                    pass
            dic[f'Unibet_{pay}'] = list_url
        except:
            pass
    driver.quit()
    close_all_chrome_instances()
    return dic

#print(scrapp_unibet_url(urls))


def scrapp_unibet(driver, home, away, url):
    driver.get(url)
    time.sleep(2)
    #driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, '/html/body/div[2]/div[2]/div/div[1]/div/div[2]/div/button[2]'))
    driver.execute_script("document.body.style.zoom='30%'")

    try:
        odd_btts, odd_nobtts = None, None
        for tabl in WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'oddbox-content'))):
            if 'Oui' in tabl.text and tabl.text.split('\n')[-1] != '' and odd_btts is None:
                odd_btts = tabl.text.split('\n')[-1]
            elif 'Non' in tabl.text and tabl.text.split('\n')[-1] != '' and odd_nobtts is None:
                odd_nobtts = tabl.text.split('\n')[-1]
            if odd_btts is not None and odd_nobtts is not None:
                break
    except:
        odd_btts, odd_nobtts = 0, 0
    if odd_btts == None:
        odd_btts = 0
    if odd_nobtts == None:
        odd_nobtts = 0
    
    try: 
        odd_h, odd_d, odd_a = driver.find_element(By.XPATH, '/html/body/div[1]/section/div[2]/div[4]/div[2]/section/div/section/section/div/section[4]/section[1]/div[2]/section/section[1]/div[1]/div[2]/span').text, driver.find_element(By.XPATH, '/html/body/div[1]/section/div[2]/div[4]/div[2]/section/div/section/section/div/section[4]/section[1]/div[2]/section/section[2]/div/div[2]/span').text, driver.find_element(By.XPATH, '/html/body/div[1]/section/div[2]/div[4]/div[2]/section/div/section/section/div/section[4]/section[1]/div[2]/section/section[3]/div[1]/div[2]/span').text
    except:
        odd_h, odd_d, odd_a = 0, 0, 0

    try: 
        odd_hd, odd_da = None, None
        for tabl3 in WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CLASS_NAME, 'team-content'))):
            if 'ou Match nul' in tabl3.text:
                if len(tabl3.text.split('\n')) == 9 and odd_hd is None and odd_da is None:
                    odd_hd, odd_da = tabl3.text.split('\n')[1], tabl3.text.split('\n')[7]
                    break
                elif len(tabl3.text.split('\n')) == 12 and odd_hd is None and odd_da is None:
                    odd_hd, odd_da = tabl3.text.split('\n')[1], tabl3.text.split('\n')[9]
                    break
        if odd_hd is None:
            odd_hd = 0
        if odd_da is None:
            odd_da = 0
    except:
        odd_hd, odd_da = 0, 0
    
    try:
        for otabl in WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "section#cps-marketcard.marketcard"))):
            if otabl.find_element(By.CLASS_NAME, 'marketcard-header').text == 'TOTAL DE BUTS':
                for butt in otabl.find_elements(By.CLASS_NAME, 'btn.btn--third'):
                    if butt:
                        driver.execute_script("arguments[0].click();", butt)
                        time.sleep(1)
                        for odd in otabl.find_elements(By.CLASS_NAME, 'odds-outrights-multiple_content'):
                            if 'Plus de 1,5' in odd.text:
                                odd_o1, odd_u1 = odd.text.split('\n')[-1], odd.text.split('\n')[1]
                            if 'Plus de 2,5' in odd.text:
                                odd_o2, odd_u2 = odd.text.split('\n')[-1], odd.text.split('\n')[1]
    except:
        odd_o1, odd_u1, odd_o2, odd_u2 = 0, 0, 0, 0

    try:
        for tab in driver.find_element(By.CLASS_NAME, 'event-market-search-filter-container.no-scrollbar').find_elements(By.CLASS_NAME, 'filter'):
            if tab.text == 'Résultat':
                driver.execute_script("arguments[0].click();", tab.find_element(By.CSS_SELECTOR, 'div'))
                time.sleep(1)
                break
        for market in driver.find_elements(By.ID, 'cps-marketcard'):
            if market.find_element(By.CLASS_NAME, 'marketcard-header').text == 'COMBO RÉSULTAT DU MATCH & TOTAL DE BUTS':
                driver.execute_script("arguments[0].click();", market.find_element(By.CLASS_NAME, 'odds-outrights-multiple_footer').find_element(By.CSS_SELECTOR, 'button'))
                time.sleep(1)
                odds = market.find_element(By.CLASS_NAME, 'marketcard-content').text.split('\n')
                break
        odd_ho15, odd_ao15 = None, None
        for index, odd in enumerate(odds):
            if odd == f'{home} & Plus de 1,5':
                odd_ho15 = odds[index + 1]
            elif odd == f'{away} & Plus de 1,5':
                odd_ao15 = odds[index + 1]
        if odd_ho15 == None:
            odd_ho15 = odds[3]
        if odd_ao15 == None:
            odd_ao15 = odds[11]
    except:
        odd_ho15, odd_ao15 = 0, 0

    dic = {'Home': odd_h, 'Draw': odd_d, 'Away': odd_a, 'HD': odd_hd, 'DA': odd_da, 'Over1': odd_o1, 'Under1': odd_u1, 'Over2': odd_o2, 'Under2': odd_u2, 'BTTS': odd_btts, 'NoBTTS': odd_nobtts, 'Ho15': odd_ho15, 'Ao15': odd_ao15}
    return dic

""" driver = initialize_unibet()
time.sleep(1)
print(scrapp_unibet(driver, 'Incheon United', 'Pohang Steelers', 'https://www.unibet.fr/sport/football/event/incheon-united-pohang-steelers-3040729_1.html')) """

