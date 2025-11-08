#
# Libraries
#
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import WebDriverException
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import pandas as pd
import re
import time
import os

#
# 1. ChromeDriver Configuration
#
# Using webdriver-manager to automatically download and manage ChromeDriver
try:
    # Automatically download and manage the correct ChromeDriver version
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)
    print("ChromeDriver initialized successfully using webdriver-manager")
except WebDriverException as e:
    print(f"Failed to initialize ChromeDriver: {str(e)}")
    print("Please ensure Google Chrome is installed on your system")
    exit(1)
except Exception as e:
    print(f"Unexpected error initializing ChromeDriver: {str(e)}")
    exit(1)

#
# 2. URLs for different statistical categories
#
STATS_URLS = {
    'standard': "https://fbref.com/en/comps/9/2024-2025/stats/2024-2025-Premier-League-Stats",
    'shooting': "https://fbref.com/en/comps/9/2024-2025/shooting/2024-2025-Premier-League-Stats",
    'passing': "https://fbref.com/en/comps/9/2024-2025/passing/2024-2025-Premier-League-Stats",
    'gca': "https://fbref.com/en/comps/9/2024-2025/gca/2024-2025-Premier-League-Stats",
    'defense': "https://fbref.com/en/comps/9/2024-2025/defense/2024-2025-Premier-League-Stats",
    'possession': "https://fbref.com/en/comps/9/2024-2025/possession/2024-2025-Premier-League-Stats",
    'misc': "https://fbref.com/en/comps/9/2024-2025/misc/2024-2025-Premier-League-Stats",
    'keeper': "https://fbref.com/en/comps/9/2024-2025/keepers/2024-2025-Premier-League-Stats"

}

#
# 3. UPDATED: Mapping from website data-stat attribute to CSV column name and data type
# This now uses the correct data-stat attributes found in the debugging script
#
COLUMN_MAP = {
    # Basic Player Info
    'player': ('Player', str),
    'nationality': ('Nation', str),
    'position': ('Pos', str),
    'team': ('Team', str),
    'age': ('Age', int),

    # Standard Stats (from standard table)
    'minutes': ('Standard_Min', int),
    'goals': ('Standard_Gls', int),
    'assists': ('Standard_Ast', int),
    'cards_yellow': ('Standard_CrdY', int),
    'cards_red': ('Standard_CrdR', int),
    'xg': ('Standard_xG', float),
    'xg_assist': ('Standard_xAG', float),
    'progressive_carries': ('Standard_PrgC', int),
    'progressive_passes': ('Standard_PrgP', int),
    'progressive_passes_received': ('Standard_PrgR', int),

    # Per 90 Stats (from standard table)
    'goals_per90': ('Standard_Gls/90', float),
    'assists_per90': ('Standard_Ast/90', float),
    'xg_per90': ('Standard_xG/90', float),
    'xg_assist_per90': ('Standard_xAG/90', float),

    # Shooting Stats (from shooting table) - CORRECTED NAMES
    'shots_on_target_pct': ('Shooting_SoT%', float),
    'shots_on_target_per90': ('Shooting_SoT/90', float),
    'goals_per_shot': ('Shooting_G/Sh', float),
    'average_shot_distance': ('Shooting_Dist', float),

    # Passing Stats (from passing table) - CORRECTED NAMES
    'passes_completed': ('Passing_Cmp', int),
    'passes_pct': ('Passing_Total_Cmp%', float),
    'passes_total_distance': ('Passing_TotDist', int),
    'passes_pct_short': ('Passing_Short_Cmp%', float),
    'passes_pct_medium': ('Passing_Medium_Cmp%', float),
    'passes_pct_long': ('Passing_Long_Cmp%', float),
    'assisted_shots': ('Passing_KP', int),
    'passes_into_final_third': ('Passing_1/3', int),
    'passes_into_penalty_area': ('Passing_PPA', int),
    'crosses_into_penalty_area': ('Passing_CrsPA', int),

    # Goalkeeping Stats (from keepers table)

    'gk_goals_against_per90': ('Goalkeeping_GA90', float),
    'gk_save_pct': ('Goalkeeping_Save%', float),
    'gk_clean_sheets_pct': ('Goalkeeping_CS%', float),

    # Defense Stats (from defense table) - CORRECTED NAMES
    'tackles': ('Defense_Tkl', int),
    'tackles_won': ('Defense_TklW', int),
    'challenges': ('Defense_Att', int),  # Renamed from dribblers_tackled
    'challenges_lost': ('Defense_Lost', int),
    'blocks': ('Defense_Blocks', int),
    'blocked_shots': ('Defense_Sh', int),
    'blocked_passes': ('Defense_Pass', int),
    'interceptions': ('Defense_Int', int),

    # Possession Stats (from possession table) - CORRECTED NAMES
    'touches': ('Possession_Touches', int),
    'touches_def_pen_area': ('Possession_Def Pen', int),
    'touches_def_3rd': ('Possession_Def 3rd', int),
    'touches_mid_3rd': ('Possession_Mid 3rd', int),
    'touches_att_3rd': ('Possession_Att 3rd', int),
    'touches_att_pen_area': ('Possession_Att Pen', int),
    'take_ons_won_pct': ('Possession_Succ%', float),  # Renamed from dribble_success_pct
    'take_ons_tackled_pct': ('Possession_Tkld%', float),  # Renamed from dribbled_past_pct
    'carries': ('Possession_Carries', int),
    'carries_progressive_distance': ('Possession_PrgDist', int),  # Corrected name
    'carries_into_final_third': ('Possession_1/3', int),
    'carries_into_penalty_area': ('Possession_CPA', int),
    'miscontrols': ('Possession_Mis', int),
    'dispossessed': ('Possession_Dis', int),
    'passes_received': ('Possession_Rec', int),

    # Misc Stats (from misc table) - CORRECTED NAMES
    'fouls': ('Misc_Fls', int),
    'fouled': ('Misc_Fld', int),  # Corrected name from fouls_drawn
    'offsides': ('Misc_Off', int),
    'crosses': ('Misc_Crs', int),
    'ball_recoveries': ('Misc_Recov', int),
    'aerials_won': ('Misc_Won', int),
    'aerials_lost': ('Misc_Lost', int),
    'aerials_won_pct': ('Misc_Won%', float)
}

#
# 4. Helper functions to get HTML and parse values
#
def get_html(url):
    """Navigates to a URL and returns the page source after the stats table has loaded."""
    driver.get(url)
    WebDriverWait(driver, 20).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'table.stats_table')))
    time.sleep(3)  # Additional wait to ensure all dynamic content is loaded
    return driver.page_source

def parse_value(raw_value, dtype):
    """Cleans and converts a raw string value to the specified data type."""
    try:
        if not raw_value or raw_value.strip() == '':
            return 'N/A'

        cleaned_value = raw_value.replace(',', '').replace('%', '').replace('+', '').strip()

        if dtype is int:
            return int(float(cleaned_value)) if cleaned_value else 0
        elif dtype is float:
            if '%' in raw_value:
                return round(float(cleaned_value) / 100, 3)
            return float(cleaned_value) if cleaned_value else 0.0
        else:
            return raw_value.strip()
    except (ValueError, TypeError):
        return 'N/A'

#
# 5. Main data crawling loop - IMPROVED
#
players_data = {}
debug_info = {stat_type: {'found_players': 0, 'missing_stats': 0} for stat_type in STATS_URLS.keys()}

for stat_type, url in STATS_URLS.items():
    print(f"Crawling: {stat_type}...")
    try:
        html = get_html(url)
        soup = BeautifulSoup(html, 'html.parser')

        # Try to find the table with standard ID pattern
        table_id = f'stats_{stat_type}'
        table = soup.find("table", id=table_id)
        if not table:
            print(f"  Warning: Table with id '{table_id}' not found")
            # Try alternative table finding method
            table = soup.find("table", {"class": "stats_table"})

        if not table:
            print(f"  Error: No stats table found for {stat_type}")
            continue

        tbody = table.find('tbody')
        if not tbody:
            print(f"  Warning: No tbody found in {stat_type} table")
            continue

        rows_processed = 0
        for row in tbody.find_all('tr'):
            player_cell = row.find("th", {'data-stat': 'player'}) or row.find("td", {'data-stat': 'player'})
            if not player_cell:
                continue

            player_name = player_cell.text.strip()
            debug_info[stat_type]['found_players'] += 1

            if player_name not in players_data:
                players_data[player_name] = {col: 'N/A' for col, _ in COLUMN_MAP.values()}
                players_data[player_name]['Player'] = player_name

            stats_found_in_row = 0
            for cell in row.find_all(['th', 'td']):
                stat = cell.get('data-stat')
                if stat in COLUMN_MAP:
                    col_name, dtype = COLUMN_MAP[stat]
                    raw_value = cell.text.strip()

                    # Special handling for specific columns
                    if stat == 'age' and '-' in raw_value:
                        raw_value = raw_value.split('-')[0]
                    if stat == 'nationality':
                        match = re.search(r'(\w+)\s+([A-Z]{3})', raw_value)
                        if match:
                            raw_value = f"{match.group(2)}" # Only keep the 3-letter code

                    parsed_value = parse_value(raw_value, dtype)
                    players_data[player_name][col_name] = parsed_value
                    stats_found_in_row += 1

            if stats_found_in_row == 0:
                debug_info[stat_type]['missing_stats'] += 1

        print(f"  Processed data from {stat_type} table")

    except Exception as e:
        print(f"Error crawling {stat_type}: {str(e)}")
        continue

#
# 6. Filter, format, and save the data - IMPROVED
#
filtered_data = []
players_with_insufficient_data = 0

for player_name, player_data in players_data.items():
    try:
        # Filter for players with more than 90 minutes
        minutes_played = player_data.get('Standard_Min', 0)
        if minutes_played != 'N/A' and int(minutes_played) > 90:
            ordered_row = [player_data.get(col, 'N/A') for col, _ in COLUMN_MAP.values()]
            filtered_data.append(ordered_row)
        else:
            players_with_insufficient_data += 1
    except (ValueError, TypeError):
        players_with_insufficient_data += 1
        continue

# Create DataFrame and save to CSV
columns = [col for col, _ in COLUMN_MAP.values()]
df = pd.DataFrame(filtered_data, columns=columns)
df.fillna('N/A', inplace=True)

# Sort players alphabetically by first name
df.sort_values(by='Player', inplace=True)

# Get the directory where the script is located
script_dir = os.path.dirname(os.path.abspath(__file__))
output_file = os.path.join(script_dir, "results.csv")
df.to_csv(output_file, index=False, encoding='utf-8')

print(f"\n=== SUMMARY ===")
print(f"Data for {len(df)} players saved to {output_file}")
print(f"Players excluded due to insufficient minutes (< 90): {players_with_insufficient_data}")

# Print debug information
# print(f"\n=== DEBUG INFO ===")
# for stat_type, info in debug_info.items():
#     print(f"{stat_type}: {info['found_players']} players processed, {info['missing_stats']} rows with no matching stats")

# Count non-N/A values for each column
# print(f"\n=== DATA COMPLETENESS ===")
# for col in columns:
#     non_na_count = df[col].value_counts().get('N/A', 0)
#     available_count = len(df) - non_na_count
#     percentage = (available_count / len(df) * 100) if len(df) > 0 else 0
#     print(f"{col}: {available_count}/{len(df)} ({percentage:.1f}%) available")

driver.quit()