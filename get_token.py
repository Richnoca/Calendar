import requests
import os
from dotenv import load_dotenv

def get_token(client_id, client_secret, code):
    response = requests.post(
        'https://www.strava.com/oauth/token',
        data={
            'client_id': client_id,
            'client_secret': client_secret,
            'code': code,
            'grant_type': 'authorization_code'
        }
    )
    
    if response.status_code != 200:
        print(f"Error: {response.status_code}")
        print(response.text)
        return
    
    token_data = response.json()
    
    # Read current .env file
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update tokens in .env content
    new_lines = []
    for line in lines:
        if line.startswith('STRAVA_ACCESS_TOKEN='):
            new_lines.append(f'STRAVA_ACCESS_TOKEN={token_data["access_token"]}\n')
        elif line.startswith('STRAVA_REFRESH_TOKEN='):
            new_lines.append(f'STRAVA_REFRESH_TOKEN={token_data["refresh_token"]}\n')
        else:
            new_lines.append(line)
    
    # Add refresh token if it doesn't exist
    if not any(line.startswith('STRAVA_REFRESH_TOKEN=') for line in new_lines):
        new_lines.append(f'STRAVA_REFRESH_TOKEN={token_data["refresh_token"]}\n')
    
    # Write back to .env file
    with open('.env', 'w') as f:
        f.writelines(new_lines)
    
    print("Tokens updated successfully!")
    print(f"Access Token: {token_data['access_token'][:10]}...")
    print(f"Refresh Token: {token_data['refresh_token'][:10]}...")

if __name__ == '__main__':
    load_dotenv()
    
    client_id = os.getenv('STRAVA_CLIENT_ID')
    client_secret = os.getenv('STRAVA_CLIENT_SECRET')
    
    if not client_id or not client_secret:
        print("Error: Make sure STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET are set in your .env file")
        exit(1)
    
    print("Please visit this URL:")
    print(f"https://www.strava.com/oauth/authorize?client_id={client_id}"
          f"&response_type=code&redirect_uri=http://localhost"
          f"&approval_prompt=force&scope=read_all,profile:read_all,activity:read_all")
    
    # If you previously hard-coded a code here, remove it — authorization codes are single-use and expire quickly.
    # Visit the printed URL, authorize, then copy the `code` parameter from the redirect (http://localhost?code=...)
    code = input("\nEnter the 'code' parameter from the redirect URL: ").strip()
    get_token(client_id, client_secret, code)
