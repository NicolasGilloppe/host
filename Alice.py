from sqlalchemy import create_engine
import pandas as pd
import datetime
from sklearn.linear_model import PoissonRegressor
from sklearn.svm import SVR
from scipy.stats import poisson
from pymongo.mongo_client import MongoClient
import numpy as np


#Set up Mongo Connection
uri = "mongodb+srv://nicolasgilloppe:s0S8eaYt0mIMdYE7@alicedb.eqrplwk.mongodb.net/?retryWrites=true&w=majority&appName=alicedb"
cluster = MongoClient(uri, connectTimeoutMS=30000, socketTimeoutMS=30000)
db= cluster["alicedb"]
collection = db['Alicetest']

#Get Today's Date
today = datetime.datetime.now().date()
today = today.strftime('%d-%m-%y')

engine = create_engine('mysql+mysqlconnector://root:ImProTiik28@localhost/alice')

query_check = """
    SELECT * From checkdb
    """
check = pd.read_sql(query_check, engine)

def poisson_probability(lambda_, k):
    """Calculate Poisson probability for given lambda and k."""
    return poisson.pmf(k, lambda_)

def home_team_wins_probability(home_lambda, away_lambda):
    """Calculate the probability of the home team scoring more goals than the away team."""
    prob = 0
    for home_goals in range(0, 10):
        for away_goals in range(0, home_goals):
            prob += poisson_probability(home_lambda, home_goals) * poisson_probability(away_lambda, away_goals)
    return prob

def draw_probability(home_lambda, away_lambda):
    """Calculate the probability of a draw."""
    prob = 0
    for goals in range(0, 10):  # Assuming max 9 goals
        prob += poisson_probability(home_lambda, goals) * poisson_probability(away_lambda, goals)
    return prob

def away_team_wins_probability(home_lambda, away_lambda):
    """Calculate the probability of the away team winning."""
    prob = 0
    for away_goals in range(0, 10):  # Assuming max 9 goals
        for home_goals in range(0, away_goals):  # Home goals must be less than away goals
            prob += poisson_probability(home_lambda, home_goals) * poisson_probability(away_lambda, away_goals)
    return prob

def more_than_2_goals_probability(home_lambda, away_lambda):
    """Calculate the probability of more than 2 total goals in the game."""
    prob = 0
    for home_goals in range(0, 10):  # Assuming max 9 goals
        for away_goals in range(0, 10):  # Assuming max 9 goals
            if home_goals + away_goals > 2:
                prob += poisson_probability(home_lambda, home_goals) * poisson_probability(away_lambda, away_goals)
    return prob

def more_than_3_goals_probability(home_lambda, away_lambda):
    """Calculate the probability of more than 3 total goals in the game."""
    prob = 0
    for home_goals in range(0, 10):  # Assuming max 9 goals
        for away_goals in range(0, 10):  # Assuming max 9 goals
            if home_goals + away_goals > 3:
                prob += poisson_probability(home_lambda, home_goals) * poisson_probability(away_lambda, away_goals)
    return prob

def both_teams_score_probability(home_lambda, away_lambda):
    """Calculate the probability of both teams scoring in the game."""
    prob = 0
    for home_goals in range(1, 10):  # Assuming max 9 goals
        for away_goals in range(1, 10):  # Assuming max 9 goals
            prob += poisson_probability(home_lambda, home_goals) * poisson_probability(away_lambda, away_goals)
    return prob


def alice(train_df, predict_df):
    # Initialize models
    model_h_svr = SVR()
    model_a_svr = SVR()
    model_h_poiss = PoissonRegressor()
    model_a_poiss = PoissonRegressor()

    train_df = train_df.dropna()
    predict_df = predict_df.dropna()
    try:
        X_train = train_df.drop(['Result', 'Over1', 'Over2', 'Ho15', 'BTTS', 'Home', 'Away', 'Pays', 'Champ', 'Time', 'Date', 'GoalA', 'GoalH'], axis=1)
    except:
        X_train = train_df.drop(['Date', 'Time', 'Champ', 'Home', 'Away', 'Pays', 'GoalH', 'GoalA'], axis=1)

    y_train_h = train_df['GoalH']
    y_train_a = train_df['GoalA']

    model_h_svr.fit(X_train, y_train_h)
    model_a_svr.fit(X_train, y_train_a)
    model_h_poiss.fit(X_train, y_train_h)
    model_a_poiss.fit(X_train, y_train_a)

    try:
        X_predict = predict_df.drop(['Home', 'Away', 'Pays', 'Champ', 'Date', 'Time', 'BTTS', 'GoalH', 'GoalA', 'Over1', 'Over2', 'Result', 'Ho15'], axis=1)
    except:
        X_predict = predict_df.drop(['Home', 'Away', 'Pays', 'Champ', 'Date', 'Time'], axis=1)

    predictions_h_svr = model_h_svr.predict(X_predict)
    predictions_a_svr = model_a_svr.predict(X_predict)
    predictions_h_svr = np.where(predictions_h_svr < 0, 0, predictions_h_svr)
    predictions_a_svr = np.where(predictions_a_svr < 0, 0, predictions_a_svr)

    predictions_h_poiss = model_h_poiss.predict(X_predict)
    predictions_a_poiss = model_a_poiss.predict(X_predict)
    predictions_h_poiss = np.where(predictions_h_poiss < 0, 0, predictions_h_poiss)
    predictions_a_poiss = np.where(predictions_a_poiss < 0, 0, predictions_a_poiss)

    predict_df['eGoalH'] = predictions_h_svr
    predict_df['eGoalA'] = predictions_a_svr

    predict_df['eGoalH_Poiss'] = predictions_h_poiss
    predict_df['eGoalA_Poiss'] = predictions_a_poiss

    for index, row in predict_df.iterrows():
        predict_df.at[index, 'Proba_H'] = home_team_wins_probability(row['eGoalH'], row['eGoalA'])
        predict_df.at[index, 'Proba_D'] = draw_probability(row['eGoalH'], row['eGoalA'])
        predict_df.at[index, 'Proba_A'] = away_team_wins_probability(row['eGoalH'], row['eGoalA'])

        predict_df.at[index, 'Proba_O1'] = more_than_2_goals_probability(row['eGoalH'], row['eGoalA'])
        predict_df.at[index, 'Proba_U1'] = 1 - more_than_2_goals_probability(row['eGoalH_Poiss'], row['eGoalA_Poiss'])

        predict_df.at[index, 'Proba_O2'] = more_than_3_goals_probability(row['eGoalH'], row['eGoalA'])
        predict_df.at[index, 'Proba_U2'] = 1 - more_than_3_goals_probability(row['eGoalH'], row['eGoalA'])

        predict_df.at[index, 'Proba_BTTS'] = both_teams_score_probability(row['eGoalH'], row['eGoalA'])
        predict_df.at[index, 'Proba_NoBTTS'] = 1 - both_teams_score_probability(row['eGoalH'], row['eGoalA'])

        predict_df.at[index, 'Total'] = row['eGoalH'] + row['eGoalA']

        predict_df.at[index, 'Proba_HD'] = home_team_wins_probability(row['eGoalH'], row['eGoalA']) + draw_probability(row['eGoalH'], row['eGoalA'])
        predict_df.at[index, 'Proba_DA'] = draw_probability(row['eGoalH'], row['eGoalA']) + away_team_wins_probability(row['eGoalH'], row['eGoalA'])

    return predict_df[['Date', 'Time', 'Champ', 'Home', 'Away', 'Pays', 'eGoalH', 'eGoalA', 'Proba_H', 'Proba_D', 'Proba_A', 'Proba_HD', 'Proba_DA', 'Proba_O1', 'Proba_U1', 'Proba_O2', 'Proba_U2', 'Proba_BTTS', 'Proba_NoBTTS', 'Total']]

bets = pd.DataFrame(columns=['Date', 'Time', 'Champ', 'Home', 'Away', 'Pays', 'Bets'])
proba = pd.DataFrame(columns=['Date', 'Time', 'Champ', 'Home', 'Away', 'Pays', 'eGoalH', 'eGoalA', 'Proba_H', 'Proba_D', 'Proba_A', 'Proba_HD', 'Proba_DA', 'Proba_O1', 'Proba_U1', 'Proba_O2', 'Proba_U2', 'Proba_BTTS', 'Proba_NoBTTS', 'Total'])

for i in ['1', '2']:
    train = pd.read_sql('Select * From alicedb', engine).dropna()
    predict = pd.read_sql(f'Select * From matchs{i}', engine)
    if i == '2':
        train = train[list(predict.columns) + ['GoalH', 'GoalA']]
    print(predict)

    # Fix Columns
    try: 
        train = train.drop(['Index'], axis=1)
        predict = predict.drop(['Index'], axis=1)
    except Exception as e:
        pass

    predicted = alice(train, predict)
    print(predicted)

    proba = pd.concat([proba, predicted])

    #Fix Check First
    """ for index, row in predicted.iterrows():
        pays = row['Pays']
        value = check[check['Pays'] == pays]['Value'].values            
        if value == 'skip':
            predicted.drop(index, inplace=True) """

    for index, row in predicted.iterrows():
        datas = [row['Date'], row['Time'], row['Champ'], row['Home'], row['Away'], row['Pays']]
        for bet in ['H', 'D', 'A', 'O1']:
            if row[f'Proba_{bet}'] >= 0.6:
                datas_result = datas.copy()
                datas_result.append(f'{bet}')
                bets.loc[len(bets)] = datas_result
                print(datas_result)

        if row['Proba_U1'] >= 0.7:
            datas_u1 = datas.copy()
            datas_u1.append('U1')
            bets.loc[len(bets)] = datas_u1
            print(datas_u1)

        if row['Total'] >= 2.9:
            datas_o2 = datas.copy()
            datas_o2.append('O2')
            bets.loc[len(bets)] = datas_o2
            print(datas_o2)

        if row['Total'] < 1.8:
            datas_u2 = datas.copy()
            datas_u2.append('U2')
            bets.loc[len(bets)] = datas_u2
            print(datas_u2)

        if row['eGoalH'] > 1.2 and row['eGoalA'] > 1.2:
            datas_btts = datas.copy()
            datas_btts.append('BTTS')
            bets.loc[len(bets)] = datas_btts
            print(datas_btts)

        if row['eGoalH'] < 0.9 and row['eGoalA'] < 0.9:
            datas_nobtts = datas.copy()
            datas_nobtts.append('NoBTTS')
            bets.loc[len(bets)] = datas_nobtts
            print(datas_nobtts)

        if row['Proba_HD'] >= 0.8:
            datas_hd = datas.copy()
            datas_hd.append('HD')
            bets.loc[len(bets)] = datas_hd
            print(datas_hd)

        if row['Proba_DA'] >= 0.8:
            datas_da = datas.copy()
            datas_da.append('DA')
            bets.loc[len(bets)] = datas_da
            print(datas_da)

        for _ in ['H', 'A']:
            if row[f'Proba_{_}'] >= 0.6 and row['Total'] >= 2.5:
                datas_h2 = datas.copy()
                datas_h2.append(f'{_}o15')
                bets.loc[len(bets)] = datas_h2
                print(datas_h2)

    print(bets)

collection = db['Proba']
collection.delete_many({})
collection.insert_many(proba.to_dict(orient="records"))

collection = db['betsdb']
collection.insert_many(bets.to_dict(orient="records"))

proba.to_sql('proba', engine, if_exists='replace', index=False)
bets.to_sql('betsdb', engine, if_exists='append', index=False)

print('Proba')
print(proba)
print('Bets')
print(bets)

#Fix Check First
""" wrp = pd.read_sql('Select * from wr_pays', engine)
wrb = pd.read_sql('Select * From wr_bets', engine)

pays_list = wrp[(wrp['Pick'] == 1) | (wrp['Pick'] == 0.5)]['Pays'].unique().tolist()
bets_list = wrb[(wrb['Pick'] == 1) | (wrb['Pick'] == 0.5)]['Bets'].unique().tolist()

bets = bets[bets['Pays'].isin(pays_list)]
bets = bets[bets['Bets'].isin(bets_list)]

bets.to_sql('predicted', engine, if_exists='replace', index=False) """

    