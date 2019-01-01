import builtins
import threading
import copy
import time
import os
import collections
import pickle
from selenium import webdriver
from urllib.parse import urlparse
from selenium.webdriver.chrome.options import Options

PWD      = os.path.dirname(os.path.realpath(__file__))
FileOut  = PWD + '\\out.txt'
Savefile = PWD + '\\save.dat'

class DataManager:

  def __init__(self):
    raise Exception('This is a static class')

  @classmethod
  def initialize(cls):
    cls.data          = {}
    cls.invoice_data  = []
    cls.invoice_data2 = []
    cls.workers       = []
    cls.ready         = False
    cls.source_url    = "https://www.etax.nat.gov.tw/etw-main/web/ETW183W1/"
    cls.page_count    = 7
    cls.terminated    = False

  @classmethod
  def start_collect(cls, fallback, print_debug=True):
    cls.data_collected_fallback = fallback
    if os.path.exists(Savefile):
      with open(Savefile, 'rb') as sfile:
        cls.invoice_data, cls.invoice_data2 = pickle.load(sfile)
      cls.on_data_ready()
    else:
      for i in range(cls.page_count):
        cls.workers.append(DataCollector())
        cls.workers[i].start(cls.source_url, i)
      t = threading.Thread(target=cls.listen_data_report(print_debug))
      t.start()

  @classmethod
  def listen_data_report(cls, log=True):
    while not cls.report_data(log) and not singal_kill:
      if log:
        print("Data not ready, wait for 1 sec.")
      time.sleep(1)
    else:
      if singal_kill:
        cls.terminated = True
      else:
        if log:
          print("Data ready")
        cls.on_data_ready()
  
  @classmethod
  def on_data_ready(cls):
    if singal_kill:
      return
    if cls.data_collected_fallback:
      try:
        cls.data_collected_fallback()
      except Exception:
        cls.data_collected_fallback.im_func()

  @classmethod
  def report_data(cls, log):
    tmp_flag = True
    for i in range(cls.page_count):
      if(not cls.workers[i].ready):
        tmp_flag = False
        break
    if tmp_flag:
      cls.ready = True
      cls.log_all_data(log)
      cls.merge_worker_data()
    else:
      cls.ready = False
    return tmp_flag

  @classmethod
  def log_all_data(cls, log=True):
    with open(FileOut, 'wb') as file:
      for i in range(cls.page_count):
        ss = "Worker {}:\n".format(i)
        ss = ss.encode('utf-8')
        file.write(ss)
        for data in cls.workers[i].data:
          for key, value in data.items():
            ss = "  {}:\n".format(key)
            ss = ss.encode('utf-8')
            file.write(ss)
            if isinstance(value, collections.Iterable) and not isinstance(value, (str, bytes)):
              for item in value:
                ss = "    {}\n".format(item)
                ss = ss.encode('utf-8')
                file.write(ss)
            else:
              ss = "    {}\n".format(value)
              ss = ss.encode('utf-8')
              file.write(ss)
        #end for each data
        ss = "Data 2\n"
        ss = ss.encode('utf-8')
        file.write(ss)
        for data in cls.workers[i].data2:
          for key, value in data.items():
            ss = "  {}:\n".format(key)
            ss = ss.encode('utf-8')
            file.write(ss)
            if isinstance(value, collections.Iterable) and not isinstance(value, (str, bytes)):
              for item in value:
                ss = "    {}\n".format(item)
                ss = ss.encode('utf-8')
                file.write(ss)
            else:
              ss = "    {}\n".format(value)
              ss = ss.encode('utf-8')
              file.write(ss)
        #end for each data2
      #end for each worker
    #end with
    print("------End Of Data------")
  #end log all data
  
  @classmethod
  def merge_worker_data(cls):
    for i in range(cls.page_count):
      print("Data size:")
      print("{}: {} {}".format(i, len(cls.workers[i].data), len(cls.workers[i].data2)))
      cls.invoice_data.extend(cls.workers[i].data)
      cls.invoice_data2.extend(cls.workers[i].data2)
    cls.invoice_data  = sorted(cls.invoice_data,  key=lambda d: d['timestamp'])
    cls.invoice_data2 = sorted(cls.invoice_data2, key=lambda d: d['timestamp'])
    with open(Savefile, 'wb') as sfile:
      pickle.dump([cls.invoice_data, cls.invoice_data2], sfile)
    print("Total Data size:")
    print(len(cls.invoice_data), len(cls.invoice_data2))
#end DataManger
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
    if singal_kill:
      print("Received kill singal")
      return worker.quit()
    worker.get(url)

    if(page):
      but = worker.find_element_by_link_text(str(page+1))
      print(but, page+1)
      if singal_kill:
        print("Received kill singal")
        return worker.quit()
      if(but):
        but.click()
        
    links = []
    for ele in worker.find_elements_by_partial_link_text('統一發票特別獎及特獎中獎清冊'):
      if singal_kill:
        print("Received kill singal")
        return worker.quit()
      links.append(ele.get_attribute('href'))
    print(links)
    singal = True
    for link in links:
      if singal_kill or (not singal):
        print("Received kill singal")
        return worker.quit()
      worker.get(link)
      singal = self.collect_group_data(worker)
    
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

    if singal_kill:
      return False
    # Find table header (number/compant/address/goods)
    for i in range(4):
      idx  = i + 1
      idx2 = i + 6
      # find column datas
      eles  = web.find_elements_by_css_selector("td[headers=group{}]".format(idx))
      if singal_kill:
        return False
      eles2 = web.find_elements_by_css_selector("td[headers=group{}]".format(idx2))
      if singal_kill:
        return False
      for dat in eles:
        if singal_kill:
          return False
        if i == 0:
          hash['number'].append(dat.text)
        elif i == 1:
          hash['company'].append(dat.text)
        elif i == 2:
          hash['address'].append(dat.text)
        elif i == 3:
          hash['goods'].append(dat.text)
        print("Group {}: {}".format(i, dat.text))

      if singal_kill:
        return False

      for dat in eles2:
        if singal_kill:
          return False
        if i == 0:
          hash2['number'].append(dat.text)
        elif i == 1:
          hash2['company'].append(dat.text)
        elif i == 2:
          hash2['address'].append(dat.text)
        elif i == 3:
          hash2['goods'].append(dat.text)
        print("Group {}-2: {}".format(i, dat.text))
      if singal_kill:
        return False
    #end for i in range(4)
    self.data.append(hash)
    self.data2.append(hash2)
    return True