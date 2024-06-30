import json
import os
import re
import asyncio
import aiofiles
import time

forge_json_path = "./ForgeData/forgable_items.json"
auction_json_path = "./DataAPI/ActiveAuction.json"
bazaar_json_path = "./DataAPI/Bazaar.json"
reforges_json_path = "./DataAPI/reforges.json"
item_json_path = "./DataAPI/Items.json"

desired_internalnames = []
items_data = {}
bazaar_data = {}
auctions_data = {}
reforges_data = {}
names_data = {}

async def load_json(path):
    async with aiofiles.open(path, 'r', encoding='utf-8') as f:
        return json.loads(await f.read())

async def load_jsons():
    global items_data, bazaar_data, auctions_data, reforges_data, names_data, desired_internalnames

    items_data, bazaar_data, auctions_data, reforges_data, names_data = await asyncio.gather(
        load_json(forge_json_path),
        load_json(bazaar_json_path),
        load_json(auction_json_path),
        load_json(reforges_json_path),
        load_json(item_json_path)
    )

    auctions_data = auctions_data["auctions"]
    names_data = names_data["items"]
    desired_internalnames = [item["internalname"] for item in items_data if "internalname" in item]

is_bin = True
output = {
    "lastTimeUpdate": None,
    "items": []
}

def remove_color_codes(text):
    return re.sub(r'§.', '', text)
def find_item_in_bazaar(input_item, item_info, search_main):
    if not search_main:
        split_item = input_item.split(":")
        normalized_input_item = split_item[0]
        quantity = float(split_item[1])
    else:
        normalized_input_item = input_item
        quantity = 1

    if normalized_input_item == "SKYBLOCK_COIN":
        if not search_main:
            item_info["inputs"].append({
                "name": normalized_input_item,
                "nameClear":"Coins",
                "found_in": "bazaar",
                "quantity": quantity,
                "sell_price": quantity,
                "buy_price": quantity
            })
            item_info["sellTheItemsPrice"] += quantity
            item_info["costToBuy"] += quantity
            return True

    if normalized_input_item in bazaar_data["products"]:
        product_data = bazaar_data["products"][normalized_input_item]
        sell_price = product_data["quick_status"]["sellPrice"]
        buy_price = product_data["quick_status"]["buyPrice"]
        id_to_name = {item['id']: item['name'] for item in names_data}
        if normalized_input_item in id_to_name:
            nameClear = remove_color_codes(id_to_name[normalized_input_item])
        

        if not search_main:
            item_info["inputs"].append({
                "name": normalized_input_item,
                "nameClear": nameClear,
                "found_in": "bazaar",
                "quantity": quantity,
                "sell_price": (quantity * float(sell_price)),
                "buy_price": (quantity * float(buy_price))
            })
            item_info["sellTheItemsPrice"] += (quantity * sell_price)
            item_info["costToBuy"] += (quantity * buy_price)
        else:
            item_info["FinalPriceSell"] = sell_price
            item_info["FinalItemFoundIn"] = "bazaar"
        return True
    return False



def remove_reforge_prefix(item_name):
    for reforge in reforges_data.values():
        reforge_name = reforge["reforgeName"]
        if item_name.startswith(reforge_name):
            return item_name[len(reforge_name):].strip()
    return item_name

def find_item_in_auction(input_item, item_info, search_main):
    if not search_main:
        split_item = input_item.split(":")
        normalized_input_item = split_item[0]
        quantity = float(split_item[1])
    else:
        normalized_input_item = input_item
        quantity = 1

    found_in_auctions = False
    lowest_starting_bid = float('inf')
    item_name_auction = ""

    for ah_item in names_data:
        if normalized_input_item == ah_item.get("id"):
            item_name_auction = remove_color_codes(ah_item.get("name"))

    matching_auctions = [
    auction for auction in auctions_data
    if item_name_auction in auction.get("item_name", "") and auction.get("bin") == is_bin
]

    for auction in matching_auctions:
        if auction.get("starting_bid", float('inf')) < lowest_starting_bid:
            lowest_starting_bid = auction["starting_bid"]
            found_in_auctions = True

    if found_in_auctions:
        if not search_main:
            id_to_name = {item['id']: item['name'] for item in names_data}
            if normalized_input_item in id_to_name:
                nameClear = remove_color_codes(id_to_name[normalized_input_item])
            item_info["inputs"].append({
                "name": normalized_input_item,
                "nameClear": nameClear,
                "found_in": "auctions",
                "quantity": quantity,
                "sell_price": lowest_starting_bid,
                "buy_price": lowest_starting_bid
            })
            item_info["sellTheItemsPrice"] += (quantity * lowest_starting_bid)
            item_info["costToBuy"] += (quantity * lowest_starting_bid)
        else:
            item_info["FinalPriceSell"] = lowest_starting_bid
            item_info["FinalItemFoundIn"] = "auction"
        return True
    return False

def search_main_item(input_item, item_info, search_main):
    if not find_item_in_bazaar(input_item, item_info, search_main):
        if not find_item_in_auction(input_item, item_info, search_main):
            if not search_main:
                split_item = input_item.split(":")
                normalized_input_item = split_item[0]
                quantity = float(split_item[1])

                id_to_name = {item['id']: item['name'] for item in names_data}
                if normalized_input_item in id_to_name:
                    nameClear = remove_color_codes(id_to_name[normalized_input_item])


                item_info["inputs"].append({
                    "name": normalized_input_item,
                    "nameClear": nameClear,
                    "found_in": "none",
                    "quantity": quantity,
                    "sell_price": "price not found",
                    "buy_price": "price not found"
                })
            else:
                normalized_input_item = input_item
                quantity = 1
def extract_number(s):
    return ''.join(filter(str.isdigit, s))
async def start_calculation():
    await load_jsons()
    for desired_internalname in desired_internalnames:
        for item in items_data:
            if item.get("internalname") == desired_internalname and item.get("recipes"):
                recipe = item["recipes"][0]
                inputs = recipe.get("inputs", [])

                craft_number = extract_number(item["crafttext"])
                if craft_number.isdigit():
                    craft_number = int(craft_number)
                    if 1 <= craft_number <= 200:
                        itemHOTM = craft_number
                    else:
                        itemHOTM = 0
                else:
                    itemHOTM = 0
                normalized_input_item = item["internalname"]
                id_to_name = {item['id']: item['name'] for item in names_data}
                if normalized_input_item in id_to_name:
                    normalized_input_item = remove_color_codes(id_to_name[normalized_input_item])
                item_info = {
                    "internalname": item["internalname"],
                    "name": normalized_input_item,
                    "inputs": [],
                    "costToBuy": 0,
                    "sellTheItemsPrice": 0,
                    "FinalPriceSell": 0,
                    "HOTM": itemHOTM,
                    "timeToMake": recipe.get("duration"),
                    "FinalItemFoundIn": ""
                }

                for input_item in inputs:
                    search_main_item(input_item, item_info, False)

                search_main_item(desired_internalname, item_info, True)

                output["items"].append(item_info)
                

    os.makedirs('DataAPI', exist_ok=True)
    output["lastTimeUpdate"] = time.time()
    async with aiofiles.open('DataAPI/dataprice.json', 'w') as json_file:
        await json_file.write(json.dumps(output, indent=4))


