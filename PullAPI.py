import asyncio
import aiohttp
import aiofiles
import json
import os

async def save_data_to_json(url, filename):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()

        async with aiofiles.open(f'DataAPI/{filename}.json', 'w') as json_file:
            await json_file.write(json.dumps(data, indent=4))
        
        print(f"Daten erfolgreich in '{filename}.json' gespeichert.")

    except aiohttp.ClientError as e:
        print(f"Fehler beim Abrufen der Daten von {url}: {e}")

    except json.JSONDecodeError as e:
        print(f"Fehler beim Verarbeiten der JSON-Daten von {url}: {e}")

    except OSError as e:
        print(f"Fehler beim Schreiben der Datei '{filename}.json': {e}")

async def ActionRequest(session):
    try:
        base_URL = "https://api.hypixel.net/skyblock/auctions?page="
        first_response = await session.get(base_URL + "0")
        first_response.raise_for_status()
        data = await first_response.json()
        
        pageCount = int(data["totalPages"]) - 1
        
       
        folder_path = './DataAPI/Auctions'
        os.makedirs(folder_path, exist_ok=True)
        
        tasks = []
        for i in range(pageCount + 1):
            url = base_URL + str(i)
            output = {"auctions": []}
            tasks.append(fetch_auction_data(session, url, output, folder_path, i))

        await asyncio.gather(*tasks)
        print("Alle Auktionsdaten erfolgreich gespeichert.")

    except aiohttp.ClientError as e:
        print(f"Fehler beim Abrufen der Auktionsdaten: {e}")

    except json.JSONDecodeError as e:
        print(f"Fehler beim Verarbeiten der JSON-Daten: {e}")

    except OSError as e:
        print(f"Fehler beim Schreiben der Datei: {e}")

async def fetch_auction_data(session, url, output, folder_path, page_number):
    try:
        async with session.get(url) as response:
            response.raise_for_status()
            data = await response.json()
            
            # Dateipfad für die JSON-Datei erstellen
            file_path = os.path.join(folder_path, f'ActiveAuction_{page_number}.json')
            
            async with aiofiles.open(file_path, 'w') as json_file:
                await json_file.write(json.dumps(data, indent=4))
            
            print(f"Auktionsdaten für Seite {page_number} erfolgreich in '{file_path}' gespeichert.")

    except aiohttp.ClientError as e:
        print(f"Fehler beim Abrufen der Auktionsdaten für Seite {page_number}: {e}")

    except json.JSONDecodeError as e:
        print(f"Fehler beim Verarbeiten der JSON-Daten für Seite {page_number}: {e}")

    except OSError as e:
        print(f"Fehler beim Schreiben der Datei für Seite {page_number}: {e}")



async def startCollecting():
    urls = {
        "Collections": "https://api.hypixel.net/v2/resources/skyblock/collections",
        "Bazaar": "https://api.hypixel.net/v2/skyblock/bazaar",
        "EndedAuction": "https://api.hypixel.net/v2/skyblock/auctions_ended",
        "Items": "https://api.hypixel.net/v2/resources/skyblock/items"
    }

    async with aiohttp.ClientSession() as session:
        tasks = [save_data_to_json(url, key) for key, url in urls.items()]
        await asyncio.gather(*tasks)
        await ActionRequest(session)

async def UpdateAPI():
    try:
        await startCollecting()
        return True
    except Exception as e:
        print(f"Fehler beim Aktualisieren der Daten: {e}")
        return False

async def main():
    async with aiohttp.ClientSession() as session:
        await ActionRequest(session)
        
        
    if await UpdateAPI():
        print("Daten erfolgreich aktualisiert.")
    else:
        print("Fehler beim Aktualisieren der Daten.")

