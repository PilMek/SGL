import subprocess
import sys
import logging
import os

cache_file = 'SGL_Cache.json'
log_file = "SGL_Logs.log"

# Clearing the log file before starting a new job
if os.path.exists(log_file):
    with open(log_file, 'w'):
        pass

# Configuring logging
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def install_requirements():
    required_packages = [
        'requests',
        'pandas',
        'howlongtobeatpy',
        'google-api-python-client',
        'google-auth'
    ]
    
    logging.info("Checking installed libraries...")
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
            logging.info(f"The {package} library is already installed")
        except ImportError:
            logging.info(f"Installing the {package} library...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package])
                logging.info(f"The {package} library was successfully installed")
            except subprocess.CalledProcessError as e:
                logging.error(f"Error when installing the {package} library: {e}")
                exit(1)

if __name__ == '__main__':
    install_requirements()

import requests
import pandas as pd
import time
import json
import re
from datetime import datetime, timedelta
from howlongtobeatpy import HowLongToBeat
from googleapiclient.discovery import build
from google.oauth2.service_account import Credentials
from googleapiclient.errors import HttpError
from requests.exceptions import SSLError

# Data Configuration
api_key = "INSERT_API_KEY" # API key Steam
steam_id = "INSERT_STEAMID64" # Steam Profile Id
spreadsheet_id = 'INSERT_SPREADSHEET_ID' # Google Sheet table Id
range_name = 'INSERT_NAME_LIST' # Name list of Google Sheet
creds = Credentials.from_service_account_file('Google_Credentials.json') # Google Cloud service account key file

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Authentication with Google Sheets
logging.info("Authentication with Google Sheets...")
try:
    service = build('sheets', 'v4', credentials=creds)
    logging.info("Successful authentication with Google Sheets.")
except Exception as e:
    logging.error(f"Error when authenticating with Google Sheets: {e}")
    exit()

# Function to load the cache
def load_cache():
    if os.path.exists(cache_file):
        try:
            with open(cache_file, 'r') as f:
                data = json.load(f)
                logging.info(f"Cache successfully loaded from {cache_file}")
                return data
        except json.decoder.JSONDecodeError:
            logging.warning(f"The cache file {cache_file} is empty or contains incorrect data. Create a new cache.")
            return {}
    logging.info(f"The cache file {cache_file} was not found. Creating a new cache.")
    return {}

# Function to save the cache
def save_cache(cache, filepath):
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=4)

# Function to retrieve data from Google Sheets
def get_existing_data():
    try:
        result = service.spreadsheets().values().get(spreadsheetId=spreadsheet_id, range=range_name).execute()
        return result.get('values', [])
    except HttpError as err:
        logging.error(f"Error when retrieving data from Google Sheets: {err}")
        return []

# Function to update data in Google Sheets
def update_data_in_sheets(range_name, updated_data):
    max_retries = 10
    for attempt in range(max_retries):
        try:
            limited_data = []
            for row in updated_data:
                if len(row) > 7:
                    limited_data.append(row[:7])
                else:
                    limited_data.append(row)

            body = {
                'values': limited_data
            }
            service.spreadsheets().values().update(
                spreadsheetId=spreadsheet_id, 
                range=range_name,
                valueInputOption="USER_ENTERED",
                body=body
            ).execute()
            return
        except (HttpError, SSLError) as err:
            logging.error(f"Error when updating Google Sheets: {err}")
            if attempt < max_retries - 1:
                logging.info(f"Retrying to update data in Google Sheets ({attempt + 1}/{max_retries})...")
                time.sleep(5)
            else:
                logging.error("The number of attempts to update data in Google Sheets has been exceeded.")
                raise

# Get a game library from Steam
def fetch_steam_games():
    games_url = f"https://api.steampowered.com/IPlayerService/GetOwnedGames/v1/?key={api_key}&steamid={steam_id}&include_played_free_games=1&include_appinfo=1"
    logging.info("Sending a request to the Steam API to get a list of games...")
    response = requests.get(games_url)
    logging.info(f"Response received from Steam API: {response.status_code}")
    
    if response.status_code != 200:
        logging.error(f"Incorrect reply status: {response.status_code}")
        return []

    data = response.json()
    if "response" not in data or "games" not in data["response"]:
        logging.error("The structure of the Steam API response is incorrect.")
        return []
    
    games = data["response"]["games"]
    logging.info(f"Found {len(games)} games.")
    
    processed_games = []
    for index, game in enumerate(games, start=1):
        app_id = game["appid"]
        game_name = game.get('name', 'Unknown')
        logging.info(f"[{index}/{len(games)}] Game Processing: {game_name}")
        
        # Use a different endpoint to get achievements
        stats_url = f"https://api.steampowered.com/ISteamUserStats/GetPlayerAchievements/v1/?appid={app_id}&key={api_key}&steamid={steam_id}"
        try:
            stats_response = requests.get(stats_url)
            achievements = "N/A"
            
            if stats_response.status_code == 200:
                stats_data = stats_response.json()
                if ('playerstats' in stats_data and 
                    'achievements' in stats_data['playerstats'] and 
                    'success' in stats_data['playerstats'] and 
                    stats_data['playerstats']['success']):
                    
                    achievements_list = stats_data['playerstats']['achievements']
                    if achievements_list:
                        achieved = sum(1 for a in achievements_list if a.get('achieved', 0) == 1)
                        total = len(achievements_list)
                        # If there is an achievement but 0 is received, return 0%
                        achievements = round((achieved / total) * 100, 2) if total > 0 else 0
            
        except Exception as e:
            logging.error(f"Error when obtaining achievements for {game_name}: {e}")
            achievements = "N/A"
            
        processed_games.append({
            "id": app_id,
            "name": game_name,
            "playtime": round(game["playtime_forever"] / 60, 1),
            "achievements": achievements
        })
        
    return processed_games

# Function to get the transit time from HowLongToBeat
def get_game_time(game_name, index, total):
    # Delete ™ and other special characters
    cleaned_game_name = re.sub(r'[™©®]', '', game_name)
    try:
        logging.info(f"[{index}/{total}] Getting passing time for the game: {cleaned_game_name}...")
        results = HowLongToBeat().search(cleaned_game_name)
        if results:
            return {
                "main_story": results[0].main_story if results[0].main_story else "N/A",
                "completionist": results[0].completionist if results[0].completionist else "N/A",
                "all_styles": results[0].all_styles if results[0].all_styles else "N/A"
            }
        else:
            logging.warning(f"No walkthrough time was found for the game {cleaned_game_name}.")
            return {"main_story": "N/A", "completionist": "N/A", "all_styles": "N/A"}
    except Exception as e:
        logging.error(f"Error receiving a pass time: {e}")
        return {"main_story": "N/A", "completionist": "N/A", "all_styles": "N/A"}

# Basic function for processing and updating data
def process_and_update():
    logging.info("Beginning of data processing...")
    existing_data = get_existing_data()
    cache = load_cache()

    # Проверка наличия заголовков
    if not existing_data or existing_data[0][0] != "App ID":
        logging.info("Adding headers to a table...")
        headers = ["App ID", "Title", "Playing time (hours)", "Achievements (%)", "Main Story", "All Styles", "Completionist"]
        existing_data.insert(0, headers)
        update_data_in_sheets(range_name, existing_data)

    steam_games = fetch_steam_games()
    total_games = len(steam_games)
    for index, game in enumerate(steam_games, start=1):
        if 'id' not in game:
            logging.error(f"The 'id' key is missing from the game data: {game}")
            continue

        game_id = str(game["id"])
        game_name = game["name"]
        playtime_hours = game["playtime"]
        achievements = game["achievements"]

        game_link = f'=HYPERLINK("https://store.steampowered.com/app/{game_id}", "{game_name}")'

        if game_id in cache:
            cached_game = cache[game_id]
            if cached_game['playtime'] == playtime_hours and cached_game.get('achievements', 0) == achievements:
                logging.info(f"[{index}/{total_games}] Using the cache to play the game: {game_name}")
                completion_time = cached_game['completion_time']
            else:
                logging.info(f"[{index}/{total_games}] Updating the data for the game: {game_name}")
                completion_time = get_game_time(game_name, index, total_games)
                cache[game_id] = {
                    'name': game_name,
                    'playtime': playtime_hours,
                    'achievements': achievements,
                    'completion_time': completion_time,
                    'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                save_cache(cache, cache_file)
                logging.info(f"[{index}/{total_games}] {game_name} cached")
        else:
            logging.info(f"[{index}/{total_games}] Obtaining data for a new game: {game_name}")
            completion_time = get_game_time(game_name, index, total_games)
            cache[game_id] = {
                'name': game_name,
                'playtime': playtime_hours,
                'achievements': achievements,
                'completion_time': completion_time,
                'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            save_cache(cache, cache_file)
            logging.info(f"[{index}/{total_games}] {game_name} cached")

        game_found = False
        for row_index, row in enumerate(existing_data[1:], start=1):
            if len(row) > 0 and row[0] == game_id:
                if (row[2] != str(playtime_hours) or 
                    (str(row[3]).rstrip('%') != str(achievements) if achievements != "N/A" else row[3] != achievements) or
                    row[4] != str(completion_time["main_story"]) or 
                    row[5] != str(completion_time["all_styles"]) or 
                    row[6] != str(completion_time["completionist"])):
                    
                    row[1] = game_link
                    row[2] = str(playtime_hours)
                    row[3] = f"{achievements}%" if achievements != "N/A" else achievements
                    row[4] = str(completion_time["main_story"])
                    row[5] = str(completion_time["all_styles"])
                    row[6] = str(completion_time["completionist"])
                    update_data_in_sheets(f'{range_name}!A{row_index+1}:G{row_index+1}', [row])
                    logging.info(f"[{index}/{total_games}] {game_name} updated in table")
                game_found = True
                break

        if not game_found:
            new_row = [
                game_id,
                game_link,
                str(playtime_hours),
                f"{achievements}%",
                str(completion_time["main_story"]),
                str(completion_time["all_styles"]),
                str(completion_time["completionist"])
            ]
            existing_data.append(new_row)
            update_data_in_sheets(f'{range_name}!A{len(existing_data)}:G{len(existing_data)}', [new_row])
            logging.info(f"[{index}/{total_games}] {game_name} added to the table")

        time.sleep(1)  # 1 second delay between requests

    logging.info("Data processing is complete.")

if __name__ == '__main__':
    start_time = datetime.now()
    logging.info("Steam data update...")
    process_and_update()
    end_time = datetime.now()
    execution_time = end_time - start_time
    minutes = execution_time.seconds // 60
    seconds = execution_time.seconds % 60
    logging.info(f"Update completed in {minutes} min. {seconds} sec.")