# Steam Games Library (SGL)

Automatic data collector of your Steam library with export to Google Sheets. The service collects information about pass time and achievements, and also supports data caching for faster work.

---

## 📋 Features
- 🎮 Collect data about your Steam games
- ⏱️ Pass time information from HowLongToBeat
- 📊 Export data to Google Sheets
- 💾 Caching data to speed up repeated requests
- 🔄 Automatically update information
- 📝 Logging of all actions for diagnostics

---

## 🚀 Installation

### 1. Install Python
Make sure you have Python version 3.7 or higher installed. You can download it [here](https://www.python.org/downloads/).

### 2. Download the project
Download the latest version of the script or clone the repository:
```bash
git clone https://github.com/PilMek/SGL.git
cd SGL
```

### 3. Install dependencies
The script will automatically install the required libraries at the first run. If you want to do it manually, execute:
```bash
pip install -r requirements.txt
```

---

## ⚙️

### Steam API Setup
1. **Get API key**:
   Go to [Steam Web API](https://steamcommunity.com/dev/apikey) and create an API key.
2. **Find your SteamID64**:
   Use the [Steam ID Finder](https://steamidfinder.com/) to determine your profile ID.
3. **Refresh the settings in `SGL.py`**:
```python
api_key = "INSERT_API_KEY"  # API key Steam
steam_id = "INSERT_STEAMID64"  # Steam profile Id
```

### Customizing Google Sheets
1. **Create a project in Google Cloud Console**:
   - Go to [Google Cloud Console](https://console.cloud.google.com/).
   - Enable the API for Google Sheets.
2. **Create a service account**:
   - Create a service account and download the JSON key.
   - Rename the key to `Google_Credentials.json` and move it to the script folder.
3. **Create a Google table**:
   - Create the table and grant the service account access with editor privileges.
   - Copy the table ID from the URL and update it in `SGL.py`:
```python
spreadsheet_id = 'INSERT_SPREADSHEET_ID'  # Google Sheet Id
range_name = 'INSERT_NAME_LIST'  # Name list of Google Sheet
```

---

## 🎮 Usage

### 1. Running the script
Once configured, simply run the script with a double click or through the console:
```bash
python SGL.py
```

The script will perform the following actions:
- Check/install missing libraries.
- Gather information about your Steam games.
- Update the data in Google Sheets.
- Save the cache to optimize future requests.

### 2. Result
- Your Google Sheets table will contain the following information:
  - App ID
  - Name of the game (with a link to Steam)
  - Game Time (hours)
  - Achievement Progress (%) - If the table says N/A, then the game has no achievements
  - Completion time (main story, all styles, completion)

Example of a completed table:

| App ID | Title           | Playing time (hours) | Achievements (%) | Main Story | All Styles | Completionist |
|--------|-----------------|----------------------|------------------|------------|------------|---------------|
| 440    | Team Fortress 2 | 120.5                | 50%              | 10         | 20         | 25            |
| 570    | Dota 2          | 300.0                | 0%               | N/A        | N/A        | N/A           |

---

## 📝 Logging
- All actions are recorded in the `SGL_Logs.log` file.
- If errors occur, examine this file for diagnosis.

## 💾 Caching
- The cache is stored in the `SGL_Cache.json` file and contains data about previously processed games.
- If you need to update the data, simply delete the cache file before running the script.

---

## ❗ Possible problems

### Google Sheets authorization errors
- Check that the `Google_Credentials.json` file is in the script folder.
- Verify that the service account has access to the table.

### Steam API errors
- Verify that the API key you entered is correct.
- Make sure your Steam profile is public.

### Slow performance
- The script pauses between requests to comply with API limits. This is normal.
- Use the cache to speed up reruns.