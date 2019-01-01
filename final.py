import builtins
from util import *
from datamanger import *
from gui import *

builtins.singal_kill = False

def on_collect_ok():
  global app
  app.assign_data(DataManager.invoice_data, DataManager.invoice_data2)
  app.enableAnalyze()

def start_collect():
  DataManager.start_collect(on_collect_ok)

DataManager.initialize()
app = GUI()
t = threading.Thread(target=start_collect)
t.start()
app.start()