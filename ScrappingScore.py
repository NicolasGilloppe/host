import pandas as pd
from bs4 import BeautifulSoup
import datetime
from sqlalchemy import create_engine
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.edge.service import Service
from selenium import webdriver
from Conf import flash_urls
from pymongo.mongo_client import MongoClient


uri = "mongodb+srv://nicolasgilloppe:s0S8eaYt0mIMdYE7@alicedb.eqrplwk.mongodb.net/?retryWrites=true&w=majority&appName=alicedb"
cluster = MongoClient(uri, connectTimeoutMS=30000, socketTimeoutMS=30000)
db = cluster["alicedb"]
collection = db['alicedb']

# Import Date
today = datetime.date.today()
today = today.strftime("%d-%m-%y")

options = webdriver.EdgeOptions()
options.add_argument("--headless")
options.add_argument("--start-maximized")
s = Service(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedgedriver.exe")

engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')
    
def scrapping_score(row):
    url = flash_urls[row['Pays']]
    home_team = row['Home']
    away_team = row['Away']

    driver = webdriver.Edge(service=s, options=options)
    driver.get(url)                                                                                                                       
    today_table = WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[4]/div[1]/div/div[1]/main/div[5]/div[2]/div[1]/div[1]/div/div')))
    today_table_html = today_table.get_attribute('innerHTML')
    driver.quit()

    soup = BeautifulSoup(today_table_html, 'html.parser')

    home_list = []
    away_list = []
    scoreh_list = []
    scorea_list = []

    for row in soup.find_all('div', {'class': 'event__match'}):
        home, away, scoreh, scorea = row.find('div', class_='_participant_x6lwl_4 event__homeParticipant').text, row.find('div', class_='_participant_x6lwl_4 event__awayParticipant').text, row.find('div', class_='event__score event__score--home').text, row.find('div', class_='event__score event__score--away').text        
        home_list.append(home)
        away_list.append(away)
        scoreh_list.append(scoreh)
        scorea_list.append(scorea)

    result = pd.DataFrame()
    result['Home'] = home_list
    result['ScoreH'] = scoreh_list
    result['ScoreA'] = scorea_list
    result['Away'] = away_list

    result = result[(result['Home'] == home_team) & (result['Away'] == away_team)]
    return result

def add_btts(row):
    goalh = int(row['GoalH'])
    goala = int(row['GoalA'])

    if goalh > 0 and goala > 0:
        return 'BTTS'
    else:
        return 'NoBTTS'
    
def add_over2(row):
    goalh = int(row['GoalH'])
    goala = int(row['GoalA'])

    if (goalh + goala) > 2:
        return 'O2'
    else:
        return 'U2'
    
def add_over1(row):
    goalh = int(row['GoalH'])
    goala = int(row['GoalA'])

    if (goalh + goala) > 1:
        return 'O1'
    else:
        return 'U1'

def add_result(row):
    goalh = int(row['GoalH'])
    goala = int(row['GoalA'])

    if goalh > goala:
        return 'H'
    elif goalh == goala:
        return 'D'
    else:
        return 'A'
    
def add_ho(row):
    goalh = int(row['GoalH'])
    goala = int(row['GoalA'])

    if goalh > goala and (goala + goalh) > 1:
        return 'Ho15'
    elif goala > goalh and (goalh + goala) > 1:
        return 'Ao15'
    else:
        return 'No'
    

for _ in ['', '2']:
    df = pd.read_sql(f'Select * From alicedb{_}', engine)

    for index, row in df.iterrows():
        if row['Date'] != today:
            if pd.isna(row['GoalH']):
                print('Missing Score')
                try:
                    score = scrapping_score(row)
                except:
                    pass
                print(score)
                if not score.empty:
                    df.at[index, 'GoalH'] = score['ScoreH'].iloc[0]
                    df.at[index, 'GoalA'] = score['ScoreA'].iloc[0]
            else:
                print('Score Already Here')
     
    condition = (df['Date'] == today) | df['GoalH'].notna()
    df = df[condition]

    df.loc[(df['BTTS'].isna()) & (df['Date'] != today), 'BTTS'] = df.loc[(df['BTTS'].isna()) & (df['Date'] != today)].apply(add_btts, axis=1)
    df.loc[(df['Over1'].isna()) & (df['Date'] != today), 'Over1'] = df.loc[(df['Over1'].isna()) & (df['Date'] != today)].apply(add_over1, axis=1)
    df.loc[(df['Over2'].isna()) & (df['Date'] != today), 'Over2'] = df.loc[(df['Over2'].isna()) & (df['Date'] != today)].apply(add_over2, axis=1)
    df.loc[(df['Result'].isna()) & (df['Date'] != today), 'Result'] = df.loc[(df['Result'].isna()) & (df['Date'] != today)].apply(add_result, axis=1)
    df.loc[(df['Ho15'].isna()) & (df['Date'] != today), 'Ho15'] = df.loc[(df['Ho15'].isna()) & (df['Date'] != today)].apply(add_ho, axis=1)

    print(df)
    df.to_sql(f'alicedb{_}', engine, if_exists='replace', index=False)

    if _ == '':
        data = df.to_dict(orient="records")
        collection.delete_many({})
        collection.insert_many(data)