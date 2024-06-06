import pandas as pd
import requests
pd.set_option('display.max_columns', None)
import time
import numpy as np
import openpyxl


def get_years():
    # Prompt the user
    start_year = int(input("Enter the season start year (e.g., 2012 --> 2012-13 Season): "))
    end_year = int(input("Enter the season end year(e.g., 2022 --> 2022-2023 Season): "))

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

        lag = np.random.uniform(low=0.1, high=3)
        print(f'...waiting {round(lag, 1)} seconds')
        time.sleep(lag)
    print(f'Finished scraping data for {y}.')

print(f'Process completed. Total runtime: {round((time.time() - begin_loop) / 60, 2)} minutes.')
df.to_excel('nba_player_data.xlsx', index=False)
del temp_df1, temp_df2, temp_df3

