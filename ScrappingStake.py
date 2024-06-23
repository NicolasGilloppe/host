import time
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
import re
from seleniumbase import Driver
from nordvpn_switcher.nordvpn_switch import terminate_VPN, initialize_VPN
from selenium.webdriver.support import expected_conditions as EC
from Conf import empty_odds
from Functions import close_all_chrome_instances

close_all_chrome_instances()

def initialize_stake():
    terminate_VPN(initialize_VPN(area_input=['France']))
    is_driver = False
    while is_driver == False:
        driver = Driver(uc=True, headless2=False, incognito=True)
        driver.get('https://stake.bet/fr')
        time.sleep(2)
        try:
            if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'header-wrapper.svelte-1nuwc3t'))):
                is_driver = True
                return driver
        except:
            driver.quit()
            close_all_chrome_instances()
            terminate_VPN(initialize_VPN(area_input=['France']))

def scrapp_stake_url(urls):
    dic = {}
    driver = initialize_stake()

    for pay, url in urls.items():
        driver.get(url)
        time.sleep(4)
        list_url = []
        try:
            driver.execute_script("arguments[0].click();", driver.find_element(By.CLASS_NAME, 'content.svelte-i9feae.is-open').find_element(By.CSS_SELECTOR, 'div[class="contents"][data-loader-content=""]'))
            time.sleep(2)
        except:
            pass
        try:
            matches = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[class*='fixture-preview']")))
            for match in matches:
                try:
                    href = match.find_element(By.CSS_SELECTOR, 'a').get_attribute('href')
                    for index, _ in enumerate(match.text.split('\n')):
                        if _ == '1x2':
                            home, away = match.text.split('\n')[index + 1], match.text.split('\n')[index + 5]
                            break
                    game = f"{home} - {away}"
                    new = {game: href}
                    list_url.append(new)
                except:
                    pass
        except Exception as e:
            continue
        dic[f'Stake_{pay}'] = list_url
    driver.quit()
    close_all_chrome_instances()
    return dic

""" urls = {'China': 'https://stake.bet/fr/sports/soccer/usa/major-league-soccer'}
print(scrapp_stake_url(urls)) """


def scrapp_stake(driver, home, away, url):
    time.sleep(2)
    driver.get(url)
    time.sleep(3)
    driver.maximize_window()
    
    try:
        ended = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'no-markets.svelte-ect7x')))
        ended = True
    except:
        ended = False

    # Check if Odds available
    try:
        table = WebDriverWait(driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[class*='odds']")))
        is_table = True
    except:
        is_table = False   
    
    if ended == True and is_table == False:
        return empty_odds
    elif ended == False and is_table == True:
        try:
            path_dict = {'H': 0, 'D': 2, 'A': 4}
            all_odds = []
            for _ in table:
                if re.match(r'^\d{1,2},\d{2}$', _.text):
                    all_odds.append(_.text)
            odd_h, odd_d, odd_a =  all_odds[path_dict['H']], all_odds[path_dict['D']], all_odds[path_dict['A']]
        except:
            odd_h, odd_d, odd_a = 0, 0, 0
        try:
            for table in driver.find_elements(By.CSS_SELECTOR, "[class*='secondary-accordion'][class*='level-2']"):
                if 'Total Asiatique' in table.find_element(By.CSS_SELECTOR, "[class*='header']").text:
                    l = []
                    for row in table.find_elements(By.CSS_SELECTOR, "[class*='outcome']"):
                        bet, odd = row.text.splitlines()
                        if bet == '1.5':
                            l.append(odd)
                        elif bet == '2.5':
                            l.append(odd)
                    odd_o1, odd_u1, odd_o2, odd_u2 = l[0], l[2], l[4], l[6]
                    break
        except:
            odd_o1, odd_u1, odd_o2, odd_u2 = 0, 0, 0, 0
        try:
            for table in driver.find_elements(By.CSS_SELECTOR, "[class*='secondary-accordion'][class*='level-2']"):
                if 'Double chance' in table.find_element(By.CSS_SELECTOR, "[class*='header']").text:
                    for row in table.find_elements(By.CSS_SELECTOR, 'button'):
                        if 'Match nul ou' in row.text:
                            bet, odd_da = row.text.splitlines()
                        elif 'ou Match nul' in row.text:
                            bet, odd_hd = row.text.splitlines()
                    break
        except:
            odd_hd, odd_da = 0, 0
        try:
            for table in driver.find_elements(By.CSS_SELECTOR, "[class*='secondary-accordion'][class*='level-2']"):
                if 'Les deux équipes qui marquent' in table.find_element(By.CSS_SELECTOR, "[class*='header']").text:
                    for row in table.find_elements(By.CSS_SELECTOR, 'button'):
                        bet, odd = row.text.splitlines()
                        if 'oui' in row.text:
                            odd_btts = odd
                        elif 'non' in row.text:
                            odd_nobtts = odd
        except:
            odd_btts, odd_nobtts = 0, 0
        try:
            liste = []
            for butt in driver.find_element(By.CLASS_NAME, 'content-wrapper.svelte-1vkrcyy').find_elements(By.CSS_SELECTOR, 'button'):
                if butt.text == 'Spéciaux':
                    driver.execute_script("arguments[0].click();", butt)
                    time.sleep(15)
                    for ta in driver.find_elements(By.CSS_SELECTOR, "[class*='secondary-accordion'][class*='level-2']"):
                        if '1x2 & total' in ta.find_element(By.CSS_SELECTOR, "[class*='header']").text:
                            for row in ta.find_elements(By.CSS_SELECTOR, "[class*='outcome']"):
                                liste.append(row.text)
                            break
            h, odd_ho15 = liste[2].split('\n')
            a, odd_ao15 = liste[10].split('\n')
        except:
            odd_ho15, odd_ao15 = 0,0
        dic = {'Home': odd_h, 'Draw': odd_d, 'Away': odd_a, 'HD': odd_hd, 'DA': odd_da, 'Over1': odd_o1, 'Under1': odd_u1, 'Over2': odd_o2, 'Under2': odd_u2, 'BTTS': odd_btts, 'NoBTTS': odd_nobtts, 'Ho15': odd_ho15, 'Ao15': odd_ao15}
        return dic

#driver = initialize_stake()
#print(scrapp_stake(driver, 'Fortuna Düsseldorf', 'VFL Bochum', 'https://stake.bet/fr/sports/soccer/republic-of-korea/k-league-2/44422066-ansan-greeners-fc-cheonan-city-fc'))
   


close_all_chrome_instances()