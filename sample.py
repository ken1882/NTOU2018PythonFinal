# -*- coding: utf-8 -*-
"""
Embed the figure of matplotlib into tkinter
"""
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
import tkinter as tk
import numpy as np
import math

root = tk.Tk()
b1   = tk.Button(root,text="Quit",command=root.quit)
b1.pack()

# draw the figure
f = Figure(figsize=(5,5), dpi=100)
a = f.add_subplot(211)
x = np.linspace(-50,50,100)
y = [math.cos(z) for z in x]
a.plot(x,y)
a.set_xlabel('x')
a.set_ylabel('y')

b = f.add_subplot(212)
b.bar(x,y)
b.set_xlabel('x')
b.set_ylabel('y')
f.tight_layout()

# show this figure on this canvas
canvas = FigureCanvasTkAgg(f, root)
canvas.draw()
canvas.get_tk_widget().pack(side=tk.BOTTOM, fill=tk.BOTH, expand=True)

toolbar = NavigationToolbar2Tk(canvas, root)
toolbar.update()
canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)


root.mainloop()
try:
    root.destroy()
except:
    pass