import wx
import wx.grid as gridlib
import asyncio
import threading
import FilterJsons  
import UpdateForgeData  
import os
import NumberToAlph

class ForgeFlipper(wx.Frame):
    def __init__(self, *args, **kw):
        super(ForgeFlipper, self).__init__(*args, **kw)
        
        self.initialize_data()
        self.initialize_gui()

    def initialize_data(self):
        self.timer = None
        self.initial_htomlv = 10
        self.initial_budget = 1000000
        self.initial_minprofit = 0
        self.initial_bzcut = 0.99
        self.initial_auction_cut = 0.97
        self.filtered_items = []
        self.filter_keyword = ""  

    def initialize_gui(self):
        self.panel = wx.Panel(self)
        self.panel.SetBackgroundColour('#404040')  
        vbox = wx.BoxSizer(wx.VERTICAL)

        group_sizer = wx.BoxSizer(wx.HORIZONTAL)
        group_sizer1 = wx.BoxSizer(wx.HORIZONTAL)
        group_sizer2 = wx.BoxSizer(wx.HORIZONTAL)
        vpanel1 = wx.BoxSizer(wx.VERTICAL)
        vpanel2 = wx.BoxSizer(wx.VERTICAL)
        
        ButtonH = wx.BoxSizer(wx.HORIZONTAL)
        SearchH = wx.BoxSizer(wx.HORIZONTAL)

        
        self.htomlv_dropdown = self.create_label_and_dropdown("Hotmlv:", self.initial_htomlv, vpanel1)
        group_sizer1.Add(vpanel1, proportion=1, flag=wx.EXPAND| wx.LEFT | wx.RIGHT, border=10)

       
        self.budget_entry = self.create_label_and_entry("Budget:", self.initial_budget, vpanel1)
        self.minprofit_entry = self.create_label_and_entry("Minprofit:", self.initial_minprofit, vpanel1)

       
        self.bzcut_entry = self.create_label_and_entry("Bzcut:", self.initial_bzcut, vpanel2)
        self.auction_cut_entry = self.create_label_and_entry("Auction Cut:", self.initial_auction_cut, vpanel2)

        group_sizer2.Add(vpanel2, proportion=1, flag=wx.EXPAND| wx.LEFT | wx.RIGHT, border=10)

       
        group_sizer.Add(group_sizer1, proportion=1, flag=wx.EXPAND| wx.LEFT | wx.RIGHT, border=30)
        group_sizer.Add(group_sizer2, proportion=1, flag=wx.EXPAND| wx.LEFT | wx.RIGHT, border=30)

        vbox.Add(group_sizer, proportion=1, flag=wx.EXPAND| wx.ALL,border=10)

       
        filter_button = wx.Button(self.panel, label="Flip")
        filter_button.SetBackgroundColour('#505050')
        filter_button.SetForegroundColour('#404040')
        filter_button.Bind(wx.EVT_BUTTON, self.start_filter)
        ButtonH.Add(filter_button,proportion=1,flag=wx.EXPAND| wx.LEFT| wx.RIGHT, border=60)
        vbox.Add(ButtonH, proportion=1,flag=wx.ALL | wx.CENTER |wx.EXPAND)

       
        search_label = wx.StaticText(self.panel, label="Suche:")
        search_label.SetForegroundColour('white')
        vbox.Add(search_label, flag=wx.LEFT , border=60)
        self.search_entry = wx.TextCtrl(self.panel)
        self.search_entry.SetBackgroundColour('#505050')
        self.search_entry.SetForegroundColour('white')
        self.search_entry.Bind(wx.EVT_TEXT, self.on_search)
        
        SearchH.Add(self.search_entry,proportion=1,flag=wx.EXPAND| wx.LEFT| wx.RIGHT, border = 60)
        vbox.Add(SearchH, proportion=1,flag=wx.ALL | wx.LEFT |wx.EXPAND)

        
        self.grid = gridlib.Grid(self.panel)
        self.grid.CreateGrid(0, 6)
        self.grid.SetColLabelValue(0, "Name")
        self.grid.SetColLabelValue(1, "Items You Need")
        self.grid.SetColLabelValue(2, "Item sells for")
        self.grid.SetColLabelValue(3, "Time to Make")
        self.grid.SetColLabelValue(4, "Profit")
        self.grid.SetColLabelValue(5, "Profit per Sec")
        self.grid.Bind(gridlib.EVT_GRID_LABEL_LEFT_CLICK, self.on_sort_column)
        self.grid.Bind(gridlib.EVT_GRID_CELL_LEFT_CLICK, self.show_item_details)
        self.grid.Bind(gridlib.EVT_GRID_CELL_RIGHT_CLICK, self.on_hover_cell)

        self.grid.SetDefaultCellBackgroundColour('#303030')
        self.grid.SetDefaultCellTextColour('white')
        self.grid.SetLabelBackgroundColour('#404040')
        self.grid.SetLabelTextColour('white')
        self.grid.EnableEditing(False)
        self.grid.SetGridLineColour(wx.Colour(190, 190, 190))
        self.grid.SetDefaultCellFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))

        

        cell_attr = gridlib.GridCellAttr()
        cell_attr.SetBackgroundColour('#303030')
        cell_attr.SetAlignment(wx.ALIGN_CENTER, wx.ALIGN_CENTER)
        cell_attr.SetFont(wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))

        for col in range(6):
            self.grid.SetColAttr(col, cell_attr.Clone())

        vbox.Add(self.grid, 2, flag=wx.EXPAND | wx.ALL, border=10)

        
        self.detail_panel = wx.Panel(self.panel)
        self.detail_panel.SetBackgroundColour('#303030')
        detail_sizer = wx.BoxSizer(wx.VERTICAL)
        self.detail_grid = gridlib.Grid(self.detail_panel)
        self.detail_grid.CreateGrid(0, 5)
        self.detail_grid.SetColLabelValue(0, "Name")
        self.detail_grid.SetColLabelValue(1, "Found In")
        self.detail_grid.SetColLabelValue(2, "Quantity")
        self.detail_grid.SetColLabelValue(3, "Buy Price")
        self.detail_grid.SetColLabelValue(4, "Number in Word")
        self.detail_grid.SetDefaultCellBackgroundColour('#404040')
        self.detail_grid.SetDefaultCellTextColour('#404040')
        self.detail_grid.EnableEditing(False)
        detail_sizer.Add(self.detail_grid, 2, flag=wx.EXPAND | wx.ALL, border=20)
        self.detail_panel.SetSizer(detail_sizer)
        self.detail_panel.Hide()

        vbox.Add(self.detail_panel, 0, flag=wx.EXPAND | wx.BOTTOM, border=20)
        self.panel.SetSizer(vbox)
        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.SetSize((800, 600))
        self.SetBackgroundColour('#404040')
        self.Show(True)


    def create_label_and_entry(self, label_text, initial_value, sizer):
        
        vertical_box = wx.BoxSizer(wx.VERTICAL)
        
       
        label = wx.StaticText(self.panel, label=label_text)
        label.SetForegroundColour('white')
        vertical_box.Add(label, flag=wx.RIGHT, border=8)
      
        entry = wx.TextCtrl(self.panel, value=str(initial_value))
        entry.SetBackgroundColour('#505050')
        entry.SetForegroundColour('white')
        
       
        vertical_box.Add(entry, proportion=0, flag=wx.EXPAND| wx.LEFT | wx.RIGHT)
        sizer.Add(vertical_box, proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        
        return entry

    def create_label_and_dropdown(self, label_text, initial_value, sizer):
        vbox = wx.BoxSizer(wx.VERTICAL)
        label = wx.StaticText(self.panel, label=label_text)
        label.SetForegroundColour('white')
        vbox.Add(label, flag=wx.RIGHT, border=8)

        choices = [str(i) for i in range(11)]
        dropdown = wx.ComboBox(self.panel, choices=choices, style=wx.CB_DROPDOWN)
        dropdown.SetValue(str(initial_value))
        dropdown.SetBackgroundColour('#505050')
        dropdown.SetForegroundColour('white')
        vbox.Add(dropdown, proportion=0,flag=wx.EXPAND| wx.LEFT | wx.RIGHT)
        sizer.Add(vbox,proportion=0, flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=10)
        
        return dropdown

    def start_filter(self, event):
       
        self.filter_keyword = self.search_entry.GetValue().strip()  
        htomlv_value = int(self.htomlv_dropdown.GetValue())
        budget_value = float(self.budget_entry.GetValue())
        minprofit_value = int(self.minprofit_entry.GetValue())
        bzcut_value = float(self.bzcut_entry.GetValue())
        auction_cut_value = float(self.auction_cut_entry.GetValue())
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
            filtered_items = self.apply_search_filter(self.filtered_items, self.filter_keyword)
            wx.CallAfter(self.update_grid, filtered_items)
        except Exception as e:
            print(f"Fehler beim Filtern: {e}")

    def apply_search_filter(self, items, keyword):
        
        if not keyword:
            return items

        filtered_items = []
        keyword_lower = keyword.lower() 
        for item in items:
            if keyword_lower in item['internalname'].lower():
                filtered_items.append(item)

        return filtered_items

    def update_grid(self, filtered_items):
      
        self.grid.ClearGrid()
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())

        for item in filtered_items:
            self.grid.AppendRows(1)
            inputs_names = ", ".join(input['name'] for input in item['inputs'])
            self.grid.SetCellValue(self.grid.GetNumberRows() - 1, 0, item['name'])
            self.grid.SetCellValue(self.grid.GetNumberRows() - 1, 1, inputs_names)
            self.grid.SetCellValue(self.grid.GetNumberRows() - 1, 2, str(item['FinalPriceSell']))
            self.grid.SetCellValue(self.grid.GetNumberRows() - 1, 3, str(item['timeToMake']/60))
            self.grid.SetCellValue(self.grid.GetNumberRows() - 1, 4, str(item['profit']))
            

            self.grid.SetCellValue(self.grid.GetNumberRows() - 1, 5, str(item['profitperms']))
            for col in range(8):
                self.grid.SetCellBackgroundColour(self.grid.GetNumberRows() - 1, col, '#303030')  
                self.grid.SetCellTextColour(self.grid.GetNumberRows() - 1, col, 'white')  
                self.grid.SetCellFont(self.grid.GetNumberRows() - 1, col, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))  

        self.grid.AutoSizeColumns()
        self.adjust_column_sizes()

    def adjust_column_sizes(self):
        total_width = self.grid.GetSize().GetWidth()
        self.grid.AutoSizeColumns()

        num_cols = self.grid.GetNumberCols()
        remaining_width = total_width - sum(self.grid.GetColSize(col) for col in range(1, num_cols - 1))

        if remaining_width > 0:
            first_col_width = remaining_width // 2
            last_col_width = remaining_width - first_col_width
            self.grid.SetColSize(0, first_col_width)
            self.grid.SetColSize(num_cols - 1, last_col_width)


    def on_resize(self, event):
       
        self.Layout()
        self.adjust_column_sizes()
        event.Skip()

    def on_sort_column(self, event):
        
        col = event.GetCol()
        data = []
        for row in range(self.grid.GetNumberRows()):
            row_data = []
            for col_index in range(self.grid.GetNumberCols()):
                row_data.append(self.grid.GetCellValue(row, col_index))
            data.append(tuple(row_data))

        if col < len(data[0]):
            try:
                data.sort(key=lambda t: float(t[col]), reverse=True)
            except ValueError:
                data.sort(key=lambda t: t[col], reverse=True)

        self.grid.ClearGrid()
        if self.grid.GetNumberRows() > 0:
            self.grid.DeleteRows(0, self.grid.GetNumberRows())

        for item in data:
            self.grid.AppendRows(1)
            for col_index, value in enumerate(item):
                self.grid.SetCellValue(self.grid.GetNumberRows() - 1, col_index, value)
                self.grid.SetCellBackgroundColour(self.grid.GetNumberRows() - 1, col_index, '#303030')  
                self.grid.SetCellTextColour(self.grid.GetNumberRows() - 1, col_index, 'white') 
                self.grid.SetCellFont(self.grid.GetNumberRows() - 1, col_index, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL)) 

        self.grid.AutoSizeColumns()
        self.adjust_column_sizes()

    def show_item_details(self, event):
        
        if not hasattr(event, 'GetRow'):
            return
        
        row = event.GetRow()
        item_internalname = self.grid.GetCellValue(row, 0)

        self.detail_grid.ClearGrid()
        if self.detail_grid.GetNumberRows() > 0:
            self.detail_grid.DeleteRows(0, self.detail_grid.GetNumberRows())

        for filtered_item in self.filtered_items:
            if filtered_item['name'] == item_internalname:
                for input_data in filtered_item['inputs']:
                    self.detail_grid.AppendRows(1)
                    last_row = self.detail_grid.GetNumberRows() - 1
                    if not(input_data['nameClear']):
                        self.detail_grid.SetCellValue(last_row, 0, input_data['name'])
                    else:
                        self.detail_grid.SetCellValue(last_row, 0, input_data['nameClear'])
                    self.detail_grid.SetCellValue(last_row, 1, input_data['found_in'])
                    self.detail_grid.SetCellValue(last_row, 2, str(input_data['quantity']))
                    self.detail_grid.SetCellValue(last_row, 3, str(input_data['buy_price']))
                    self.detail_grid.SetCellValue(last_row, 4, str(NumberToAlph.number_to_words(str(input_data['buy_price']))))
                    for col in range(5):
                        self.detail_grid.SetCellBackgroundColour(last_row, col, '#404040')
                        self.detail_grid.SetCellTextColour(last_row, col, 'white')
                        self.detail_grid.SetCellFont(last_row, col, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.NORMAL))

                self.detail_grid.AppendRows(1)
                last_row = self.detail_grid.GetNumberRows() - 1
                self.detail_grid.SetCellValue(last_row, 0, filtered_item['name'])
                self.detail_grid.SetCellValue(last_row, 1, "Price to buy Overall")
                self.detail_grid.SetCellValue(last_row, 2, "1")
                self.detail_grid.SetCellValue(last_row, 3, str(filtered_item['costToBuy']))
                self.detail_grid.SetCellValue(last_row, 4, str(NumberToAlph.number_to_words(filtered_item['costToBuy'])))

                for col in range(5):
                    self.detail_grid.SetCellBackgroundColour(last_row, col, '#404040')
                    self.detail_grid.SetCellTextColour(last_row, col, 'Red')
                    self.detail_grid.SetCellFont(last_row, col, wx.Font(10, wx.DEFAULT, wx.NORMAL, wx.BOLD))

        
        self.detail_grid.AutoSizeColumns()

        self.detail_panel.Show()
        self.panel.Layout()

        
        self.detail_panel.Show()
        self.panel.Layout()
    def on_search(self, event):
        
            self.filter_keyword = self.search_entry.GetValue().strip().lower()  
            filtered_items = self.apply_search_filter(self.filtered_items, self.filter_keyword)
            self.update_grid(filtered_items)
    def on_hover_cell(self, event):
        
        row = event.GetRow()
        col = event.GetCol()
        if row != -1 and col in [2,3,4, 5]: 
            if self.timer:
                event.Skip() 
            cell_value = self.grid.GetCellValue(row, col)
            try:
                cell_value = float(cell_value)
            except:
                cell_value = str(cell_value)
            if isinstance(cell_value, float):
                tooltip_text = NumberToAlph.number_to_words(str(cell_value))
        
                self.grid.SetCellValue(row, col, tooltip_text)
            
          
                self.timer = threading.Timer(10.0, lambda: self.revert_cell_value(row, col, str(cell_value)))
                self.timer.start()
                self.grid.AutoSizeColumns()
                self.adjust_column_sizes()
        else:
            event.Skip()

    def revert_cell_value(self, row, col, original_value):
        
        wx.CallAfter(self.grid.SetCellValue, row, col, original_value)




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
    app = wx.App(False)
    frame = ForgeFlipper(None, title="ForgeFlipper")
    app.MainLoop()

def check_and_run_app():
    asyncio.run(create_delete_bat_and_run_app())
    start_app()

if __name__ == "__main__":
    check_and_run_app()



