import requests
import json
import asyncio
import time
from datetime import datetime

# Define your Discord webhook URL
WEBHOOK_URL = 'WEBHOOK_URL'

# Define the API endpoint URLs
API_URL = 'https://pepeexplorer.com/ext/getsummary'
GET_BLOCK_HASH_URL = 'https://pepeexplorer.com/api/getblockhash?index='
GET_BLOCK_INFO_URL = 'https://pepeexplorer.com/api/getblock?hash='

# Variable to store the previous block count
previous_block_count = None

# Function to fetch data from the API endpoint
async def fetch_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            print("Failed to fetch data from API:", response.status_code)
            return None
    except Exception as e:
        print("Error occurred while fetching data:", str(e))
        return None

# Function to send a message to Discord webhook as a rich embed
async def send_to_discord(message):
    # Construct the payload for the rich embed
    payload = {
        "embeds": [
            {
                "title": "New Block Mined!",
                "description": message,
                "color": 39232  # Green color
            }
        ]
    }

    # Send a POST request to the webhook URL
    response = requests.post(WEBHOOK_URL, json=payload, allow_redirects=True)
    
    # Check if the request was successful
    if response.status_code == 204:
        print("Message sent to Discord successfully")
    elif response.status_code >= 400:
        print("Failed to send message to Discord:", response.status_code)
    else:
        print("Unexpected response from Discord:", response.status_code)

# Main function to monitor changes and send messages to Discord
async def main():
    global previous_block_count
    
    while True:
        # Fetch data from the API endpoint
        data = await fetch_data()
        
        if data:
            # Extract relevant information
            block_count = data.get('blockcount')
            difficulty = data.get('difficulty')
            
            # Check if block count has changed
            if block_count != previous_block_count:
                # Format difficulty without decimals
                formatted_difficulty = '{:,.0f}'.format(float(difficulty))
                
                # Fetch block hash using block number
                block_hash_response = requests.get(GET_BLOCK_HASH_URL + str(block_count))
                block_hash = block_hash_response.text
                
                # Fetch block info using block hash
                block_info_response = requests.get(GET_BLOCK_INFO_URL + block_hash)
                try:
                    block_info_data = block_info_response.json()
                except json.decoder.JSONDecodeError as e:
                    print("Error decoding JSON data for block info:", str(e))
                    print("Response:", block_info_response.text)
                    block_info_data = None
                
                if block_info_data:
                    # Format time in the desired format
                    formatted_time = f"<t:{block_info_data['time']}:R>"
                    
                    # Construct message
                    message = f"**Block:** {block_count}\n**New Difficulty:** {formatted_difficulty}\n**Time:** {formatted_time}"

                    # Send message to Discord as a rich embed
                    await send_to_discord(message)
                    
                    # Update previous block count
                    previous_block_count = block_count
            else:
                print("Block count hasn't changed. Skipping...")

        # Sleep for a certain interval before checking again (e.g., 1 minute)
        await asyncio.sleep(60)  # sleep for 1 minute

# Run the main function asynchronously
asyncio.run(main())
