import tkinter as tk
import time
import threading
import time
import urllib.request as urlrequest
import collections
import os
import numpy as np
import math
import matplotlib
import copy
import pickle
import math
matplotlib.use("TkAgg")
import matplotlib.font_manager as font_manager
from matplotlib.font_manager import FontProperties
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from selenium import webdriver
from urllib.parse import urlparse
from selenium.webdriver.chrome.options import Options

PWD      = os.path.dirname(os.path.realpath(__file__))
Fontpath = os.environ['WINDIR']+'\\Fonts\\NotoSansCJKtc-Regular.otf'
FileOut  = PWD + '\\out.txt'
Savefile = PWD + '\\save.dat'

font   = FontProperties(fname=Fontpath, size=16)
font_s = FontProperties(fname=Fontpath, size=12)
invoice_data  = []
invoice_data2 = []
source_url = "https://www.etax.nat.gov.tw/etw-main/web/ETW183W1/"
data = {}
workers = []
flag_data_ready = False
page_cnt = 7

def flatten(l, parent = []):
  for el in l:
    if el is l or el in parent:
      pass
    elif isinstance(el, collections.Iterable) and not isinstance(el, (str, bytes)):
      parent.append(l)
      yield from flatten(el, parent)
    else:
      yield el

app  = None
lock = threading.Lock()

class GUI:
  # Object initialization
  def __init__(self):
    self.create_app()
    self.create_frames()
    self.create_text()
    self.create_items()
    self.init_graphic()

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

  def on_command_analyze(self):
    print("Start analyze")
    print("Date duration: {}".format(self.get_date()))
    # draw the figure
    f = Figure(figsize=(10,5), dpi=100)
    self.bar_chart_a = f.add_subplot(211)
    a = self.bar_chart_a
    a.title.set_text("1000萬發票中獎分布圖")
    a.title.set_fontproperties(font_s)
    x, y, z = get_invoice_data(self.get_date()[0], self.get_date()[1])
    self.x_a = x
    self.y_a = y
    self.z_a = z
    w = 0.1
    a.bar(x, y, width=-w,color='b', align='edge', label='一千萬')
    a.bar(x, z, width=w,color='g', align='edge', label='兩百萬')
    
    for label in a.get_xticklabels():
      label.set_fontproperties(font_s)
      label.set_rotation(45)
    a.legend(loc='upper left',prop=font_s)
    a.set_xlabel('縣市', fontproperties=font)
    a.set_ylabel('次數', fontproperties=font)

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

  def start(self):
    print("App started")
    self.app.mainloop()

  def terminate(self):
    print("App terminated")
    self.app.quit()

  def enableAnalyze(self):
    self.start_button.config(state='normal')
    self.update_hint("Ready to analyze!")

  def disableAnalyze(self, hint="Please wait..."):
    self.start_button.config(state='disabled')
    self.update_hint(hint)

def get_invoice_data(sd, ed):
  print(sd, ed)
  start = False
  re_x = []
  re_y = []
  re_z = []
  cnt  = {}
  cnt2 = {}
  for data, data2 in zip(invoice_data, invoice_data2):
    if data['timestamp'] == sd:
      start = True
    if start:
      for city in data['address']:
        key = city[:3]
        if key not in cnt:
          cnt[key] = 1
        else:
          cnt[key] += 1
      for city in data2['address']:
        key = city[:3]
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

class DataCollector:

  def __init__(self):
    self.workers = []
    self.threads = []
    self.ready   = False
    self.data    = []
    self.data2   = []

  def start(self, url, page, _async = True):
    if(_async):
      t = threading.Thread(target = self.scan_web, args=(url,page,))
      t.start()

    else:
      self.scan_web(url, page)

  def scan_web(self, url, page):
    print("Target url: {}".format(url))
    worker = webdriver.Chrome()
    worker.get(url)
    if(page):
      but = worker.find_element_by_link_text(str(page+1))
      print(but, page+1)
      if(but):
        but.click()
    links = []
    for ele in worker.find_elements_by_partial_link_text('統一發票特別獎及特獎中獎清冊'):
      links.append(ele.get_attribute('href'))
    print(links)
    
    for link in links:
      worker.get(link)
      self.collect_group_data(worker)
    
    self.ready = True
    worker.quit()

  def collect_group_data(self, web):
    hash = {
      'timestamp': '',
      'number': [],
      'company': [],
      'address': [],
      'goods': []
    }

    title = web.find_element_by_class_name("text-center").text
    title = title.split('年')
    year  = int(title[0])
    month = int(title[1].split('-')[0])
    hash['timestamp'] = "{}/{}".format(year, month)
    print(hash['timestamp'], len(self.data), len(self.data2))
    hash2 = copy.deepcopy(hash)
    # Find table header (number/compant/address/goods)
    for i in range(4):
      idx  = i + 1
      idx2 = i + 6
      # find column datas
      eles  = web.find_elements_by_css_selector("td[headers=group{}]".format(idx))
      eles2 = web.find_elements_by_css_selector("td[headers=group{}]".format(idx2))
      for dat in eles:
        if i == 0:
          hash['number'].append(dat.text)
        elif i == 1:
          hash['company'].append(dat.text)
        elif i == 2:
          hash['address'].append(dat.text)
        elif i == 3:
          hash['goods'].append(dat.text)
        print("Group {}: {}".format(i, dat.text))
      
      for dat in eles2:
        if i == 0:
          hash2['number'].append(dat.text)
        elif i == 1:
          hash2['company'].append(dat.text)
        elif i == 2:
          hash2['address'].append(dat.text)
        elif i == 3:
          hash2['goods'].append(dat.text)
        print("Group {}-2: {}".format(i, dat.text))
    #end for i in range(4)
    self.data.append(hash)
    self.data2.append(hash2)

def create_GUI():
  global app
  app = GUI()

def start_GUI():
  global app
  app.start()

def collect_data():
  for i in range(page_cnt):
    workers.append(DataCollector())
    workers[i].start(source_url, i)

def report_data():
  global workers
  for i in range(page_cnt):
    global flag_data_ready
    flag_data_ready = True
    if(not workers[i].ready):
      flag_data_ready = False
      break
  
  with open(FileOut, 'wb') as file:
    if flag_data_ready:
      for i in range(page_cnt):
        ss = "Worker {}:".format(i)
        # print(ss)
        ss += '\n'
        ss = ss.encode('utf-8')
        file.write(ss)
        for data in workers[i].data:
          for key, value in data.items():
            ss = "  {}:".format(key)
            # print(ss)
            ss += '\n'
            ss = ss.encode('utf-8')
            file.write(ss)
            if isinstance(value, collections.Iterable) and not isinstance(value, (str, bytes)):
              for item in value:
                ss = "    {}".format(item)
                # print(ss)
                ss += '\n'
                ss = ss.encode('utf-8')
                file.write(ss)
            else:
              ss = "    {}".format(value)
              # print(ss)
              ss += '\n'
              ss = ss.encode('utf-8')
              file.write(ss)
        ss = "Data 2"
        # print(ss)
        ss += '\n'
        ss = ss.encode('utf-8')
        file.write(ss)
        for data in workers[i].data2:
          for key, value in data.items():
            ss = "  {}:".format(key)
            # print(ss)
            ss += '\n'
            ss = ss.encode('utf-8')
            file.write(ss)
            if isinstance(value, collections.Iterable) and not isinstance(value, (str, bytes)):
              for item in value:
                ss = "    {}".format(item)
                # print(ss)
                ss += '\n'
                ss = ss.encode('utf-8')
                file.write(ss)
            else:
              ss = "    {}".format(value)
              # print(ss)
              ss += '\n'
              ss = ss.encode('utf-8')
              file.write(ss)
      merge_worker_data()
    #end if
  #end with
  print("------End Of Data------")
  return flag_data_ready

def listen_data_report():
  global app
  while not report_data():
    print("Data not ready, wait for 1 sec.")
    time.sleep(1)
  else:
    print("Data ready")
    app.enableAnalyze()

def merge_worker_data():
  global workers, invoice_data, invoice_data2
  for i in range(page_cnt):
    print("Data size:")
    print("{}: {} {}".format(i, len(workers[i].data), len(workers[i].data2)))
    invoice_data.extend(workers[i].data)
    invoice_data2.extend(workers[i].data2)
  #end for
  invoice_data  = sorted(invoice_data,  key=lambda d: d['timestamp'])
  invoice_data2 = sorted(invoice_data2, key=lambda d: d['timestamp'])
  with open(Savefile, 'wb') as sfile:
    pickle.dump([invoice_data, invoice_data2], sfile)
  print("Total Data size:")
  print(len(invoice_data), len(invoice_data2))

gui_test = False
shotcut  = True

if shotcut and os.path.exists(Savefile):
  with open(Savefile, 'rb') as sfile:
    invoice_data, invoice_data2 = pickle.load(sfile)
elif not gui_test:
  t = threading.Thread(target=listen_data_report)
  collect_data()
  t.start()

create_GUI()
if invoice_data or gui_test:
  app.enableAnalyze()
start_GUI()