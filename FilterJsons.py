import json
import os
import re
import asyncio
import aiofiles
import time
import calculatePriceToBuy
import PullAPI

price_json_path = "./DataAPI/dataprice.json"
price_data = {}

async def load_json(path):
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return json.loads(await f.read())
    except FileNotFoundError:
        print(f"File {path} not found.")
        return {}

async def load_jsons():
    global price_data
    price_data = await load_json(price_json_path)

def filter_items_and_sort(hotm_value, willing_to_pay, minProfit, bazaar_cut, auction_cut):
    filtered_items = []
    hotm_range = set(map(str, range(int(hotm_value))))
    
    for item in price_data.get('items', []):
        if str(item.get('HOTM', '')) in hotm_range and item.get('costToBuy', float('inf')) <= willing_to_pay:

            try:
                final_price_sell = float(item.get('FinalPriceSell', 0))
                cost_to_buy = float(item.get('costToBuy', 0))
                profit = final_price_sell - cost_to_buy
                
                if profit >= minProfit and final_price_sell > 0:
                    ahprofit =profit * (auction_cut if item.get("FinalItemFoundIn") == "auction" else bazaar_cut)
                    item['profit'] = ahprofit
                    item['profitperms'] = ahprofit / item.get('timeToMake')
                    filtered_items.append(item)
            except ValueError:
                print(f"Skipping item due to invalid data: {item}")
    
    return sorted(filtered_items, key=lambda x: x['profit'], reverse=True)

async def startfilter(htomlv, budget, minprofit, bzcut, auction_cut):
    await load_jsons()
    
    if time.time() - price_data.get("lastTimeUpdate", 0) >= 300:
        await PullAPI.UpdateAPI()
        await calculatePriceToBuy.start_calculation()
        await load_jsons()
    
    filtered_items = filter_items_and_sort(htomlv, budget, minprofit, bzcut, auction_cut)
    return filtered_items


# if __name__ == "__main__":
#     async def main():
#         filtered_items = await startfilter(2, 10000000, 100000, 0.99, 0.97)
#         print(filtered_items)

#     asyncio.run(main())
