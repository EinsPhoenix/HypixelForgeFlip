import json
import os
import asyncio
import aiofiles
import time

# Paths to JSON files
forge_json_path = "./ForgeData/forgable_items.json"
auction_json_path = "./DataAPI/Auctions"
ended_auction_path = "./DataAPI/EndedAuction.json"
reforges_json_path = "./DataAPI/reforges.json"
item_json_path = "./DataAPI/Items.json"
output_json_path = "./DataAPI/Output/output.json"

# Data structures
desired_internalnames = []
items_data = []
ended_auction = {}
auctions_data = []
reforges_data = {}
names_data = {}
output_json_data = {}

output = {
    "lastTimeUpdate": None,
    "items": [],
    "average": []
}

# Function to load JSON file asynchronously
async def load_json(path):
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return json.loads(await f.read())
    except Exception as e:
        print(f"Error loading JSON from {path}: {e}")
        return {}

# Function to load all required JSON files
async def load_jsons():
    global items_data, ended_auction, reforges_data, names_data, desired_internalnames

    items_data, reforges_data, names_data, ended_auction = await asyncio.gather(
        load_json(forge_json_path),
        load_json(reforges_json_path),
        load_json(item_json_path),
        load_json(ended_auction_path)
    )

    # Load auction data
    auction_files = [file for file in os.listdir(auction_json_path) if file.endswith(".json")]
    auction_tasks = [load_json(os.path.join(auction_json_path, file)) for file in auction_files]
    auction_results = await asyncio.gather(*auction_tasks)
    
    # Combine auction data
    for auction_data in auction_results:
        auctions_data.extend(auction_data.get("auctions", []))

    # Filter names data
    names_data = names_data.get("items", [])
    desired_internalnames = [item.get("internalname") for item in items_data if "internalname" in item]

def calculate_results():
    for item_uuid in output_json_data:
        for item in ended_auction.get("auctions", []):
            if item_uuid.get("uuid") == item.get("auction_id"):
                output["average"].append({
                    "name": item_uuid.get("item"),
                    "lowest_bin": item_uuid.get("lowest_bin"),
                    "auction_id": item_uuid.get("auction_id")
                })

def search_for_item_in_auction(input_item):
    normalized_input_item = input_item.split(":")[0]
    
    lowest_starting_bid = float('inf')
    item_name_auction = ""
    ahUUID = ""

    for ah_item in names_data:
        if normalized_input_item == ah_item.get("id"):
            item_name_auction = ah_item.get("name")  # Assuming `calculatePriceToBuy.remove_color_codes` was used here

    matching_auctions = [
        auction for auction in auctions_data
        if item_name_auction in auction.get("item_name", "") and auction.get("bin")
    ]

    for auction in matching_auctions:
        if auction.get("starting_bid", float('inf')) < lowest_starting_bid:
            lowest_starting_bid = auction["starting_bid"]
            ahUUID = auction["uuid"]
            auctioneer = auction["auctioneer"]

    if lowest_starting_bid != float('inf'):
        output["items"].append({
            "item": normalized_input_item,
            "lowest_bin": lowest_starting_bid,
            "auctionId": ahUUID,
            "auctioneer": auctioneer
        })

# Function to start scanning auctions
def start_scanning():
    output["items"].clear()  # Clear previous results
    for item in desired_internalnames:
        search_for_item_in_auction(item)
    calculate_results()
    output["lastTimeUpdate"] = time.strftime('%Y-%m-%d %H:%M:%S', time.gmtime())
    
    # Create the output file if it doesn't exist
    os.makedirs(os.path.dirname(output_json_path), exist_ok=True)
    if not os.path.isfile(output_json_path):
        with open(output_json_path, 'w', encoding='utf-8') as f:
            json.dump({}, f)
    
    # Write the output data
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=4)

# Function to run the scanner periodically
async def periodic_scanning():
    while True:
        start_scanning()
        await asyncio.sleep(30)  # Wait for 30 seconds

# Main function to load data and start periodic scanning
async def main():
    await load_jsons()
    await periodic_scanning()

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
