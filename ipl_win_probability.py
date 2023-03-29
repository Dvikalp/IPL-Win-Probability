"""IPL Win Probability.ipynb

Automatically generated by Colaboratory.

"""

import pandas as pd
import numpy as np

match=pd.read_csv('matches.csv')
delivery=pd.read_csv('deliveries.csv')

match.head()

delivery.head()

total_score_df= delivery.groupby(['match_id','inning']).sum()['total_runs'].reset_index()
total_score_df=total_score_df[total_score_df['inning']==1]
total_score_df

match_df= match.merge(total_score_df[['match_id','total_runs']],left_on='id',right_on='match_id',)
match_df

match_df['team1'].unique()

teams=[
    'Sunrisers Hyderabad', 'Mumbai Indians', 'Royal Challengers Bangalore',
       'Kolkata Knight Riders', 'Kings XI Punjab',
       'Chennai Super Kings', 'Rajasthan Royals',
       'Delhi Capitals'
]
match_df['team1']=match_df['team1'].str.replace('Delhi Daredevils','Delhi Capitals')
match_df['team2']=match_df['team2'].str.replace('Delhi Daredevils','Delhi Capitals')

match_df['team1']=match_df['team1'].str.replace('Deccan Chargers','Sunrisers Hyderabad')
match_df['team2']=match_df['team2'].str.replace('Deccan Chargers','Sunrisers Hyderabad')

match_df= match_df[match_df['team1'].isin(teams)]
match_df= match_df[match_df['team2'].isin(teams)]

match_df= match_df[match_df['dl_applied']==0]
match_df= match_df[['match_id','city','winner','total_runs']]

delivery_df= match_df.merge(delivery,on='match_id')
delivery_df= delivery_df[delivery_df['inning']==2]

delivery_df

delivery_df['current_score']= delivery_df.groupby('match_id').cumsum()['total_runs_y']
delivery_df['runs_left']= delivery_df['total_runs_x']-delivery_df['current_score']

delivery_df['balls_left']= 126-(delivery_df['over']*6 + delivery_df['ball'])

delivery_df['player_dismissed'] = delivery_df['player_dismissed'].fillna("0")
delivery_df['player_dismissed'] = delivery_df['player_dismissed'].apply(lambda x:x if x == "0" else "1")
delivery_df['player_dismissed'] = delivery_df['player_dismissed'].astype('int')
wickets = delivery_df.groupby('match_id').cumsum()['player_dismissed'].values
delivery_df['wickets'] = 10 - wickets

delivery_df

delivery_df['current_rr']= (6*delivery_df['current_score'])/(120-delivery_df['balls_left'])

delivery_df['req_rr']=(6*delivery_df['runs_left'])/delivery_df['balls_left']
delivery_df

def result(row):
  return 1 if row['batting_team']==row['winner'] else 0

delivery_df['result']=delivery_df.apply(result,axis=1)

final_df= delivery_df[['batting_team','bowling_team','city','runs_left','balls_left','wickets','total_runs_x','current_rr','req_rr','result']]
final_df.dropna(inplace=True)
final_df=final_df[final_df['balls_left']!=0]

final_df

X=final_df.iloc[:,:-1]
y=final_df.iloc[:,-1]
from sklearn.model_selection import train_test_split

X_train,X_test,y_train,y_test= train_test_split(X,y,test_size=0.2,random_state=1)

X_train

from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder

trf = ColumnTransformer([
    ('trf',OneHotEncoder(sparse=False,drop='first'),['batting_team','bowling_team','city'])
],
remainder='passthrough')

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.pipeline import Pipeline

pipe=Pipeline(
    steps=[
        ('step1',trf),
        ('step2',LogisticRegression(solver='liblinear'))
    ]
)

import warnings
with warnings.catch_warnings():
    warnings.simplefilter(action='ignore', category=FutureWarning)
    pipe.fit(X_train,y_train)

y_pred= pipe.predict(X_test)

from sklearn.metrics import accuracy_score
accuracy_score(y_test,y_pred)

pipe.predict_proba(X_test)[10]

def match_progression(x_df,match_id,pipe):
    match = x_df[x_df['match_id'] == match_id]
    match = match[(match['ball'] == 6)]
    temp_df = match[['batting_team','bowling_team','city','runs_left','balls_left','wickets','total_runs_x','current_rr','req_rr']].dropna()
    temp_df = temp_df[temp_df['balls_left'] != 0]
    result = pipe.predict_proba(temp_df)
    temp_df['lose'] = np.round(result.T[0]*100,1)
    temp_df['win'] = np.round(result.T[1]*100,1)
    temp_df['end_of_over'] = range(1,temp_df.shape[0]+1)
    
    target = temp_df['total_runs_x'].values[0]
    runs = list(temp_df['runs_left'].values)
    new_runs = runs[:]
    runs.insert(0,target)
    temp_df['runs_after_over'] = np.array(runs)[:-1] - np.array(new_runs)
    wickets = list(temp_df['wickets'].values)
    new_wickets = wickets[:]
    new_wickets.insert(0,10)
    wickets.append(0)
    w = np.array(wickets)
    nw = np.array(new_wickets)
    temp_df['wickets_in_over'] = (nw - w)[0:temp_df.shape[0]]
    
    print("Target-",target)
    temp_df = temp_df[['end_of_over','runs_after_over','wickets_in_over','lose','win']]
    return temp_df,target

temp_df,target=match_progression(delivery_df,74,pipe)
temp_df

import matplotlib.pyplot as plt
plt.figure(figsize=(18,8))
plt.plot(temp_df['end_of_over'],temp_df['wickets_in_over'],color='yellow',linewidth=3)
plt.plot(temp_df['end_of_over'],temp_df['win'],color='#00a65a',linewidth=4)
plt.plot(temp_df['end_of_over'],temp_df['lose'],color='red',linewidth=4)
plt.bar(temp_df['end_of_over'],temp_df['runs_after_over'])
plt.title('Target-' + str(target))

batting_team= input("Enter batting team :")
bowling_team= input("Enter bowling team :")
city= input("Enter city:")
run_left= int(input("Enter runs left :"))
balls_left= int(input("Enter balls left :"))
wickets= int(input("Enter wickets left :"))
total_runs= int(input("Enter total runs :"))
current_rr= 6*(total_runs-run_left)/(120-balls_left)
req_rr= 6*(run_left)/balls_left

input_df=pd.DataFrame({
    'batting_team':[batting_team],
    'bowling_team':[bowling_team],
    'city':[city],
    'runs_left':[run_left],
    'balls_left':[balls_left],
    'wickets':[wickets],
    'total_runs_x':[total_runs],
    'current_rr':[current_rr],
    'req_rr':[req_rr],
})

pipe.predict_proba(input_df)