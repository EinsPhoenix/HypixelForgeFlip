import os
import json
import RecipiePull
import PullAPI
import os
import shutil
import asyncio
import calculatePriceToBuy


json_folder = './downloaded_items'
output_file = 'forgableitems.json'
item_file = './DataAPI/Items.json'

outputFolder = "./ForgeData"

def collect_forgable_items(directory):
    forgable_items = []

    for filename in os.listdir(directory):
        if filename.endswith('.json'):
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='utf-8') as file:
                try:
                    data = json.load(file)
                   
                    if "recipes" in data:
                        for recipe in data["recipes"]:
                            if recipe.get("type") == "forge":
                                if "crafttext" not in data or not data["crafttext"]:
                                    
                                    internalname = data["internalname"]
                                    found_item = None
                                    
                                   
                                    with open(item_file, 'r', encoding='utf-8') as item_file_data:
                                        items_data = json.load(item_file_data)
                                        items_list = items_data.get("items", [])
                                        
                                       
                                        for item in items_list:
                                            if item["id"] == internalname:
                                                found_item = item
                                                break
                                    
                                    
                                    if found_item:
                                        requirements = found_item.get("requirements", [])
                                        requirement_texts = []
                                        for requirement in requirements:
                                            if requirement["type"] == "HEART_OF_THE_MOUNTAIN":
                                                requirement_texts.append(f"{requirement['type']} {requirement['tier']}")
                                        
                                        craft_text = f"Requires: {', '.join(requirement_texts)}"
                                        data["crafttext"] = craft_text
                                        forgable_items.append(data)
                                    else:
                                        
                                        forgable_items.append(data)
                                else:
                                    forgable_items.append(data)
                except json.JSONDecodeError:
                    print(f"Fehler beim Laden der JSON-Datei: {filepath}")

    output_path = os.path.join(outputFolder, 'forgable_items.json')
    with open(output_path, 'w', encoding='utf-8') as outfile:
        json.dump(forgable_items, outfile, ensure_ascii=False, indent=4)
    print(f"Gesammelte Daten wurden in {output_path} gespeichert.")




def create_or_clear_folder(folder_name):
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
        print(f"Ordner '{folder_name}' erstellt.")
    else:
        print(f"Ordner '{folder_name}' vorhanden. Lösche Inhalte...")

       
        for filename in os.listdir(folder_name):
            file_path = os.path.join(folder_name, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Fehler beim Löschen der Datei {file_path}: {e}")

        print(f"Inhalte von '{folder_name}' gelöscht.")

def RestetFolders():
    folders_to_create_clear = ["DataAPI", "ForgeData"]

    for folder in folders_to_create_clear:
        create_or_clear_folder(folder)



async def UpdateForge():
    RestetFolders()
    await PullAPI.main()
    RecipiePull.update_recipes()
    collect_forgable_items(json_folder)
    await calculatePriceToBuy.start_calculation()


