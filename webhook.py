import requests
import json
import asyncio
from datetime import datetime
import pytz

# Define your Discord webhook URL
WEBHOOK_URL = 'WEBHOOK_URL'

# Define the API endpoint URLs
API_URL = 'https://pepeexplorer.com/ext/getsummary'
GET_BLOCK_HASH_URL = 'https://pepeexplorer.com/api/getblockhash?index='
GET_BLOCK_INFO_URL = 'https://pepeexplorer.com/api/getblock?hash='

# File to store mined blocks and timestamps
MINED_BLOCKS_FILE = 'mined_blocks.json'

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
    # Load mined blocks and timestamps from file
    try:
        with open(MINED_BLOCKS_FILE, 'r') as file:
            mined_blocks = json.load(file)
    except FileNotFoundError:
        mined_blocks = {}

    while True:
        # Fetch data from the API endpoint
        data = await fetch_data()
        
        if data:
            # Extract relevant information
            block_count = data.get('blockcount')
            difficulty = data.get('difficulty')
            
            # Check if block count has changed
            if block_count not in mined_blocks:
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
                    # Convert block timestamp to UTC
                    block_timestamp = block_info_data['time']
                    formatted_time = f"<t:{block_info_data['time']}:R>"
                    # Get the first mined block's timestamp
                    first_mined_block_timestamp = next(iter(mined_blocks.values()), None)
                    
                    # Calculate the number of blocks mined today
                    if first_mined_block_timestamp is not None:
                        blocks_mined_today = block_count - int(list(mined_blocks.keys())[0])
                    else:
                        blocks_mined_today = 0
                    
                    # Construct message
                    message = f"**Block:** {block_count}\n**New Difficulty:** {formatted_difficulty}\n**Time:** {formatted_time}\n**Blocks Mined Today:** {blocks_mined_today}"
                    
                    # Send message to Discord as a rich embed
                    await send_to_discord(message)
                    
                    # Update mined blocks and timestamps
                    mined_blocks[block_count] = block_timestamp
                    
                    # Write updated mined blocks and timestamps to file
                    with open(MINED_BLOCKS_FILE, 'w') as file:
                        json.dump(mined_blocks, file)
            else:
                print("Block has already been processed. Skipping...")

        # Sleep for a certain interval before checking again (e.g., 1 minute)
        await asyncio.sleep(300)  # sleep for 5 minutes

# Run the main function asynchronously
asyncio.run(main())
