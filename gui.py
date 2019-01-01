import builtins
import tkinter as tk
import numpy as np
import math
import matplotlib
import os
import time
import threading
matplotlib.use("TkAgg")
import matplotlib.font_manager as font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

PWD      = os.path.dirname(os.path.realpath(__file__))
Fontpath = os.environ['WINDIR']+'\\Fonts\\NotoSansCJKtc-Regular.otf'

class GUI:
  # Object initialization
  def __init__(self):
    self.init_props()
    self.create_app()
    self.create_frames()
    self.create_text()
    self.create_items()
    self.init_graphic()

  def init_props(self):
    self.font     = FontProperties(fname=Fontpath, size=16)
    self.font_s   = FontProperties(fname=Fontpath, size=12)
    self.keywords = {
      '食': ['食','飲','餐','滷','飯','麵','咖啡','水','湯','乳','奶','酒','蛋','薯','雞','茶',
        '冰','糖','油品','餅','火鍋','菜','漿','餃'],
      '衣': ['褲','衣','服'],
      '行': ['汽油','石油','柴油','車'],
      '娛樂': ['菸','網路','妝','數位','3C','書','遊戲','美容','票','玩','點數'],
      '規費': ['費','業務','服務','租'],
    }

  def init_categoty(self):
    self.category = {
      '食': 0,
      '衣': 0,
      '行': 0,
      '娛樂': 0,
      '規費': 0,
      '雜項': 0
    }
  # Create interface
  def create_app(self):
    self.app = tk.Tk()
    self.app.title("Invoice Analyze")
    self.app.protocol("WM_DELETE_WINDOW", self.terminate)
    self.app.geometry("1024x768")

  def create_frames(self):
    self.input_frame = tk.Frame(self.app)
    self.input_frame.pack()

  def create_text(self):
    self.text = {}
    texts = ["Start date", "End date"]
    for txt in texts:
      key = txt.lower().replace(' ', '_')
      self.text[key] = tk.StringVar(self.app)
      self.text[key].set(txt)

  def create_items(self):
    self.create_dates()
    self.create_date_selections()
    self.create_hint_text()
    self.create_analyze_button()
    self.create_quit_button()

  def padding(self):
    return 32

  def str_to_tk_var(self, ss):
    re = tk.StringVar(self.app)
    re.set(ss)
    return re

  def create_dates(self):
    self.dates = []
    year  = [102, 107]
    month = [1, 9]
    for i in range(year[0], year[1]+1):
      start_month = month[0] if i == year[0] else 1
      end_month   = month[1] if i == year[1] else 12
      for j in range(start_month, end_month + 1, 2):
        self.dates.append("{}/{}".format(i, j))

  def create_date_selections(self):
    tk.Label(self.input_frame, text=" Start Date: ", borderwidth=1).grid(row=0,column=0)
    self.sdate_value = self.str_to_tk_var(self.dates[0])
    self.sdate_selection = tk.OptionMenu(self.input_frame, self.sdate_value, *self.dates)
    self.sdate_selection.grid(row=0, column=2)

    tk.Label(self.input_frame, text=" End Date: ", borderwidth=1).grid(row=1, column=0)
    self.edate_value = self.str_to_tk_var(self.dates[0])
    self.edate_selection = tk.OptionMenu(self.input_frame, self.edate_value, *self.dates)
    self.edate_selection.grid(row=1, column=2)

  def create_hint_text(self):
    self.hint_text = tk.Label(self.input_frame, text="Please wait while collecting data...")
    self.hint_text.grid(row=3, column=1)

  def update_hint(self, txt):
    self.hint_text.config(text=txt)

  def create_analyze_button(self):
    self.start_button = tk.Button(self.input_frame, text="Analyze", command=(lambda: self.on_command_analyze()), state='disabled')
    self.start_button.grid(row=4, column=0)

  def create_quit_button(self):
    self.quit_button = tk.Button(self.input_frame, text="Quit", command=(lambda: self.terminate()))
    self.quit_button.grid(row=4, column=2)

  def get_date(self):
    return [self.sdate_value.get(), self.edate_value.get()]

  def init_graphic(self):
    self.widget  = None
    self.toolbar = None

  def assign_data(self, data, data2):
    self.invoice_data  = data
    self.invoice_data2 = data2

  def on_command_analyze(self):
    print("Start analyze")
    print("Date duration: {}".format(self.get_date()))
    # draw the figure
    f = Figure(figsize=(10,5), dpi=100)
    self.bar_chart_a = f.add_subplot(211)
    a = self.bar_chart_a
    a.title.set_text("發票中獎分布圖")
    a.title.set_fontproperties(self.font_s)
    x, y, z = self.get_invoice_data(self.get_date()[0], self.get_date()[1])
    self.x_a = x
    self.y_a = y
    self.z_a = z
    w = 0.1
    a.bar(x, y, width=-w,color='b', align='edge', label='一千萬')
    a.bar(x, z, width=w,color='g', align='edge', label='兩百萬')
    
    for label in a.get_xticklabels():
      label.set_fontproperties(self.font_s)
      label.set_rotation(45)
    a.legend(loc='upper left',prop=self.font_s,framealpha=0.5)
    a.set_xlabel('縣市', fontproperties=self.font)
    a.set_ylabel('次數', fontproperties=self.font)

    self.init_categoty()
    self.calc_invoice_item(self.get_date()[0], self.get_date()[1])
    b = f.add_subplot(212)
    b.bar(list(self.category.keys()), list(self.category.values()))
    for label in b.get_xticklabels():
      label.set_fontproperties(self.font_s)
    b.set_xlabel('類別', fontproperties=self.font)
    b.set_ylabel('次數', fontproperties=self.font)
    f.tight_layout()

    if self.widget:
      self.widget.destroy()
      self.toolbar.destroy()
    # show this figure on this canvas
    canvas = FigureCanvasTkAgg(f, self.app)
    canvas.draw()
    self.widget = canvas.get_tk_widget()
    self.widget.pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)
    self.toolbar = NavigationToolbar2Tk(canvas, self.app)
    a.format_coord = self.format_coord
    b.format_coord = self.format_coord_cat
    self.toolbar.update()
    canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
    
  def format_coord(self, x, y):
    try:
      x_index = math.floor(x + 0.5)
    except Exception:
      x_index = -1
    x_index = min(x_index, len(self.x_a) - 1)
    if x_index < 0:
      return "No data selected"
    return "{}: 一千萬={} 兩百萬={}".format(self.x_a[x_index], self.y_a[x_index], self.z_a[x_index])

  def format_coord_cat(self, x, y):
    try:
      x_index = math.floor(x + 0.5)
    except Exception:
      x_index = -1
    x_index = min(x_index, len(self.category.keys()) - 1)
    if x_index < 0:
      return "No data selected"
    k = list(self.category.keys())[x_index]
    v = self.category[k]
    return "{}: {}".format(k, v)

  def start(self):
    print("App started")
    self.app.mainloop()

  def terminate(self):
    print("App terminated")
    builtins.singal_kill = True
    self.update_hint("Terminating web crawlers, please wait...")
    t = threading.Thread(target=self.close_app)
    t.start()

  def close_app(self):
    time.sleep(0.3)
    self.app.quit()

  def enableAnalyze(self):
    self.start_button.config(state='normal')
    self.update_hint("Ready to analyze!")

  def disableAnalyze(self, hint="Please wait..."):
    self.start_button.config(state='disabled')
    self.update_hint(hint)

  def calc_invoice_item(self, sd, ed):
    print(sd, ed)
    start = False
    for data, data2 in zip(self.invoice_data, self.invoice_data2):
      if data['timestamp'] == sd:
        start = True
      if start:
        for item_name in data['goods']:
          for cat in self.determine_category(item_name):
            self.category[cat] += 1
        for item_name in data2['goods']:
          for cat in self.determine_category(item_name):
            self.category[cat] += 1
      if data['timestamp'] == ed:
        start = False
  
  def determine_category(self, name):
    re = []
    for cat, words in self.keywords.items():
      for w in words:
        if w in name:
          re.append(cat)
          break
    if len(re) == 0:
      re.append('雜項') 
    return re
  
  def get_invoice_data(self, sd, ed):
    print(sd, ed)
    start = False
    re_x = []
    re_y = []
    re_z = []
    cnt  = {}
    cnt2 = {}
    for data, data2 in zip(self.invoice_data, self.invoice_data2):
      if data['timestamp'] == sd:
        start = True
      if start:
        for city in data['address']:
          key = city[:3]
          key = '桃園市' if key == '桃園縣' else key
          if key not in cnt:
            cnt[key] = 1
          else:
            cnt[key] += 1
        for city in data2['address']:
          key = city[:3]
          key = '桃園市' if key == '桃園縣' else key
          if key not in cnt2:
            cnt2[key] = 1
          else:
            cnt2[key] += 1
      if data['timestamp'] == ed:
        start = False
    
    re_x = sorted(list(set().union(cnt.keys(), cnt2.keys())))
    for k in re_x:
      v1 = 0
      v2 = 0
      if k in cnt:
        v1 += cnt[k]
      if k in cnt2:
        v2 += cnt2[k]
      re_y.append(v1)
      re_z.append(v2)
    print(re_x, re_y, re_z)
    return [re_x, re_y, re_z]