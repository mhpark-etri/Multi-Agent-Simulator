import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np
from utils import Point

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

def compute_area(gmap, lp, up, threshold=240):
  area_cnt = 0
  for  i in range(up.x, lp.x):
    for j in range(up.y, lp.y):
      if gmap[i,j] > threshold: area_cnt = area_cnt + 1
  return area_cnt

def split_area(gmap, lp, up, threshold=240):
  num_agents = 3
  area = compute_area(gmap, lp, up)
  subarea = area / num_agents

  split_line = []
  new_up = up
  for  j in range(up.y, lp.y):
      new_lp = Point(lp.x, j)
      ar = compute_area(gmap, new_lp, new_up, threshold)
      if ar < subarea: continue
      split_line.append(new_lp)
      new_up = Point(up.x, new_lp.y)

  return split_line
