from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from nordvpn_switcher.nordvpn_switch import initialize_VPN, rotate_VPN
import time
from Functions import close_all_chrome_instances
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from seleniumbase import Driver
import random

def initialize_winamax():
    is_driver = False
    while is_driver == False:
        driver = Driver(uc=True, headless2=False, incognito=True)
        driver.get('https://www.winamax.fr/paris-sportifs')
        time.sleep(2)
        try:
            if WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, 'container'))):
                is_driver = True
                return driver
        except:
            driver.quit()
            close_all_chrome_instances()
            rotate_VPN(instructions=initialize_VPN(area_input=['France']))


#urls = {'Argentina': 'https://www.winamax.fr/paris-sportifs/sports/1/26/18'}
def scrapp_winamax_url(urls):
    dic = {}
    driver = initialize_winamax()
    for pay, url in urls.items():
        try:
            driver.get(url)
            time.sleep(2)
            driver.execute_script("document.body.style.zoom='30%'")
            time.sleep(2)

            # Click Cookies Button
            x, y = random.randint(420, 480), random.randint(200, 280)
            actions = ActionChains(driver)
            actions.move_by_offset(x,y).click().perform()
            """ try:
                cookie_button = WebDriverWait(driver, 30).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'sc-jGKxIK.sc-guJBdh.sc-hZDyAQ.sc-gvPdwL.BKCRO.cwgzut.jDqKPQ.jcPFMp'))
                ).find_element(By.CLASS_NAME, 'tarteaucitronCTAButton.tarteaucitronAllow')
                driver.execute_script("arguments[0].click();", cookie_button)
                time.sleep(1)
            except:
                pass """

            # Click Login Button
            try:
                login_button = WebDriverWait(driver, 10).until(
                    EC.element_to_be_clickable((By.CLASS_NAME, 'sc-jGKxIK.sc-guJBdh.sc-hZDyAQ.sc-gvPdwL.BKCRO.cwgzut.jDqKPQ.jcPFMp'))
                )
                driver.execute_script("arguments[0].click();", login_button)
                time.sleep(1)
            except:
                pass

            list_url = []
            elements = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "[data-testid]"))
            )

            for el in elements:
                if el.get_attribute('data-testid') != 'middleColumn':
                    try:
                        teams = el.find_element(By.CSS_SELECTOR, 'a')
                        if teams.text.split('\n')[-1] == 'paris':
                            a, b = teams.text.split('\n')[0], teams.text.split('\n')[2]
                        else:
                            a, b = teams.text.split('\n')[0], teams.text.split('\n')[4]
                        team = f"{a} - {b}"    
                        href = teams.get_attribute('href')
                        new = {team: href}
                        list_url.append(new)
                        
                    except:
                        pass

            dic[f'Winamax_{pay}'] = list_url
        except:
            pass
    driver.quit()
    close_all_chrome_instances()
    return dic

#print(scrapp_winamax_url(urls))

def scrapp_winamax(driver, home, away, url):
    driver.get(url)
    time.sleep(5)
    driver.execute_script("document.body.style.zoom='30%'")

    # Click Cookies Button
    x, y = random.randint(420, 480), random.randint(200, 280)
    actions = ActionChains(driver)
    actions.move_by_offset(x,y).click().perform()                                                                    
    driver.execute_script("document.body.style.zoom='30%'")
    time.sleep(1)

    try:
        path_dict = {'HD': 2, 'DA': 8, 'O': 1, 'U': 4, 'BTTS': 2, 'NoBTTS': 5}
        odds_h, odds_d, odds_a = [], [], []                                  
        for tab in driver.find_elements(By.CLASS_NAME, "ReactVirtualized__Grid.ReactVirtualized__List"):
            odds = tab.text.split('\n')
        for index, odd in enumerate(odds):
            if odd == home or home in odd or odd in home:
                odds_h.append(odds[index + 1])
            elif odd == away or away in odd or odd in away:
                odds_a.append(odds[index + 1])
            elif odd == 'Match nul':
                odds_d.append(odds[index + 1])
            elif odd == 'Double chance':
                if ',' not in odds[index + path_dict['HD']]:
                    odd_hd =  odds[index + path_dict['HD'] +1]
                else:
                    odd_hd = odds[index + path_dict['HD']]
                if ',' not in odds[index + path_dict['DA']]:
                    odd_da =  odds[index + path_dict['DA'] +1]
                else:
                    odd_da = odds[index + path_dict['DA']]
            elif odd == 'Les 2 équipes marquent':
                if ',' not in odds[index + path_dict['BTTS']]:
                    odd_btts, odd_nobtts = odds[index + path_dict['BTTS'] +1], odds[index + path_dict['NoBTTS'] +1]
                else:
                    odd_btts, odd_nobtts = odds[index + path_dict['BTTS']], odds[index + path_dict['NoBTTS']]
    except:
        odd_h, odd_d, odd_a, odd_hd, odd_da, odd_btts, odd_nobtts = 0, 0, 0, 0, 0, 0, 0
    
    try:
        odd_o1, odd_o2 = None, None
        for element in driver.find_elements(By.CLASS_NAME, 'sc-QFgvm.gLBgIs'):
            value = element.get_attribute('style')
            if 'height: ' in value and 'px; left: ' in value and 'px; position: absolute; top: ' in value and 'px; width: 100%;' in value:
                if element.text.split('\n')[0] == 'Nombre de buts':
                    driver.execute_script("arguments[0].click();", element.find_element(By.CLASS_NAME, 'sc-dFfFtc.jJKhBC'))
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", element.find_element(By.CLASS_NAME, 'sc-dcbbvR.ckUCie'))
                    time.sleep(0.5)    
                    for odd in element.find_elements(By.CLASS_NAME, 'sc-iiCjWg.eOqpQK'):
                        odd = odd.text.split('\n')
                        if 'Plus de' not in odd[0]: 
                            odd.remove(odd[0])
                        if odd[0] == 'Plus de 1,5':
                            odd_o1, odd_u1 = odd[path_dict['O']], odd[path_dict['U']]
                        elif odd[0] == 'Plus de 2,5':
                            odd_o2, odd_u2 =  odd[path_dict['O']], odd[path_dict['U']]   
        if not odd_o2:
            odd_o2, odd_u2 = 0, 0 
        if not odd_o1:
            odd_o1, odd_u1 = 0, 0
    except:
        odd_o1, odd_u1, odd_o2, odd_u2 = 0, 0, 0, 0

    if len(odds_h) > 0:
        odd_h, odd_d, odd_a = odds_h[0], odds_d[0], odds_a[0]    
    else:
        odd_h, odd_d, odd_a = 0, 0, 0                       

    try:
        time.sleep(1)
        liste, resultat_found = [], None
        while resultat_found is None:
            buttons = driver.find_element(By.CLASS_NAME, 'sc-cDsqlO.culsln.filter-wrapper-list').find_elements(By.CLASS_NAME, 'sc-dIHSXr.dGDFTW.filter-button')
            for butt in buttons:
                if 'Résultat' in butt.text:
                    driver.execute_script("arguments[0].click();", butt)
                    resultat_found = True
                    break
            else:
                for butt in buttons:
                    if butt.text == '':
                        driver.execute_script("arguments[0].click();", butt)
                        time.sleep(1)
                        break
        for tab in driver.find_elements(By.CLASS_NAME, "sc-gLjfqm.bceKAV.sc-lgPrIz.kKdgWl"):
            if tab.find_element(By.CLASS_NAME, 'sc-gXdwyB.cFwvkc').text == 'Résultat et nombre de buts':
                driver.execute_script("arguments[0].click();", tab.find_element(By.CLASS_NAME, 'sc-tSoMJ.dsKpEL.expand-button.sc-hVKATT.ddXhVm'))
                time.sleep(1)
                for row in tab.find_elements(By.CLASS_NAME, 'sc-hGWFOF.kReFMD.sc-dKBpOM.qaMGU'):
                    liste.append(row.text)
        odd_ho15, odd_ao15 = liste[0].split('\n')[1], liste[2].split('\n')[1]
    except:
        odd_ho15, odd_ao15 = 0, 0

    dic = {'Home': odd_h, 'Draw': odd_d, 'Away': odd_a, 'HD': odd_hd, 'DA': odd_da, 'Over1': odd_o1, 'Under1': odd_u1, 'Over2': odd_o2, 'Under2': odd_u2, 'BTTS': odd_btts, 'NoBTTS': odd_nobtts, 'Ho15': odd_ho15, 'Ao15': odd_ao15}
    return dic

""" driver = initialize_winamax()
time.sleep(1)
print(scrapp_winamax(driver, 'Jeju United', 'Ulsan HD FC', 'https://www.winamax.fr/paris-sportifs/match/47092159'))
driver.quit() """
close_all_chrome_instances()

