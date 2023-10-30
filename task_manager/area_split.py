import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np


os.chdir('d:/temp')

mapfile = 'map.pgm'
with open(mapfile, 'rb') as imap:
    gmap = plt.imread(imap)

num_agents = 3

def transform_map(gmap, pixels=10):
  rows = int(np.ceil(gmap.shape[0] / pixels))
  cols = int(np.ceil(gmap.shape[1] / pixels)) 
  new_map = np.zeros((rows, cols), dtype=np.uint8)
  for i in range(0, rows):
      for j in range(0, cols):
        new_map[i, j] = gmap[i*pixels:i*pixels+pixels, j*pixels:j*pixels+pixels].mean()
  return new_map

def transform_point(p, scale=1):
  pixels = scale
  return Point(int(p.x/pixels), int(p.y/pixels))

class Point:
  def __init__(self, x=0, y=0):
    self.x = x
    self.y = y
  def get_str(self):
    return str(self.x)+","+str(self.y)



def compute_area(gmap, lp, up, threshold=240):
  area_cnt = 0
  for  i in range(up.x, lp.x):
    for j in range(up.y, lp.y):
      if gmap[i,j] > threshold: area_cnt = area_cnt + 1
  return area_cnt

