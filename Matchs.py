import pandas as pd
from bs4 import BeautifulSoup
from Conf import nouveaux_noms, div2_dict, champ_dict, urls_tier2_socc, champ_by_bookie, betclic_urls, stake_urls, unibet_urls, winamax_urls
from pyexcel_ods import get_data
import datetime
import time
from nordvpn_switcher.nordvpn_switch import initialize_VPN, rotate_VPN, terminate_VPN
import mysql
from mysql import connector
import sqlalchemy
from sqlalchemy import create_engine, MetaData
from selenium.common import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.wait import WebDriverWait
import undetected_chromedriver as uc
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium import webdriver
from ScrappingStake import scrapp_stake_url
from ScrappingBetclic import scrapp_betclic_url
from ScrappingUnibet import scrapp_unibet_url
from ScrappingWinamax import scrapp_winamax_url
from Functions import close_all_chrome_instances, close_all_edge_instances

engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')
query = 'Select * From names'

names = pd.read_sql(query, engine)

close_all_edge_instances()
close_all_chrome_instances()
#Import Check from SQL
query = """
    SELECT * From checkdb
    """
check = pd.read_sql(query, engine)

all_champ = []
for valeurs in champ_dict.values():
    if len(valeurs) == 1:
        all_champ.append(valeurs[0])
    else:
        for i in range(0, len(valeurs)):
            all_champ.append(valeurs[i])

options = webdriver.EdgeOptions()
options.add_argument("--headless")
options.add_argument("--start-maximized")
s = Service(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe")

driver = webdriver.Edge(service=s, options=options)
driver.get("https://www.flashscore.com/")
WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[6]/div[2]/div/div[1]/div/div[2]/div/button[1]'))).click()
time.sleep(3)


def scrapping_matchs(utcs):
    for utc in utcs:
        xpaths = ['/html/body/header/div/div[4]/div[1]', '/html/body/header/div/div[4]/div[2]/div/div[1]', '/html/body/header/div/div[4]/div[1]/div/div[3]/div[1]/div/div', f'/html/body/header/div/div[4]/div[1]/div/div[3]/div[1]/div/div/div[2]/div/div[{utc + 1}]']

        for path in xpaths:
            WebDriverWait(driver, 600).until(EC.presence_of_element_located((By.XPATH, path))).click()
            time.sleep(1)

        time.sleep(1)
        webdriver.ActionChains(driver).send_keys(Keys.ESCAPE).perform()
        time.sleep(2)                                                                              
        today_table = WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[1]/div/div/main/div[5]/div[2]/div/section/div')))
        today_table_html = today_table.get_attribute('innerHTML')

        soup = BeautifulSoup(today_table_html, 'html.parser')
        time_list = []
        home_list = []
        away_list = []
        pays_list = []
        champ_list = []

        for row in soup.find_all('div', {'class': ['wclLeagueHeader', 'event__match']}):
            if 'wclLeagueHeader' in row.get('class', []):
                box = row.find('div', class_='event__titleBox').text
                
                try:
                    pays, champ = box.split(':')
                except:
                    if box == 'CZECH REPUBLIC: FORTUNA:LIGA':
                        pays = 'CZECH REPUBLIC'
                        champ = 'FORTUNA:LIGA'
                
                pays = pays.lower().title()
                champ = champ.lstrip()

            if 'event__match' in row.get('class', []):
                try:
                    home = row.find('div', class_='_participant_x6lwl_4 event__homeParticipant').text
                except:
                    home = 'h'
                try:
                    away = row.find('div', class_='_participant_x6lwl_4 event__awayParticipant').text
                except: 
                    away = 'a'

                timee = row.find('div', class_='event__time')
                if timee:
                    timee = timee.text

                home_list.append(home)
                away_list.append(away)
                time_list.append(timee)
                pays_list.append(pays)
                champ_list.append(champ)

        df = pd.DataFrame()
        df['Date'] = ''
        df['Time'] = time_list
        df['Champ'] = champ_list
        df['Home'] = home_list
        df['Away'] = away_list
        df['Pays'] = pays_list

        df = df[df['Home'].isin(names['flashscore']) & df['Away'].isin(names['flashscore'])]
        matchs = df.copy()

        # Import Date
        today = datetime.date.today()
        matchs['Date'] = today.strftime("%d-%m-%y")

        # Clean Unwanted Matches
        matchs = matchs.drop(matchs[matchs['Pays'] == 'World'].index)
        matchs['Pays'] = matchs['Pays'].replace('South Korea', 'Korea').replace('Bosnia And Herzegovina', 'Bosnia').replace('United Arab Emirates', 'Uae')

        # Fix Pays2 Names
        for index, row in matchs.iterrows():
            if row['Pays'] in div2_dict:
                div2_subdict = div2_dict[row['Pays']]
                if row['Champ'] in div2_subdict:
                    matchs.at[index, 'Pays'] = div2_subdict[row['Champ']]

        matchs = matchs[matchs['Champ'].isin(all_champ)]
        matchs = matchs[~matchs['Time'].isin(['Postponed', 'Finished', 'Half Time'])]

        if matchs.empty:
            print('Pas de matchs Aujourdhui')
        else:
            matchs1 = matchs[~matchs['Pays'].isin(list(urls_tier2_socc.keys()))].copy()
            matchs2 = matchs[matchs['Pays'].isin(list(urls_tier2_socc.keys()))].copy()
            print(matchs1)
            print(matchs2)
            for index, row in matchs1.iterrows():
                pays = row['Pays']
                home = row['Home']
                away = row['Away']
                df_pays = pd.read_sql('Select * From leaguesdb', engine)
                df_pays.drop(df_pays[df_pays['Pays'] != pays].index, inplace=True)
                team_data_h = df_pays[df_pays['Squad'] == home].drop(['Pays', 'Squad', 'AW/MP', 'AD/MP', 'AL/MP', 'AGD/MP', 'MPA', 'GFA', 'GAA', 'AGFPG', 'AGAPG', 'AAS', 'ADS', 'MP', 'MPH'], axis=1)
                team_data_h.columns = ['HW/MP', 'HD/MP', 'HL/MP', 'HGD/MP', 'GlsH', 'ShH', 'SoTH', 'SoT%H', 'Sh/90H', 'SoT/90H', 'G/ShH', 'G/SoTH', 'PKH', 'PkattH', 'vs GlsH', 'vs ShH', 'vs SoTH', 'vs SoT%H', 'vs Sh/90H', 'vs SoT/90H', 'vs G/ShH', 'vs G/SoTH', 'vs PKH', 'vs PkattH', 'GFH', 'GAH', 'HGFPG', 'HGAPG', 'HAS', 'HDS']
                print(home)
                for col in team_data_h.columns:
                    matchs1.loc[matchs1['Home'] == home, col] = team_data_h[col].values[0]

                team_data_a = df_pays[df_pays['Squad'] == away].drop(['Pays', 'Squad', 'HW/MP', 'HD/MP', 'HL/MP', 'HGD/MP', 'MPH', 'GFH', 'GAH', 'HGFPG', 'HGAPG', 'HAS', 'HDS', 'MP', 'MPA'], axis=1)
                team_data_a.columns = ['AW/MP', 'AD/MP', 'AL/MP', 'AGD/MP', 'GlsA', 'ShA', 'SoTA', 'SoT%A', 'Sh/90A', 'SoT/90A', 'G/ShA', 'G/SoTA', 'PKA', 'PkattA', 'vs GlsA', 'vs ShA', 'vs SoTA', 'vs SoT%A', 'vs Sh/90A', 'vs SoT/90A', 'vs G/ShA', 'vs G/SoTA', 'vs PKA', 'vs PkattA', 'GFA', 'GAA', 'AGFPG', 'AGAPG', 'AAS', 'ADS']
                print(away)
                for col in team_data_a.columns:
                    matchs1.loc[matchs1['Away'] == away, col] = team_data_a[col].values[0]

            for index, row in matchs1.iterrows():
                df_pays = pd.read_sql('Select * From leaguesdb', engine)
                df_pays = df_pays[df_pays['Pays'] == row['Pays']]
                matchs1.at[index, 'ExpH'] = round((float(row['HAS']) * float(row['ADS']) * round(float(df_pays['HGFPG'].mean()), 2)), 2)
                matchs1.at[index, 'ExpA'] = round((float(row['AAS']) * float(row['HDS']) * round(float(df_pays['AGFPG'].mean()), 2)), 2)

                matchs1.at[index, 'SexpH'] = round((((float(row['ShH']) + float(row['vs ShA'])) / 2) * ((float(row['G/ShH']) + float(row['vs G/ShA'])) / 2) + ((float(row['SoTH']) + float(row['vs SoTA'])) / 2) * ((float(row['G/SoTH']) + float(row['vs G/SoTA'])) / 2)) / 2, 2)
                matchs1.at[index, 'SexpA'] = round(((((float(row['ShA']) + float(row['vs ShH'])) / 2) * ((float(row['G/ShA']) + float(row['vs G/ShH'])) / 2)) + (((float(row['SoTA']) + float(row['vs SoTH'])) / 2) * ((float(row['G/SoTA']) + float(row['vs G/SoTH'])) / 2))) / 2, 2)

            for index, row in matchs2.iterrows():
                pays = row['Pays']
                home = row['Home']
                away = row['Away']
                df_pays = pd.read_sql('Select * From leaguesdb2', engine)
                df_pays.drop(df_pays[df_pays['Pays'] != pays].index, inplace=True)
                print(df_pays)
                team_data_h = df_pays[df_pays['Squad'] == home].drop(['Pays', 'Squad', 'AW/MP', 'GF', 'GA', 'AD/MP', 'AL/MP', 'AGD/MP', 'MPA', 'GFA', 'GAA', 'AGFPG', 'AGAPG', 'AAS', 'ADS', 'MP', 'MPH'], axis=1)
                team_data_h.columns = ['HW/MP', 'HD/MP', 'HL/MP', 'HGD/MP', 'GFH', 'GAH', 'HGFPG', 'HGAPG', 'HAS', 'HDS']
                print(home)
                for col in team_data_h.columns:
                    matchs2.loc[matchs2['Home'] == home, col] = team_data_h[col].values[0]

                team_data_a = df_pays[df_pays['Squad'] == away].drop(['Pays', 'Squad', 'HW/MP', 'GF', 'GA', 'HD/MP', 'HL/MP', 'HGD/MP', 'MPH', 'GFH', 'GAH', 'HGFPG', 'HGAPG', 'HAS', 'HDS', 'MP', 'MPA'], axis=1)
                team_data_a.columns = ['AW/MP', 'AD/MP', 'AL/MP', 'AGD/MP', 'GFA', 'GAA', 'AGFPG', 'AGAPG', 'AAS', 'ADS']
                for col in team_data_a.columns:
                    matchs2.loc[matchs2['Away'] == away, col] = team_data_a[col].values[0]

            for index, row in matchs2.iterrows():
                df_pays = pd.read_sql('Select * From leaguesdb2', engine)
                df_pays = df_pays[df_pays['Pays'] == row['Pays']]
                matchs2.at[index, 'ExpH'] = round((float(row['HAS']) * float(row['ADS']) * round(float(df_pays['HGFPG'].mean()), 2)), 2)
                matchs2.at[index, 'ExpA'] = round((float(row['AAS']) * float(row['HDS']) * round(float(df_pays['AGFPG'].mean()), 2)), 2)

            matchs1 = matchs1.sort_values(by='Time').dropna()
            matchs2 = matchs2.sort_values(by='Time').dropna()
            matchs1.to_sql('alicedb', engine, if_exists='append', index=False)
            matchs2.to_sql('alicedb2', engine, if_exists='append', index=False)
            matchs1.to_sql('matchs1', engine, if_exists='replace', index=False)
            matchs2.to_sql('matchs2', engine, if_exists='replace', index=False)
            print(matchs1)
            print(matchs2)


#scrapping_matchs([15])
driver.quit()

close_all_chrome_instances()
close_all_edge_instances()

start = time.time()
query_names = 'Select * From names'
names = pd.read_sql(query_names, engine)

final_df = pd.DataFrame(columns=['Date', 'Time', 'Champ', 'Home', 'Away', 'Pays', 'Stake_Url', 'Unibet_Url', 'Winamax_Url', 'Betclic_Url'])

for i in ['1', '2']:
    df = pd.read_sql(f'Select * from matchs{i}', engine)
    if not df.empty:
        pays = df['Pays'].unique().tolist()
        urls_stake, urls_unibet, urls_betclic, urls_winamax = {}, {}, {}, {}
        for pay in pays:
            try:
                urls_stake[pay], urls_unibet[pay], urls_winamax[pay], urls_betclic[pay] = stake_urls[pay], unibet_urls[pay], winamax_urls[pay], betclic_urls[pay]
            except:
                pass
        print(urls_stake, urls_unibet, urls_winamax, urls_betclic)
        dic_stake, dic_unibet, dic_betclic, dic_winamax = scrapp_stake_url(urls_stake), scrapp_unibet_url(urls_unibet), scrapp_betclic_url(urls_betclic), scrapp_winamax_url(urls_winamax)

        print(dic_stake)
        print(dic_unibet)
        print(dic_winamax)
        print(dic_betclic)

        df['Stake_Url'], df['Unibet_Url'], df['Betclic_Url'], df['Winamax_Url'] = '', '', '', ''
        for index, row in df.iterrows():
            for book in ['Stake', 'Winamax', 'Unibet', 'Betclic']:
                home, away = names[names['flashscore'] == row['Home']][f'{book.lower()}'].values[0], names[names['flashscore'] == row['Away']][f'{book.lower()}'].values[0]
                try:
                    if book == 'Stake':
                        for _ in dic_stake[f"Stake_{row['Pays']}"]: 
                            for key, val in _.items():
                                if key == f"{home} - {away}":
                                    df.at[index, 'Stake_Url'] = val
                    elif book == 'Unibet':
                        for _ in dic_unibet[f"Unibet_{row['Pays']}"]:
                            for key, val in _.items():
                                if key == f"{home} - {away}":
                                    df.at[index, 'Unibet_Url'] = val
                    elif book == 'Winamax':
                        for _ in dic_winamax[f"Winamax_{row['Pays']}"]:
                            for key, val in _.items():
                                if key == f"{home} - {away}":
                                    df.at[index, 'Winamax_Url'] = val
                    elif book == 'Betclic':
                        for _ in dic_betclic[f"Betclic_{row['Pays']}"]:
                            for key, val in _.items():
                                if key == f"{home} - {away}":
                                    df.at[index, 'Betclic_Url'] = val
                except:
                    df.at[index, f'{book}_Url'] = ''

        df = df[['Date', 'Time', 'Champ', 'Home', 'Away', 'Pays', 'Stake_Url', 'Unibet_Url', 'Winamax_Url', 'Betclic_Url']]
        final_df = pd.concat([final_df, df])
        df.to_sql(f'urls_{i}', engine, if_exists='replace', index=False)
        print(df)
        df.to_excel('Alice.xlsx')

print(final_df)
final_df.to_sql('urls_all', engine, if_exists='replace', index=False)
close_all_chrome_instances()
close_all_edge_instances()

end = time.time()
print('Script executed in', end - start, 'secondes')