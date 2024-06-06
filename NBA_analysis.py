# Shlok Yeolekar
# NBA Analysis Through The Seasons
# Completed: June 2, 2024

import pandas as pd
import requests
pd.set_option('display.max_columns', None)
import time
import numpy as np
import openpyxl
import plotly.express as px
import plotly.graph_objects as go
import warnings
import os

###################################*** SCRAPER ***###########################################

def get_years():
    # Prompt the user
    print("\nEnter the range of years you would like to analyze. \n(Max range: 1951-52 to 2023-24 Seasons)\n")
    start_year = int(input("Enter the season start year (e.g., 2012 --> 2012-13 Season): "))
    end_year = int(input("Enter the season end year(e.g., 2022 --> 2022-2023 Season): "))
    print("\n")

    # Generate the list of years in the desired format
    years = []
    for year in range(start_year, end_year + 1):
        next_year_short = str(year + 1)[-2:]  # Get the last two digits of the next year
        year_str = f"{year}-{next_year_short}"
        years.append(year_str)

    return years

test_url = 'https://stats.nba.com/stats/leagueLeaders?LeagueID=00&PerMode=Totals&Scope=S&Season=2012-13&SeasonType=Regular%20Season&StatCategory=PTS'
r = requests.get(url=test_url).json()
table_headers = r['resultSet']['headers']
df_cols = ['Year', 'Season'] + table_headers
warnings.simplefilter(action='ignore', category=FutureWarning)

headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br, zstd',
    'Accept-Language': 'en-US,en;q=0.9',
    'Connection': 'keep-alive',
    'Host': 'stats.nba.com',
    'Origin': 'https://www.nba.com',
    'Referer': 'https://www.nba.com/',
    'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    'Sec-Ch-Ua-Mobile': '?0',
    'Sec-Ch-Ua-Platform': "macOS",
    'Sec-Fetch-Dest': 'empty',
    'Sec-Fetch-Mode': 'cors',
    'Sec-Fetch-Site': 'same-site',
    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36'
}

df = pd.DataFrame(columns=df_cols)
season_types = ['Regular%20Season', 'Playoffs']
years = get_years()
print(f'Scraping data from the {years[0]} to the {years[-1]} season...')
time.sleep(2)

begin_loop = time.time()

for y in years:
    for s in season_types:
        api_url = 'https://stats.nba.com/stats/leagueLeaders?LeagueID=00&PerMode=Totals&Scope=S&Season=' + y + '&SeasonType=' + s + '&StatCategory=PTS'
        r = requests.get(url=api_url).json()

        temp_df1 = pd.DataFrame(r['resultSet']['rowSet'], columns=table_headers)
        temp_df2 = pd.DataFrame({'Year': [y for i in range(len(temp_df1))],
                                 'Season': [s for i in range(len(temp_df1))]})
        temp_df3 = pd.concat([temp_df2, temp_df1], axis=1)
        df = pd.concat([df, temp_df3], axis=0)

        lag = np.random.uniform(low=0.1, high=1.5)
        time.sleep(lag)
    print(f'Finished scraping data for {y}.')

print(f'Process completed. Total runtime: {round((time.time() - begin_loop) / 60, 2)} minutes.')
df.to_excel('nba_player_data.xlsx', index=False)
del temp_df1, temp_df2, temp_df3

###################################*** ANALYSIS ***###########################################

pd.set_option('display.max_columns', None)

# Read file with scraped data
data = pd.read_excel('nba_player_data.xlsx')

##### Data Cleaning #####
data.drop(columns=['RANK', 'EFF', 'TEAM_ID'], inplace=True)  # drop unnecessary columns
data['season_start_year'] = data['Year'].str[:4].astype(int)  # replace str years w ints
data['TEAM'] = data['TEAM'].replace(to_replace=['NOP', 'NOH'], value='NOP')     # replace NOLA Hornets w Pelicans
data['Season'] = data['Season'].replace('Regular%20Season', 'RS')               # change 'Regular Season' source text

# Playoff  and regular season dataframes
rs_df = data[data['Season'] == 'RS']
p_df = data[data['Season'] == 'Playoffs']

# Only need these categories. Percentages will be manually calculated
total_cols = ['MIN', 'FGM', 'FGA', 'FG3M', 'FG3A', 'FTM', 'FTA',
              'OREB', 'DREB', 'REB', 'AST', 'STL', 'BLK', 'TOV', 'PF', 'PTS']


def percents(df):
    # Percentage stats
    df['FG%'] = df['FGM'] / df['FGA']
    df['3PT%'] = df['FG3M'] / df['FG3A']
    df['FT%'] = df['FTM'] / df['FTA']
    df['AST%'] = df['AST'] / df['FGM']
    df['FG3A%'] = df['FG3A'] / df['FGA']
    df['PTS/FGA'] = df['PTS'] / df['FGA']
    df['FG3M/FGM'] = df['FG3M'] / df['FGM']
    df['FTA/FGA'] = df['FTA'] / df['FGA']
    df['TRU%'] = 0.5 * df['PTS'] / (df['FGA'] + 0.475 * df['FTA'])
    df['AST_TOV'] = df['AST'] / df['TOV']
    return df


# This definition trims any dataset that has too few minutes or too few games played
# This removes outliers and misrepresentative stats
def hist_data(df=rs_df, min_MIN=0, min_GP=0):
    return df.loc[(df['MIN'] >= min_MIN) & (df['GP'] >= min_GP), 'MIN'] / \
        df.loc[(df['MIN'] >= min_MIN) & (df['GP'] >= min_GP), 'GP']



##### Heat Map #####
dpm = data.groupby(['PLAYER', 'PLAYER_ID', 'Year'])[total_cols].sum().reset_index()

for col in dpm.columns[4:]:
    dpm[col] = dpm[col] / dpm['MIN']

dpm = percents(dpm)
dpm = dpm[dpm['MIN'] >= 50]  # Must play min of 50 mins to be included
dpm.drop(columns='PLAYER_ID', inplace=True)  # Remove PLAYER_ID column bc it's pointless

# Plotting
fig = px.imshow(dpm.corr(numeric_only=True),
                labels=dict(x="Categories(x)", y="Categories(y)", color="Correlation"))
fig.update_layout(title=f"Correlation Heatmap of All Stats ({data['Year'].iloc[0]} to {data['Year'].iloc[-1]} Seasons)")
fig.show()

##### Distribution of Minutes Played #####

year_diff = data['season_start_year'].max() - data['season_start_year'].min()

# Plotting
fig = go.Figure()
fig.add_trace(go.Histogram(x=hist_data(rs_df, 50, 5), histnorm='percent', name='Regular Season',
                           xbins={'start': 0, 'end': 46, 'size': 1}))
fig.add_trace(go.Histogram(x=hist_data(p_df, 5, 1), histnorm='percent', name='Playoffs',
                           xbins={'start': 0, 'end': 46, 'size': 1}))
fig.update_layout(title=f"Distribution of Minutes Played by % Over {year_diff} Years",
                  xaxis_title='Minutes Played',
                  yaxis_title='% of Players',
                  showlegend=True)
fig.show()

##### How has the game changed? #####

# Combine all player data for each yr and estimate approx. # of possessions per year
change_df = data.groupby('season_start_year')[total_cols].sum().reset_index()
change_df['POSS_est'] = change_df['FGA'] - change_df['OREB'] + change_df['TOV'] + 0.44 * change_df['FTA']
change_df[list(change_df.columns[0:2]) + ['POSS_est'] + list(change_df.columns[2:-1])]

# Change per 48 mins
cp48_df = change_df.copy()
cp48_df = percents(cp48_df)
for col in cp48_df.columns[2:18]:
    cp48_df[col] = (cp48_df[col] / cp48_df['MIN']) * 48 * 5

cp48_df.drop(columns='MIN', inplace=True)

fig = go.Figure()
for col in cp48_df.columns[1:]:
    fig.add_trace(go.Scatter(x=cp48_df['season_start_year'],
                             y=cp48_df[col], name=col))
fig.update_layout(title=f"Distribution of All Stats Per 48 Minutes Played "
                        f"({data['Year'].iloc[0]} to {data['Year'].iloc[-1]} Seasons)",
                  legend_title_text='Single click a stat<br>to select/deselect;<br>Double click to isolate it:',
                  xaxis_title='Season Start Year',
                  yaxis_title='Average per 48 Minutes',
                  showlegend=True)
fig.show()

# Change per 100 possessions
cp100_df = change_df.copy()
cp100_df = percents(cp100_df)
for col in cp100_df.columns[2:18]:
    cp100_df[col] = (cp100_df[col] / cp100_df['POSS_est']) * 100

cp100_df.drop(columns=['MIN', 'POSS_est'], inplace=True)

# Plotting
fig = go.Figure()
for col in cp100_df.columns[1:]:
    fig.add_trace(go.Scatter(x=cp100_df['season_start_year'],
                             y=cp100_df[col], name=col))
fig.update_layout(title=f"Distribution of All Stats Per 100 Possessions Played "
                        f"({data['Year'].iloc[0]} to {data['Year'].iloc[-1]} Seasons)",
                  legend_title_text='Single click a stat<br>to select/deselect;<br>Double click to isolate it:',
                  xaxis_title='Season Start Year',
                  yaxis_title='Average per 100 Possessions',
                  showlegend=True)

fig.show()

##### Regular Season vs. Playoffs (Percent Change) #####

# Group the separated dataframes by season
rs_c_df = rs_df.groupby('season_start_year')[total_cols].sum().reset_index()
p_c_df = p_df.groupby('season_start_year')[total_cols].sum().reset_index()

# Recalculates percentages for both regular season and playoffs
for i in [rs_c_df, p_c_df]:
    i['POSS_est'] = i['FGA'] - i['OREB'] + i['TOV'] + i['FTA'] * 0.44
    i['POSS_48'] = (i['POSS_est'] / i['MIN']) * 48 * 5
    i = percents(i)

    # x100 to get percentage
    for col in total_cols:
        i[col] = 100 * i[col] / i['POSS_est']

    i.drop(columns=['MIN', 'POSS_est'], inplace=True)

# %Change from reg season to playoffs each year
comparison_df = round(100 * (p_c_df - rs_c_df) / rs_c_df, 3)
comparison_df['season_start_year'] = (
    list(range(rs_c_df['season_start_year'].iloc[0], rs_c_df['season_start_year'].iloc[-1]+1)))

# Plotting
fig = go.Figure()
for col in comparison_df.columns[1:]:
    fig.add_trace(go.Scatter(x=comparison_df['season_start_year'],
                             y=comparison_df[col], name=col))
fig.update_layout(title=f"Percent Change In All Stats Between Regular Season and Playoffs "
                        f"({data['Year'].iloc[0]} to {data['Year'].iloc[-1]} Seasons)",
                  legend_title_text='Single click a stat<br>to select/deselect;<br>Double click to isolate it:',
                  xaxis_title='Season Start Year',
                  yaxis_title='Percentage',
                  showlegend=True)

fig.show()
print('Done!')
os.remove('nba_player_data.xlsx')
