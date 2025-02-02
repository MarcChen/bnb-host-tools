import os
import json

# Token response from your received data from OAuth Playground
# https://stackoverflow.com/questions/19766912/how-do-i-authorise-an-app-web-or-installed-without-user-intervention/19766913#19766913
# https://developers.google.com/oauthplayground/?code=4/0AdLIrYcBVbTAaNgid9cyz0YUmwc9e1zgZq2RMnT_-mFFTH3Or0E2C96bVB3nmojb7dOrMg&scope=https://www.googleapis.com/auth/calendar%20https://mail.google.com/%20https://www.googleapis.com/auth/drive
token_response = {
  "access_token": os.getenv("GOOGLE_ACCESS_TOKEN"), 
  "scope": "https://www.googleapis.com/auth/drive https://mail.google.com/ https://www.googleapis.com/auth/calendar", 
  "token_type": "Bearer", 
  "expires_in": 3599, 
  "refresh_token": os.getenv("GOOGLE_REFRESH_TOKEN"),
  "client_id": os.getenv("GOOGLE_CLIENT_ID"),
  "client_secret": os.getenv("GOOGLE_CLIENT_SECRET")
}

# Construct the save path
SAVE_PATH = os.path.join(os.getenv("PROJECT_ROOT"), "token.json")

# Ensure the directory exists
os.makedirs(os.path.dirname(SAVE_PATH), exist_ok=True)

# Save the tokens to a file
with open(SAVE_PATH, 'w') as token_file:
    json.dump(token_response, token_file)

print("Tokens have been saved successfully.")