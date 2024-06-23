from sqlalchemy import create_engine
import pandas as pd
from Conf import empty_odds
import time
from pymongo.mongo_client import MongoClient
from ScrappingStake import scrapp_stake, initialize_stake
from ScrappingBetclic import scrapp_betclic, initialize_betclic
from ScrappingUnibet import scrapp_unibet, initialize_unibet
from ScrappingWinamax import scrapp_winamax, initialize_winamax
from nordvpn_switcher.nordvpn_switch import initialize_VPN, rotate_VPN, terminate_VPN
from pymongo.mongo_client import MongoClient
from Functions import close_all_chrome_instances

start = time.time()
# Create DB Connection
engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')

uri = "mongodb+srv://nicolasgilloppe:s0S8eaYt0mIMdYE7@alicedb.eqrplwk.mongodb.net/?retryWrites=true&w=majority&appName=alicedb"
cluster = MongoClient(uri, connectTimeoutMS=30000, socketTimeoutMS=30000)
db = cluster["alicedb"]
collection = db['odds_1']

engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')
names = pd.read_sql('Select * From names', engine)
df = pd.read_sql('Select * From urls_all', engine)

stake_urls, unibet_urls, winamax_urls, betclic_urls = {}, {}, {}, {}
instructions = initialize_VPN(area_input=['France'])

for index, row in df.iterrows():
    if row['Stake_Url'] is not None:
        stake_urls[f"{row['Home']} - {row['Away']}"] = row['Stake_Url']
    if row['Unibet_Url'] is not None:
        unibet_urls[f"{row['Home']} - {row['Away']}"] = row['Unibet_Url']
    if row['Betclic_Url'] is not None:
        home_b, away_b = names[names['flashscore'] == row['Home']]['betclic'].values[0], names[names['flashscore'] == row['Away']]['betclic'].values[0]
        betclic_urls[f"{home_b} - {away_b}"] = row['Betclic_Url']
    if row['Winamax_Url'] is not None:
        home_w, away_w = names[names['flashscore'] == row['Home']]['winamax'].values[0], names[names['flashscore'] == row['Away']]['winamax'].values[0]
        winamax_urls[f"{home_w} - {away_w}"] = row['Winamax_Url']

close_all_chrome_instances()
try:
    terminate_VPN()
except:
    pass
odds_stake, odds_unibet, odds_winamax, odds_betclic = {}, {}, {}, {}

driver = initialize_stake()
time.sleep(1)
driver.maximize_window()
time.sleep(3)
for key, value in stake_urls.items():
    time.sleep(1)
    home, away = key.split(' - ')
    print(home, away, value)
    try:
        odd = scrapp_stake(driver, home, away, value)
        print(odd)
        odds_stake[key] = odd
    except: 
        try: 
            odd = scrapp_stake(driver, home, away, value)
            print(odd)
            odds_stake[key] = odd
        except:
            odd = empty_odds
            print(odd)
            odds_stake[key] = odd
driver.quit()
close_all_chrome_instances()

driver = initialize_winamax()
for key, value in winamax_urls.items():
    time.sleep(2)
    home, away = key.split(' - ')
    print(home, away, value)
    try:
        odd = scrapp_winamax(driver, home, away, value)
        print(odd)
        odds_winamax[key] = odd
    except: 
        try: 
            odd = scrapp_winamax(driver, home, away, value)
            print(odd)
            odds_winamax[key] = odd
        except:
            odd = empty_odds
            print(odd)
            odds_winamax[key] = odd
driver.quit()
close_all_chrome_instances()

driver = initialize_betclic()
for key, value in betclic_urls.items():
    time.sleep(2)
    home, away = key.split(' - ')
    print(home, away, value)
    try:
        odd = scrapp_betclic(driver, home, away, value)
        print(odd)
        odds_betclic[key] = odd
    except: 
        try: 
            odd = scrapp_betclic(driver, home, away, value)
            print(odd)
            odds_betclic[key] = odd
        except:
            odd = empty_odds
            print(odd)
            odds_betclic[key] = odd
driver.quit()
close_all_chrome_instances()

driver = initialize_unibet()
for key, value in unibet_urls.items():
    time.sleep(2)
    home, away = key.split(' - ')
    print(home, away, value)
    try:
        odd = scrapp_unibet(driver, home, away, value)
        print(odd)
        odds_unibet[key] = odd
    except:
        try: 
            odd = scrapp_unibet(driver, home, away, value)
            print(odd)
            odds_unibet[key] = odd
        except:
            odd = empty_odds
            print(odd)
            odds_unibet[key] = odd
driver.quit()
close_all_chrome_instances()

print(odds_stake)
print(odds_unibet)
print(odds_betclic)
print(odds_winamax)

for match, dic in odds_stake.items():
    home, away = match.split(' - ')
    for key, value in dic.items():
        try:
            df.loc[(df['Home'] == home) & (df['Away'] == away), f'Stake_{key}'] = value.replace(',', '.')
        except:
            df.loc[(df['Home'] == home) & (df['Away'] == away), f'Stake_{key}'] = value

for match, dic in odds_unibet.items():
    home, away = match.split(' - ')
    for key, value in dic.items():
        try:
            df.loc[(df['Home'] == home) & (df['Away'] == away), f'Unibet_{key}'] = value.replace(',', '.')
        except:
            df.loc[(df['Home'] == home) & (df['Away'] == away), f'Unibet_{key}'] = value

for match, dic in odds_betclic.items():
    home, away = match.split(' - ')
    home_f, away_f = names[names['betclic'] == home]['flashscore'].values[0], names[names['betclic'] == away]['flashscore'].values[0]
    for key, value in dic.items():
        try:
            df.loc[(df['Home'] == home_f) & (df['Away'] == away_f), f'Betclic_{key}'] = value.replace(',', '.')
        except:
            df.loc[(df['Home'] == home_f) & (df['Away'] == away_f), f'Betclic_{key}'] = value

for match, dic in odds_winamax.items():
    home, away = match.split(' - ')
    home_f, away_f = names[names['winamax'] == home]['flashscore'].values[0], names[names['winamax'] == away]['flashscore'].values[0]
    for key, value in dic.items():
        try:
            df.loc[(df['Home'] == home_f) & (df['Away'] == away_f), f'Winamax_{key}'] = value.replace(',', '.')
        except:
            df.loc[(df['Home'] == home_f) & (df['Away'] == away_f), f'Winamax_{key}'] = value

print(df)
df.to_excel('Alice.xlsx')
df.to_sql('odds_1', engine, if_exists='replace', index=False)
collection = db['odds_df']
collection.delete_many({})
collection.insert_many(df.to_dict(orient="records"))

df = pd.read_sql('Select * from odds_1', engine).fillna(0)
predi = pd.read_sql('Select * From predicted_1', engine)  
query_wrp = 'Select * From wr_pays'
wrp = pd.read_sql(query_wrp, engine)

query_wrb = 'Select * From wr_bets'
wrb = pd.read_sql(query_wrb, engine)

for index, row in predi.iterrows():
    bet_dic = {'H': 'Home', 'D': 'Draw', 'A': 'Away', 'HD': 'HD', 'DA': 'DA', 'O': 'Over', 'U': 'Under', 'BTTS': 'BTTS', 'NoBTTS': 'NoBTTS'}
    bet = bet_dic[row['Bets']]

    coeff = wrb[wrb['Bets'] == row['Bets']]['Pick'].values[0] + wrp[wrp['Pays'] == row['Pays']]['Pick'].values[0]
    matching_row = df[df['Home'] == row['Home']]
    for book in ['Stake', 'Unibet', 'Winamax', 'Betclic']:
        predi.at[index, f'Odds_{book}'] = matching_row[f'{book}_{bet}'].values[0]
        predi.at[index, f'{book}_Url'] = matching_row[f'{book}_Url'].values[0]

    max_odd = max(float(matching_row[f'Betclic_{bet}'].values[0]), float(matching_row[f'Stake_{bet}'].values[0]), float(matching_row[f'Winamax_{bet}'].values[0]), float(matching_row[f'Unibet_{bet}'].values[0]))
    predi.at[index, 'Max'] = max_odd
    if max_odd < 1.6:
        coeff += 1
    elif max_odd < 2:
        coeff += 0.5

    predi.at[index, 'Coeff'] = coeff
    

print(predi)
collection = db['odds_1']
collection.delete_many({})
collection.insert_many(predi.to_dict(orient="records"))


end = time.time()

print('Script Executé en', end - start, 'secondes')