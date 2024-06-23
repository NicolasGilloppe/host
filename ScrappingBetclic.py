from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait

from nordvpn_switcher.nordvpn_switch import initialize_VPN, rotate_VPN
import time

import undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd

from nordvpn_switcher.nordvpn_switch import initialize_VPN, rotate_VPN, terminate_VPN

from selenium.webdriver.edge.service import Service
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import StaleElementReferenceException

from unidecode import unidecode
from seleniumbase import Driver

from Functions import close_all_chrome_instances

def initialize_betclic():
    rotate_VPN(initialize_VPN(area_input=['France']))
    is_driver = False
    while is_driver == False:
        driver = Driver(uc=True, headless2=False, incognito=True)
        driver.get('https://www.betclic.fr/')
        time.sleep(2)
        try:
            if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'cardEvent_content'))):
                is_driver = True
                return driver
        except:
            driver.quit()
            close_all_chrome_instances()
            rotate_VPN(instructions=initialize_VPN(area_input=['France']))

def scrapp_betclic_url(urls):
    dic = {}
    driver = initialize_betclic()
    for pay, url in urls.items():
        try:
            driver.get(url)
            time.sleep(3)
            try:
                driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/button[2]'))
            except:
                pass
            list_url = []
            for match in driver.find_elements(By.CLASS_NAME, 'groupEvents_card.ng-star-inserted'):
                event_text = match.find_element(By.CLASS_NAME, 'event').text.split('\n')
                if len(event_text) == 7:
                    teams = f"{event_text[-5]} - {event_text[-1]}"
                else:
                    teams = f"{event_text[-3]} - {event_text[-1]}"
                href = match.find_element(By.CSS_SELECTOR, 'a').get_attribute('href') 
                list_url.append({teams: href})   
            dic[f'Betclic_{pay}'] = list_url
        except:
            pass
    driver.quit()
    close_all_chrome_instances()
    try:
        terminate_VPN(initialize_VPN(area_input=['France']))
    except:
        pass
    return dic

#urls = {'ARG': 'https://www.betclic.fr/football-s1/etats-unis-mls-c504'}
#print(scrapp_betclic_url(urls))

def scrapp_betclic(driver, home, away, url):
    team_name = {
    'Al Nassr': 'Al Nassr Riyadh',
    'Tromsø': 'Tromsø IL',
    'Brann': 'Brann-Bergen'}
    home, away = team_name.get(home, home), team_name.get(away, away)

    driver.get(url)
    time.sleep(5)
    driver.execute_script("document.body.style.zoom='30%'")
    try:
        driver.execute_script("arguments[0].click();", driver.find_element(By.XPATH, '/html/body/div[1]/div/div[2]/button[2]'))
    except:
        pass
    time.sleep(2)

    path_dict = {'H': 0, 'D': 1, 'A': 2}
    numbers = []
    for ele in driver.find_element(By.CSS_SELECTOR, 'sports-markets-single-market').text.split('\n'):
        try:
            a = float(ele.replace(',', '.'))
            numbers.append(ele)
        except:
            pass
    odd_h, odd_d, odd_a = numbers[path_dict['H']], numbers[path_dict['D']], numbers[path_dict['A']]
    time.sleep(1)
    for head in driver.find_elements(By.CSS_SELECTOR, 'sports-markets-single-market'):
        title = head.find_element(By.CLASS_NAME, 'marketBox_head').text
        if title == 'Nombre total de buts':
            driver.execute_script("arguments[0].click();", head.find_element(By.CLASS_NAME, 'btn.is-medium.is-seeMore.is-tertiary'))
            odds = head.find_element(By.CLASS_NAME, 'ng-star-inserted').text.split('\n')
            for index, odd in enumerate(odds):
                if odd == '+ de 1,5':
                    odd_o1 = odds[index + 1]
                elif odd == '- de 1,5':
                    odd_u1 = odds[index + 1]
                elif odd == '+ de 2,5':
                    odd_o2 = odds[index + 1]
                elif odd == '- de 2,5':
                    odd_u2 =  odds[index + 1]
        elif title == 'Double chance':
            table = head.find_element(By.CLASS_NAME, 'ng-star-inserted').text.split('\n')
            for index, odd in enumerate(table):
                if odd == f'{home} ou Nul':
                    odd_hd = table[index + 1]
                elif odd == f'Nul ou {away}':
                    odd_da = table[index + 1]
        elif title == 'But pour les 2 équipes':
            odd_btts, odd_nobtts = head.find_element(By.CLASS_NAME, 'ng-star-inserted').text.split('\n')[1], head.find_element(By.CLASS_NAME, 'ng-star-inserted').text.split('\n')[3]
    if not odd_o2:
        odd_o2, odd_u2 = 0, 0
    if not odd_o1:
        odd_o1, odd_u1 = 0, 0
    for tab in driver.find_element(By.CLASS_NAME, 'tab.isPrimary.isHot.isScrollable.isBeginning.is-beginning').find_elements(By.CLASS_NAME, 'tab_item'):
        if tab.text == 'Résultats':
            driver.execute_script("arguments[0].click();", tab)
            time.sleep(1)
            break
    time.sleep(2)
    for head in driver.find_elements(By.CSS_SELECTOR, 'sports-markets-single-market'):
        if head.find_element(By.CLASS_NAME, 'marketBox_head').text == 'Résultat & Nombre total de buts':
            driver.execute_script("arguments[0].click();", head.find_element(By.CLASS_NAME, 'btn.is-medium.is-seeMore.is-tertiary'))
            odds = head.find_element(By.CLASS_NAME, 'ng-star-inserted').text.split('\n')
            for index, odd in enumerate(odds):
                if odd == f'{home} et + de 1,5':
                    odd_ho15 = odds[index + 1]
                elif odd == f'{away} et + de 1,5':
                    odd_ao15 = odds[index + 1]
            break
    dic = {'Home': odd_h, 'Draw': odd_d, 'Away': odd_a, 'HD': odd_hd, 'DA': odd_da, 'Over1': odd_o1, 'Under1': odd_u1, 'Over2': odd_o2, 'Under2': odd_u2, 'BTTS': odd_btts, 'NoBTTS': odd_nobtts, 'Ho15': odd_ho15, 'Ao15': odd_ao15}
    try:
        terminate_VPN(initialize_VPN(area_input=['France']))
    except:
        pass
    return dic           

""" driver = initialize_betclic()
time.sleep(1)
print(scrapp_betclic(driver, 'Criciuma SC', 'Botafogo', 'https://www.betclic.fr/football-s1/bresil-serie-a-c187/criciuma-botafogo-m3002266539'))
driver.quit()
close_all_chrome_instances() """


