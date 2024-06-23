import pandas as pd
import sqlalchemy
from sqlalchemy import create_engine, MetaData
import mysql
from mysql import connector
from nordvpn_switcher.nordvpn_switch import initialize_VPN, rotate_VPN
from Conf import urls_tier2_socc, cols_tier2
import requests
from bs4 import BeautifulSoup
from pymongo.mongo_client import MongoClient

#Set up Mongo Connection
uri = "mongodb+srv://nicolasgilloppe:s0S8eaYt0mIMdYE7@alicedb.eqrplwk.mongodb.net/?retryWrites=true&w=majority&appName=alicedb"
cluster = MongoClient(uri, connectTimeoutMS=30000, socketTimeoutMS=30000)
db= cluster["alicedb"]

# Initialize VPN with specific areas
instructions = initialize_VPN(area_input=['Belgium', 'France', 'Luxembourg', 'Switzerland'])

# Create DB Connection
db_config = {
    'user': 'root',
    'password': 'ImProTiik28',
    'host': 'localhost',
    'database': 'alice'
}
conn = mysql.connector.connect(**db_config)
cursor = conn.cursor()

engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')

query = """
    SELECT * From urlsdb
    """

df_urls = pd.read_sql(query, engine)

query = 'Select * From names'
names = pd.read_sql(query, engine)

big_five = ['Germany', 'England', 'England2', 'Spain', 'France', 'Italy']

col_sf = ['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']
col_sa = ['Squad', 'vs Gls', 'vs Sh', 'vs SoT', 'vs SoT%', 'vs Sh/90', 'vs SoT/90', 'vs G/Sh', 'vs G/SoT', 'vs PK', 'vs PKatt']

#engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/leaguesdb')

leagues = pd.DataFrame()

for row in df_urls.iterrows():
    index, data = row
    url = data['Urls']
    pays = data['Pays']
    print(pays)

    finished = True
    nb_try = 0
    while finished and nb_try <3:
        try:
            if pays in big_five:

                df = pd.read_html(url)

                # Get Shotfor & Shotagainst
                a = len(df)

                columns_shotfor = ['Squad', '# Pl', '90s', 'Gls', 'Sh', 'SoT']

                df_shotfor = None
                df_shotagainst = None
                found_match_for = False
                found_match_against = False

                for i in range(4, a):
                    try:
                        dff = df[i]
                        b = dff.columns.values[0:6]

                        result_list = [item for tpl in b for sub_item in tpl for item in sub_item.split(',')]

                        z = len(result_list)
                        col_list = []

                        for j in range(z):
                            if j % 2 == 0:
                                pass
                            else:
                                col_list.append(result_list[j])

                        if col_list == columns_shotfor:
                            if not found_match_for:
                                df_shotfor = dff
                                found_match_for = True
                            elif not found_match_against:
                                df_shotagainst = dff
                                found_match_against = True

                        if found_match_for and found_match_against:
                            break  # Exit the loop if both matches are found

                    except Exception as e:
                        pass


                # Get df_home & df_away
                df_stats = df[1]
                df_stats.columns = df_stats.columns.droplevel()
                df_team = df[0]

                # Création Home datas
                df_home = df_stats.iloc[:, :11].copy()
                df_home['HW/MP'] = round(df_home['W'] / df_home['MP'], 2)
                df_home['HD/MP'] = round(df_home['D'] / df_home['MP'], 2)
                df_home['HL/MP'] = round(df_home['L'] / df_home['MP'], 2)
                df_home['HGD/MP'] = round(df_home['GD'] / df_home['MP'], 2)

                # Création Away Datas
                df_away = df_stats.iloc[:, [0, 1] + list(range(15, 24))].copy()
                df_away['AW/MP'] = round(df_away['W'] / df_away['MP'], 2)
                df_away['AD/MP'] = round(df_away['D'] / df_away['MP'], 2)
                df_away['AL/MP'] = round(df_away['L'] / df_away['MP'], 2)   
                df_away['AGD/MP'] = round(df_away['GD'] / df_away['MP'], 2)

                # Merge dataframes
                df_pays = df_team[['Squad', 'MP']].merge(df_home[['Squad', 'HW/MP', 'HD/MP', 'HL/MP', 'HGD/MP']], on='Squad')
                df_pays = df_pays.merge(df_away[['Squad', 'AW/MP', 'AD/MP', 'AL/MP', 'AGD/MP']], on='Squad')

                equipes = []

                # Parcourez la colonne 'Squad' et ajoutez chaque équipe à la liste
                for equipe in df_team['Squad']:
                    equipes.append(equipe)

                if df_shotfor is None:
                    df_shotfor = pd.DataFrame(columns=['Squad'])
                    df_shotfor['Squad'] = equipes

                    temp_df = pd.DataFrame(columns=col_sf)
                    temp_df[col_sf] = 0
                    temp_df['Squad'] = equipes

                    df_shotfor = df_shotfor.merge(temp_df, left_on='Squad', right_on='Squad', how='left')
                    shotfor = df_shotfor[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']]

                    df_shotagainst = pd.DataFrame(columns=['Squad'])
                    df_shotagainst['Squad'] = equipes

                    temp_dfa = pd.DataFrame(columns=col_sa)
                    temp_dfa[col_sa] = 0
                    temp_dfa['Squad'] = equipes

                    df_shotagainst = df_shotagainst.merge(temp_dfa, left_on='Squad', right_on='Squad', how='left')
                    shotagainst = df_shotagainst[['Squad', 'vs Gls', 'vs Sh', 'vs SoT', 'vs SoT%', 'vs Sh/90', 'vs SoT/90', 'vs G/Sh', 'vs G/SoT', 'vs PK', 'vs PKatt']]
                else:

                    # Cleaning shotfor & shotagainst
                    df_shotfor.columns = df_shotfor.columns.droplevel()
                    shotfor = df_shotfor[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']]

                    # Diviser les valeurs des colonnes par '90s'
                    columns_to_divide = ['Gls', 'Sh', 'SoT', 'PK', 'PKatt']
                    shotfor[columns_to_divide] = round(shotfor[columns_to_divide].div(shotfor['90s'], axis=0), 2)

                    def remove_first_3_chars(text):
                        return text[3:]

                    df_shotagainst.columns = df_shotagainst.columns.droplevel()
                    df_shotagainst['Squad'] = df_shotagainst['Squad'].apply(lambda x: remove_first_3_chars(x) if isinstance(x, str) else x)
                    shotagainst = df_shotagainst[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']].copy()

                    # Diviser les valeurs des colonnes par '90s'
                    columns_to_divide = ['Gls', 'Sh', 'SoT', 'PK', 'PKatt']
                    shotagainst[columns_to_divide] = round(shotagainst[columns_to_divide].div(shotagainst['90s'], axis=0), 2)

                    shotagainst.rename(columns={'Gls': 'vs Gls', 'Sh': 'vs Sh', 'SoT': 'vs SoT', 'SoT%': 'vs SoT%', 'Sh/90': 'vs Sh/90', 'SoT/90': 'vs SoT/90', 'G/Sh': 'vs G/Sh', 'G/SoT': 'vs G/SoT', 'PK': 'vs PK', 'PKatt': 'vs PKatt'}, inplace=True)
                    shotagainst = shotagainst.drop('90s', axis=1)

                #Scrapping TeamStrengh
                columns_to_keep = ['Squad', 'MP', 'GF', 'GA']
                df_stats = df_stats[columns_to_keep]
                df_stats.columns = ['Squad', 'MPH', 'MPA', 'GFH', 'GFA', 'GAH', 'GAA']
                df_stats = df_stats[['Squad', 'MPH', 'GFH', 'GAH', 'MPA', 'GFA', 'GAA']]

                # Ajout des Averages
                df_stats['HGFPG'] = round(df_stats['GFH'] / df_stats['MPH'], 2)
                df_stats['HGAPG'] = round(df_stats['GAH'] / df_stats['MPH'], 2)
                df_stats['AGFPG'] = round(df_stats['GFA'] / df_stats['MPA'], 2)
                df_stats['AGAPG'] = round(df_stats['GAA'] / df_stats['MPA'], 2)

                moyennes = round(df_stats[['HGFPG', 'HGAPG', 'AGFPG', 'AGAPG']].mean(), 2)

                # Créer un nouveau DataFrame df5 avec les moyennes
                mean = pd.DataFrame(moyennes, columns=['Moyenne'])
                df_pays_avg = mean.transpose().reset_index(drop=True)

                # Calcul Team Strengh
                df_stats['HAS'] = round(df_stats['HGFPG'] / df_pays_avg['HGFPG'][0], 2)
                df_stats['HDS'] = round(df_stats['HGAPG'] / df_pays_avg['HGAPG'][0], 2)
                df_stats['AAS'] = round(df_stats['AGFPG'] / df_pays_avg['AGFPG'][0], 2)
                df_stats['ADS'] = round(df_stats['AGAPG'] / df_pays_avg['AGAPG'][0], 2)

                teamstats = df_stats[['Squad', 'MPH', 'GFH', 'GAH', 'MPA', 'GFA', 'GAA', 'HGFPG', 'HGAPG', 'AGFPG', 'AGAPG', 'HAS', 'HDS', 'AAS', 'ADS']]

                # Merge Dataframes
                df_pays = df_pays.merge(shotfor, left_on='Squad', right_on='Squad', how='left')
                df_pays = df_pays.merge(shotagainst, left_on='Squad', right_on='Squad', how='left')
                df_pays = df_pays.merge(teamstats, left_on='Squad', right_on='Squad', how='left')

                # Fix Columns
                df_pays.drop('90s', axis=1, inplace=True)

                # Parcourir les noms de colonnes et retirer la partie '_x' si présente
                for col in df_pays.columns:
                    df_pays.rename(columns={col: col.replace('_x', '')}, inplace=True)

                df_pays['Pays'] = pays
                df_pays.insert(0, 'Pays', df_pays.pop('Pays'))
                print(df_pays)
                leagues = pd.concat([leagues, df_pays], ignore_index=True)
                print(leagues)

                finished = False

            elif pays == 'Usa':

                df = pd.read_html(url)

                # Get Shotfor & Shotagainst
                a = len(df)

                columns_shotfor = ['Squad', '# Pl', '90s', 'Gls', 'Sh', 'SoT']

                df_shotfor = None
                df_shotagainst = None
                found_match_for = False
                found_match_against = False

                for i in range(4, a):
                    try:
                        dff = df[i]
                        b = dff.columns.values[0:6]

                        result_list = [item for tpl in b for sub_item in tpl for item in sub_item.split(',')]

                        z = len(result_list)
                        col_list = []

                        for j in range(z):
                            if j % 2 == 0:
                                pass
                            else:
                                col_list.append(result_list[j])

                        if col_list == columns_shotfor:
                            if not found_match_for:
                                df_shotfor = dff
                                found_match_for = True
                            elif not found_match_against:
                                df_shotagainst = dff
                                found_match_against = True

                        if found_match_for and found_match_against:
                            break  # Exit the loop if both matches are found

                    except Exception as e:
                        pass

                df0 = df[0]
                df1 = df[1]
                df2 = df[2]
                df3 = df[3]

                # Get df_home & df_away
                df_stats = pd.concat([df1, df3], ignore_index=True)
                df_stats.columns = df_stats.columns.droplevel()

                df_team = pd.concat([df0, df2], ignore_index=True)

                # Création Home datas
                df_home = df_stats.iloc[:, :11].copy()
                df_home['HW/MP'] = round(df_home['W'] / df_home['MP'], 2)
                df_home['HD/MP'] = round(df_home['D'] / df_home['MP'], 2)
                df_home['HL/MP'] = round(df_home['L'] / df_home['MP'], 2)
                df_home['HGD/MP'] = round(df_home['GD'] / df_home['MP'], 2)

                # Création Away Datas
                df_away = df_stats.iloc[:, [0, 1] + list(range(15, 24))].copy()
                df_away['AW/MP'] = round(df_away['W'] / df_away['MP'], 2)
                df_away['AD/MP'] = round(df_away['D'] / df_away['MP'], 2)
                df_away['AL/MP'] = round(df_away['L'] / df_away['MP'], 2)   
                df_away['AGD/MP'] = round(df_away['GD'] / df_away['MP'], 2)

                # Merge dataframes
                df_pays = df_team[['Squad', 'MP']].merge(df_home[['Squad', 'HW/MP', 'HD/MP', 'HL/MP', 'HGD/MP']], on='Squad')
                df_pays = df_pays.merge(df_away[['Squad', 'AW/MP', 'AD/MP', 'AL/MP', 'AGD/MP']], on='Squad')

                equipes = []

                # Parcourez la colonne 'Squad' et ajoutez chaque équipe à la liste
                for equipe in df_team['Squad']:
                    equipes.append(equipe)

                if df_shotfor is None:
                    df_shotfor = pd.DataFrame(columns=['Squad'])
                    df_shotfor['Squad'] = equipes

                    temp_df = pd.DataFrame(columns=col_sf)
                    temp_df[col_sf] = 0
                    temp_df['Squad'] = equipes

                    df_shotfor = df_shotfor.merge(temp_df, left_on='Squad', right_on='Squad', how='left')
                    shotfor = df_shotfor[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']]

                    df_shotagainst = pd.DataFrame(columns=['Squad'])
                    df_shotagainst['Squad'] = equipes

                    temp_dfa = pd.DataFrame(columns=col_sa)
                    temp_dfa[col_sa] = 0
                    temp_dfa['Squad'] = equipes

                    df_shotagainst = df_shotagainst.merge(temp_dfa, left_on='Squad', right_on='Squad', how='left')
                    shotagainst = df_shotagainst[['Squad', 'vs Gls', 'vs Sh', 'vs SoT', 'vs SoT%', 'vs Sh/90', 'vs SoT/90', 'vs G/Sh', 'vs G/SoT', 'vs PK', 'vs PKatt']]
                else:

                    # Cleaning shotfor & shotagainst
                    df_shotfor.columns = df_shotfor.columns.droplevel()
                    shotfor = df_shotfor[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']]

                    # Diviser les valeurs des colonnes par '90s'
                    columns_to_divide = ['Gls', 'Sh', 'SoT', 'PK', 'PKatt']
                    shotfor[columns_to_divide] = round(shotfor[columns_to_divide].div(shotfor['90s'], axis=0), 2)

                    def remove_first_3_chars(text):
                        return text[3:]

                    df_shotagainst.columns = df_shotagainst.columns.droplevel()
                    df_shotagainst['Squad'] = df_shotagainst['Squad'].apply(lambda x: remove_first_3_chars(x) if isinstance(x, str) else x)
                    shotagainst = df_shotagainst[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']].copy()

                    # Diviser les valeurs des colonnes par '90s'
                    columns_to_divide = ['Gls', 'Sh', 'SoT', 'PK', 'PKatt']
                    shotagainst[columns_to_divide] = round(shotagainst[columns_to_divide].div(shotagainst['90s'], axis=0), 2)

                    shotagainst.rename(columns={'Gls': 'vs Gls', 'Sh': 'vs Sh', 'SoT': 'vs SoT', 'SoT%': 'vs SoT%', 'Sh/90': 'vs Sh/90', 'SoT/90': 'vs SoT/90', 'G/Sh': 'vs G/Sh', 'G/SoT': 'vs G/SoT', 'PK': 'vs PK', 'PKatt': 'vs PKatt'}, inplace=True)
                    shotagainst = shotagainst.drop('90s', axis=1)

                #Scrapping TeamStrengh
                columns_to_keep = ['Squad', 'MP', 'GF', 'GA']
                df_stats = df_stats[columns_to_keep]
                df_stats.columns = ['Squad', 'MPH', 'MPA', 'GFH', 'GFA', 'GAH', 'GAA']
                df_stats = df_stats[['Squad', 'MPH', 'GFH', 'GAH', 'MPA', 'GFA', 'GAA']]

                # Ajout des Averages
                df_stats['HGFPG'] = round(df_stats['GFH'] / df_stats['MPH'], 2)
                df_stats['HGAPG'] = round(df_stats['GAH'] / df_stats['MPH'], 2)
                df_stats['AGFPG'] = round(df_stats['GFA'] / df_stats['MPA'], 2)
                df_stats['AGAPG'] = round(df_stats['GAA'] / df_stats['MPA'], 2)

                moyennes = round(df_stats[['HGFPG', 'HGAPG', 'AGFPG', 'AGAPG']].mean(), 2)

                # Créer un nouveau DataFrame df5 avec les moyennes
                mean = pd.DataFrame(moyennes, columns=['Moyenne'])
                df_pays_avg = mean.transpose().reset_index(drop=True)

                # Calcul Team Strengh
                df_stats['HAS'] = round(df_stats['HGFPG'] / df_pays_avg['HGFPG'][0], 2)
                df_stats['HDS'] = round(df_stats['HGAPG'] / df_pays_avg['HGAPG'][0], 2)
                df_stats['AAS'] = round(df_stats['AGFPG'] / df_pays_avg['AGFPG'][0], 2)
                df_stats['ADS'] = round(df_stats['AGAPG'] / df_pays_avg['AGAPG'][0], 2)

                teamstats = df_stats[['Squad', 'MPH', 'GFH', 'GAH', 'MPA', 'GFA', 'GAA', 'HGFPG', 'HGAPG', 'AGFPG', 'AGAPG', 'HAS', 'HDS', 'AAS', 'ADS']]

                # Merge Dataframes
                df_pays = df_pays.merge(shotfor, left_on='Squad', right_on='Squad', how='left')
                df_pays = df_pays.merge(shotagainst, left_on='Squad', right_on='Squad', how='left')
                df_pays = df_pays.merge(teamstats, left_on='Squad', right_on='Squad', how='left')

                # Fix Columns
                df_pays.drop('90s', axis=1, inplace=True)

                # Parcourir les noms de colonnes et retirer la partie '_x' si présente
                for col in df_pays.columns:
                    df_pays.rename(columns={col: col.replace('_x', '')}, inplace=True)

                df_pays['Pays'] = pays
                df_pays.insert(0, 'Pays', df_pays.pop('Pays'))
                print(df_pays)
                leagues = pd.concat([leagues, df_pays], ignore_index=True)

                finished = False

            else:
                df = pd.read_html(url)

                # Get Shotfor & Shotagainst
                a = len(df)
                columns_shotfor = ['Squad', '# Pl', '90s', 'Gls', 'Sh', 'SoT']
                columns_df_stats = ['Rk', 'Squad', 'MP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts', 'Pts/MP', 'W', 'D', 'L', 'GF', 'GA', 'GD', 'Pts', 'Pts/MP']

                df_shotfor = None
                df_shotagainst = None
                found_match_for = False
                found_match_against = False
                df_stats = None

                for i in range(a):
                    try:
                        dff = df[i]
                        b = dff.columns.values[0:6]

                        result_list = [item for tpl in b for sub_item in tpl for item in sub_item.split(',')]

                        z = len(result_list)
                        col_list = []

                        for j in range(z):
                            if j % 2 == 0:
                                pass
                            else:
                                col_list.append(result_list[j])

                        if col_list == columns_shotfor:
                            if not found_match_for:
                                df_shotfor = dff
                                found_match_for = True
                            elif not found_match_against:
                                df_shotagainst = dff
                                found_match_against = True

                        if found_match_for and found_match_against:
                            break

                    except Exception as e:
                        pass

                for i in range(4):
                    dff = df[i]

                    try: 
                        dff.columns = dff.columns.droplevel()
                        df_stats = dff
                        break

                    except Exception as e:
                        pass

                # Get df_home & df_away
                df_team = df[0]

                # Création Home datas
                df_home = df_stats.iloc[:, :11].copy()
                df_home['HW/MP'] = round(df_home['W'] / df_home['MP'], 2)
                df_home['HD/MP'] = round(df_home['D'] / df_home['MP'], 2)
                df_home['HL/MP'] = round(df_home['L'] / df_home['MP'], 2)
                df_home['HGD/MP'] = round(df_home['GD'] / df_home['MP'], 2)

                # Création Away Datas
                df_away = df_stats.iloc[:, :2].copy()
                df_away = pd.concat([df_away, df_stats.iloc[:, 11:]], axis=1)
                df_away['AW/MP'] = round(df_away['W'] / df_away['MP'], 2)
                df_away['AD/MP'] = round(df_away['D'] / df_away['MP'], 2)
                df_away['AL/MP'] = round(df_away['L'] / df_away['MP'], 2)   
                df_away['AGD/MP'] = round(df_away['GD'] / df_away['MP'], 2)

                # Merge dataframes
                df_pays = df_team[['Squad', 'MP']].merge(df_home[['Squad', 'HW/MP', 'HD/MP', 'HL/MP', 'HGD/MP']], on='Squad')
                df_pays = df_pays.merge(df_away[['Squad', 'AW/MP', 'AD/MP', 'AL/MP', 'AGD/MP']], on='Squad')

                equipes = []

                # Parcourez la colonne 'Squad' et ajoutez chaque équipe à la liste
                for equipe in df_team['Squad']:
                    equipes.append(equipe)

                if df_shotfor is None:
                    df_shotfor = pd.DataFrame(columns=['Squad'])
                    df_shotfor['Squad'] = equipes

                    temp_df = pd.DataFrame(columns=col_sf)
                    temp_df[col_sf] = 0
                    temp_df['Squad'] = equipes

                    df_shotfor = df_shotfor.merge(temp_df, left_on='Squad', right_on='Squad', how='left')
                    shotfor = df_shotfor[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']]

                    df_shotagainst = pd.DataFrame(columns=['Squad'])
                    df_shotagainst['Squad'] = equipes

                    temp_dfa = pd.DataFrame(columns=col_sa)
                    temp_dfa[col_sa] = 0
                    temp_dfa['Squad'] = equipes

                    df_shotagainst = df_shotagainst.merge(temp_dfa, left_on='Squad', right_on='Squad', how='left')
                    shotagainst = df_shotagainst[['Squad', 'vs Gls', 'vs Sh', 'vs SoT', 'vs SoT%', 'vs Sh/90', 'vs SoT/90', 'vs G/Sh', 'vs G/SoT', 'vs PK', 'vs PKatt']]
                else:

                    # Cleaning shotfor & shotagainst
                    df_shotfor.columns = df_shotfor.columns.droplevel()
                    shotfor = df_shotfor[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']]

                    # Diviser les valeurs des colonnes par '90s'
                    columns_to_divide = ['Gls', 'Sh', 'SoT', 'PK', 'PKatt']
                    shotfor[columns_to_divide] = round(shotfor[columns_to_divide].div(shotfor['90s'], axis=0), 2)

                    def remove_first_3_chars(text):
                        return text[3:]

                    df_shotagainst.columns = df_shotagainst.columns.droplevel()
                    df_shotagainst['Squad'] = df_shotagainst['Squad'].apply(lambda x: remove_first_3_chars(x) if isinstance(x, str) else x)
                    shotagainst = df_shotagainst[['Squad', '90s', 'Gls', 'Sh', 'SoT', 'SoT%', 'Sh/90', 'SoT/90', 'G/Sh', 'G/SoT', 'PK', 'PKatt']].copy()

                    # Diviser les valeurs des colonnes par '90s'
                    columns_to_divide = ['Gls', 'Sh', 'SoT', 'PK', 'PKatt']
                    shotagainst[columns_to_divide] = round(shotagainst[columns_to_divide].div(shotagainst['90s'], axis=0), 2)

                    shotagainst.rename(columns={'Gls': 'vs Gls', 'Sh': 'vs Sh', 'SoT': 'vs SoT', 'SoT%': 'vs SoT%', 'Sh/90': 'vs Sh/90', 'SoT/90': 'vs SoT/90', 'G/Sh': 'vs G/Sh', 'G/SoT': 'vs G/SoT', 'PK': 'vs PK', 'PKatt': 'vs PKatt'}, inplace=True)
                    shotagainst = shotagainst.drop('90s', axis=1)

                #Scrapping TeamStrengh
                columns_to_keep = ['Squad', 'MP', 'GF', 'GA']
                df_stats = df_stats[columns_to_keep]
                df_stats.columns = ['Squad', 'MPH', 'MPA', 'GFH', 'GFA', 'GAH', 'GAA']
                df_stats = df_stats[['Squad', 'MPH', 'GFH', 'GAH', 'MPA', 'GFA', 'GAA']]

                # Ajout des Averages
                df_stats['HGFPG'] = round(df_stats['GFH'] / df_stats['MPH'], 2)
                df_stats['HGAPG'] = round(df_stats['GAH'] / df_stats['MPH'], 2)
                df_stats['AGFPG'] = round(df_stats['GFA'] / df_stats['MPA'], 2)
                df_stats['AGAPG'] = round(df_stats['GAA'] / df_stats['MPA'], 2)

                moyennes = round(df_stats[['HGFPG', 'HGAPG', 'AGFPG', 'AGAPG']].mean(), 2)

                # Créer un nouveau DataFrame df5 avec les moyennes
                mean = pd.DataFrame(moyennes, columns=['Moyenne'])
                df_pays_avg = mean.transpose().reset_index(drop=True)

                # Calcul Team Strengh
                df_stats['HAS'] = round(df_stats['HGFPG'] / df_pays_avg['HGFPG'][0], 2)
                df_stats['HDS'] = round(df_stats['HGAPG'] / df_pays_avg['HGAPG'][0], 2)
                df_stats['AAS'] = round(df_stats['AGFPG'] / df_pays_avg['AGFPG'][0], 2)
                df_stats['ADS'] = round(df_stats['AGAPG'] / df_pays_avg['AGAPG'][0], 2)

                teamstats = df_stats[['Squad', 'MPH', 'GFH', 'GAH', 'MPA', 'GFA', 'GAA', 'HGFPG', 'HGAPG', 'AGFPG', 'AGAPG', 'HAS', 'HDS', 'AAS', 'ADS']]

                # Merge Dataframes
                df_pays = df_pays.merge(shotfor, left_on='Squad', right_on='Squad', how='left')
                df_pays = df_pays.merge(shotagainst, left_on='Squad', right_on='Squad', how='left')
                df_pays = df_pays.merge(teamstats, left_on='Squad', right_on='Squad', how='left')

                # Fix Columns
                df_pays.drop('90s', axis=1, inplace=True)

                # Parcourir les noms de colonnes et retirer la partie '_x' si présente
                for col in df_pays.columns:
                    df_pays.rename(columns={col: col.replace('_x', '')}, inplace=True)


                df_pays['Pays'] = pays
                df_pays.insert(0, 'Pays', df_pays.pop('Pays'))
                print(df_pays)
                leagues = pd.concat([leagues, df_pays], ignore_index=True)
                print(leagues)

                finished = False

        except Exception as e:
            print(e)
            if nb_try <3:
                nb_try += 1
                rotate_VPN(instructions)
            else:
                try:
                    query_l = 'Select * from leaguedb'
                    mom = pd.read_sql(query_l, engine)
                    mom = mom[mom['Pays'] == pays]
                    leagues = pd.concat([leagues, mom], ignore_index=True)
                    finished = False
                except:
                    finished = False


for index, row in leagues.iterrows():
    squad = row['Squad']
    pays = row['Pays']
    try:
        corres = names[(names['fbref'] == squad) & (names['champ'] == pays)]
        flash = corres['flashscore'].values[0]
        leagues.at[index, 'Squad'] = flash
    except:
        pass

engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')
leagues.to_sql('leaguesdb', engine, if_exists='replace', index=False)
collection = db['leaguesdb']
data = leagues.to_dict(orient="records")
collection.delete_many({})
collection.insert_many(data)


def scrapping_socc_tier2(key, url):
    response = requests.get(url)
    soup = BeautifulSoup(response.content, 'html.parser')

    df_home = pd.read_html(str(soup.find('div', id='h2h-team1')))[0]
    df_away = pd.read_html(str(soup.find('div', id='h2h-team2')))[0]

    df_home.columns = ['Index', 'Squad', 'MPH', 'WH', 'DH', 'LH', 'GFH', 'GAH', 'GDH', 'PtsH']
    df_away.columns = ['Index', 'Squad', 'MPA', 'WA', 'DA', 'LA', 'GFA', 'GAA', 'GDA', 'PtsA']

    df_home = df_home.drop(['Index', 'PtsH'], axis=1)
    df_away = df_away.drop(['Index', 'PtsA'], axis=1)
    df = pd.merge(df_home, df_away, on='Squad', how='inner').dropna()

    for index, row in df.iterrows():
        df.at[index, 'Pays'] = key
        df.at[index, 'MP'] = float(row['MPH']) + float(row['MPA'])
        df.at[index, 'HW/MP'] = round(float(row['WH']) / float(row['MPH']), 2)
        df.at[index, 'HD/MP'] = round(float(row['DH']) / float(row['MPH']), 2)
        df.at[index, 'HL/MP'] = round(float(row['LH']) / float(row['MPH']), 2)
        df.at[index, 'HGD/MP'] = round(float(row['GDH']) / float(row['MPH']), 2)
        df.at[index, 'AW/MP'] = round(float(row['WA']) / float(row['MPA']), 2)
        df.at[index, 'AD/MP'] = round(float(row['DA']) / float(row['MPA']), 2)
        df.at[index, 'AL/MP'] = round(float(row['LA']) / float(row['MPA']), 2)
        df.at[index, 'AGD/MP'] = round(float(row['GDA']) / float(row['MPA']), 2)
        df.at[index, 'GF'] = round(float(row['GFH']) + float(row['GFA']), 2)
        df.at[index, 'GA'] = round(float(row['GAH']) + float(row['GAA']), 2)
        df.at[index, 'HGFPG'] = round(float(row['GFH']) / float(row['MPH']), 2)
        df.at[index, 'HGAPG'] = round(float(row['GAH']) / float(row['MPH']), 2)
        df.at[index, 'AGFPG'] = round(float(row['GFA']) / float(row['MPA']), 2)
        df.at[index, 'AGAPG'] = round(float(row['GAA']) / float(row['MPA']), 2)

    df['HGFPG'] = df['HGFPG'].astype(float)
    df['HGAPG'] = df['HGAPG'].astype(float)
    df['AGFPG'] = df['AGFPG'].astype(float)
    df['AGAPG'] = df['AGAPG'].astype(float)
    gfhm = round(df['HGFPG'].mean(), 2)
    gahm = round(df['HGAPG'].mean(), 2)
    gfam = round(df['AGFPG'].mean(), 2)
    gaam = round(df['AGAPG'].mean(), 2)

    for index, row in df.iterrows():
        df.at[index, 'HAS'] = round(float(row['HGFPG']) / gfhm, 2)
        df.at[index, 'HDS'] = round(float(row['HGAPG']) / gahm, 2)
        df.at[index, 'AAS'] = round(float(row['AGFPG']) / gfam, 2)
        df.at[index, 'ADS'] = round(float(row['AGAPG']) / gaam, 2)

    df = df[cols_tier2]
    return df

tier2_league = pd.DataFrame(columns=cols_tier2)
for key, url in urls_tier2_socc.items():
    finished = False
    while not finished:
        try:
            tier2_league = pd.concat([tier2_league, scrapping_socc_tier2(key, url)], ignore_index=True)
            print(tier2_league)
            finished = True
        except:
            rotate_VPN(instructions)

for index, row in tier2_league.iterrows():
    squad = row['Squad']
    pays = row['Pays']

    try:
        corres = names[(names['soccerstats'] == squad) & (names['champ'] == pays)]
        flash = corres['flashscore'].values[0]
        tier2_league.at[index, 'Squad'] = flash
    except:
        pass

tier2_league.to_sql('leaguesdb2', engine, if_exists='replace', index=False)
collection = db['leaguesdb2']
data2 = tier2_league.to_dict(orient="records")
collection.delete_many({})
collection.insert_many(data2)

