import tkinter as tk
from tkinter import ttk
import asyncio
import threading
import os
import subprocess
import FilterJsons
import UpdateForgeData

class DarkApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Dark Themed App")
        self.root.configure(bg='darkgray')

        self.initial_htomlv = 10
        self.initial_budget = 1000000
        self.initial_minprofit = 0
        self.initial_bzcut = 0.99
        self.initial_auction_cut = 0.97

        self.filtered_items = []

        style = ttk.Style()

        style.configure("TEntry",
                        background="darkgray",
                        foreground="black",
                        font=("Helvetica", 10),
                        borderwidth=1)

        style.configure("TButton",
                        background="darkgray",
                        foreground="black",
                        font=("Helvetica", 10),
                        borderwidth=1)

        self.htomlv_entry = None
        self.budget_entry = None
        self.minprofit_entry = None
        self.bzcut_entry = None
        self.auction_cut_entry = None

        self.create_label_and_entry("Htomlv:", self.initial_htomlv)
        self.create_label_and_entry("Budget:", self.initial_budget)
        self.create_label_and_entry("Minprofit:", self.initial_minprofit)
        self.create_label_and_entry("Bzcut:", self.initial_bzcut)
        self.create_label_and_entry("Auction Cut:", self.initial_auction_cut)

        self.filter_button = ttk.Button(self.root, text="Daten filtern", command=self.start_filter, style="TButton")
        self.filter_button.pack(pady=10)

        self.tree = ttk.Treeview(self.root, columns=("Internal Name", "Inputs", "Final Price", "Time to Make", "Profit", 'ProfitperMs'), show='headings')
        self.tree.heading("Internal Name", text="Internal Name")
        self.tree.heading("Inputs", text="Inputs")
        self.tree.heading("Final Price", text="Final Price")
        self.tree.heading("Time to Make", text="Time to Make")
        self.tree.heading("Profit", text="Profit", command=self.sort_by_last_column)
        self.tree.heading("ProfitperMs", text="ProfitperMs", command=self.sort_by_last_column)
        self.tree.pack(padx=10, pady=10, expand=tk.YES, fill=tk.BOTH)

        self.tree.bind("<ButtonRelease-1>", self.on_tree_select)

    def create_label_and_entry(self, label_text, initial_value):
       
        label = ttk.Label(self.root, text=label_text)
        label.configure(background='darkgray', foreground='white', font=("Helvetica", 10))
        label.pack(pady=5, padx=10, anchor="w")

        
        entry = ttk.Entry(self.root, style="TEntry")
        entry.insert(0, str(initial_value))
        entry.pack(pady=5, padx=10, fill=tk.X)

        
        if label_text.startswith("Htomlv"):
            self.htomlv_entry = entry
        elif label_text.startswith("Budget"):
            self.budget_entry = entry
        elif label_text.startswith("Minprofit"):
            self.minprofit_entry = entry
        elif label_text.startswith("Bzcut"):
            self.bzcut_entry = entry
        elif label_text.startswith("Auction Cut"):
            self.auction_cut_entry = entry

    def start_filter(self):
        htomlv_value = int(self.htomlv_entry.get())
        budget_value = float(self.budget_entry.get())
        minprofit_value = int(self.minprofit_entry.get())
        bzcut_value = float(self.bzcut_entry.get())
        auction_cut_value = float(self.auction_cut_entry.get())

       
        threading.Thread(target=self.run_filter_threaded, args=(htomlv_value, budget_value, minprofit_value, bzcut_value, auction_cut_value)).start()

    def run_filter_threaded(self, htomlv, budget, minprofit, bzcut, auction_cut):
        
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_filter(htomlv, budget, minprofit, bzcut, auction_cut))
        loop.close()

    async def run_filter(self, htomlv, budget, minprofit, bzcut, auction_cut):
        print("Filter wird gestartet mit Parametern:", htomlv, budget, minprofit, bzcut, auction_cut)
        try:
            self.filtered_items.clear()
            self.filtered_items = await FilterJsons.startfilter(htomlv, budget, minprofit, bzcut, auction_cut)
            self.update_treeview(self.filtered_items)
        except Exception as e:
            print(f"Fehler beim Filtern: {e}")

    def sort_by_last_column(self):
        data = [(self.tree.set(child, "Internal Name"), self.tree.set(child, "Inputs"),
                 self.tree.set(child, "Final Price"), self.tree.set(child, "Time to Make"),
                 self.tree.set(child, "Profit")) for child in self.tree.get_children('')]

        data.sort(key=lambda t: float(t[4]), reverse=True)

        for item in self.tree.get_children():
            self.tree.delete(item)

        for item in data:
            self.tree.insert('', 'end', values=item)

    def update_treeview(self, filtered_items):
        for item in self.tree.get_children():
            self.tree.delete(item)

        for item in filtered_items:
            inputs_names = ", ".join(input['name'] for input in item['inputs'])
            self.tree.insert('', 'end', values=(item['internalname'], inputs_names, item['FinalPriceSell'], item['timeToMake'], item['profit'], item['profitperms']))

    def on_tree_select(self, event):
        item_id = self.tree.identify_row(event.y)
        if item_id:
            item = self.tree.item(item_id)
            inputs = item['values'][1].split(', ')

            detail_window = tk.Toplevel(self.root)
            detail_window.title("Details der Inputs")
            detail_window.configure(bg='darkgray')

            detail_tree = ttk.Treeview(detail_window, columns=("Name", "Found In", "Quantity", "Buy Price"), show='headings')
            detail_tree.heading("Name", text="Name")
            detail_tree.heading("Found In", text="Found In")
            detail_tree.heading("Quantity", text="Quantity")
            detail_tree.heading("Buy Price", text="Buy Price")
            detail_tree.pack(padx=10, pady=10, expand=tk.YES, fill=tk.BOTH)

            for filtered_item in self.filtered_items:
                if filtered_item['internalname'] == item['values'][0]:
                    for input_data in filtered_item['inputs']:
                        detail_tree.insert('', 'end', values=(input_data['name'], input_data["found_in"], input_data['quantity'], input_data['buy_price']))

    def run(self):
        self.root.mainloop()

async def create_delete_bat_and_run_app():
    try:
        if not os.path.exists("delete.bat"):
            with open("delete.bat", "w") as f:
                f.write("@echo off\n")
                f.write("rmdir /s /q .\\NotEnoughUpdates-REPO\\.git\n")
            await UpdateForgeData.UpdateForge()
    except Exception as e:
        print(f"Fehler bei der Ausführung von UpdateForge: {e}")

def start_app():
    root = tk.Tk()
    app = DarkApp(root)
    app.run()

def check_and_run_app():
    asyncio.run(create_delete_bat_and_run_app())
    start_app()

if __name__ == "__main__":
    check_and_run_app()
