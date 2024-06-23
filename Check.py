import pandas as pd
from nordvpn_switcher.nordvpn_switch import initialize_VPN,rotate_VPN
import mysql
from mysql import connector
import sqlalchemy
from sqlalchemy import create_engine

check = {}

instructions = initialize_VPN(area_input=['Belgium,France,Luxembourg,Switzerland'])

engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')
table_name = "checkdb"

df_matchs = pd.read_sql('Select * From matchsperseason', engine)
df_urls = pd.read_sql('Select * From urlsdb', engine)

try:
    df_urls = df_urls.drop(columns='index')
except:
    pass

for row in df_urls.iterrows():
    index, data = row  
    key = data['Pays']  
    url = data['Urls']
    print(url)
    
    # Search for the country in df_matchs
    matching_row = df_matchs[df_matchs['Pays'] == key]

    if not matching_row.empty:
        number_of_matchs = matching_row.iloc[0]['Matchs']
    else:
        pass
    
    max_matchs = int(number_of_matchs - 3)
    print('Max matchs:', max_matchs)

    finished = True
    while finished: 
        try:
            df1 = pd.read_html(url)
            df = df1[0]
            moy = df['MP'].mean()
            if int(moy) >= 8 and int(moy) < max_matchs:
                print('Nb matchs:', int(moy))
                check[key] = 'ok'
            else:
                check[key] = 'skip'
            print(check[key])
            finished = False    
        except Exception as e:
            print(e)
            rotate_VPN(instructions)

check_data = [{'Pays': key, 'Value': value} for key, value in check.items()]
check = pd.DataFrame(check_data)

check.to_sql(name=table_name, con=engine, if_exists='replace', index=True)

print(check)