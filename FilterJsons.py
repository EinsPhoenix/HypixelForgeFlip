import json
import aiofiles
import time
import calculatePriceToBuy
import PullAPI

price_json_path = "./DataAPI/dataprice.json"
price_data = {}

async def load_json(path):
    """Load JSON data from a file asynchronously."""
    try:
        async with aiofiles.open(path, 'r', encoding='utf-8') as f:
            return json.loads(await f.read())
    except FileNotFoundError:
        print(f"File {path} not found.")
        return {}

async def load_jsons():
    """Load the price data from the JSON file."""
    global price_data
    price_data = await load_json(price_json_path)

def filter_items_and_sort(hotm_value, willing_to_pay, min_profit, bazaar_cut, auction_cut):
    """Filter items based on criteria and sort them by profit."""
    filtered_items = []
    hotm_range = set(range(int(hotm_value) + 1))

    for item in price_data.get('items', []):
        try:
            hotm_value_in_item = item.get('HOTM')
            if hotm_value_in_item is not None and isinstance(hotm_value_in_item, int):
                if hotm_value_in_item in hotm_range and float(item.get('costToBuy', float('inf'))) <= willing_to_pay:
                    final_price_sell = float(item.get('FinalPriceSell', 0))
                    cost_to_buy = float(item.get('costToBuy', 0))
                    profit = final_price_sell - cost_to_buy

                    if profit >= min_profit and final_price_sell > 0:
                        ah_profit = profit * (auction_cut if item.get("FinalItemFoundIn") == "auction" else bazaar_cut)
                        item['profit'] = ah_profit
                        item['profitperms'] = ah_profit / item.get('timeToMake', float('inf'))
                        filtered_items.append(item)
        except (ValueError, TypeError) as e:
            print(f"Skipping item due to invalid data: {item}. Error: {e}")

    return sorted(filtered_items, key=lambda x: x['profit'], reverse=True)

async def startfilter(htomlv, budget, minprofit, bzcut, auction_cut):
    """Load data, update if necessary, and filter items."""
    await load_jsons()

    # Check if data needs to be updated
    if time.time() - price_data.get("lastTimeUpdate", 0) >= 3:
        await PullAPI.UpdateAPI()
        await calculatePriceToBuy.start_calculation()
        await load_jsons()

    # Filter and sort items
    filtered_items = filter_items_and_sort(htomlv, budget, minprofit, bzcut, auction_cut)
    return filtered_items

# # Example of running the filter function
# if __name__ == "__main__":
#     async def main():
#         filtered_items = await start_filter(2, 10000000000000000, 100000, 0.99, 0.97)
#         print(filtered_items)
#     asyncio.run(main())
