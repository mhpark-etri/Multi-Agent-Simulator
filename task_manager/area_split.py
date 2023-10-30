import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np


os.chdir('d:/temp')

mapfile = 'map.pgm'
with open(mapfile, 'rb') as imap:
    gmap = plt.imread(imap)

def transform_map(gmap, pixels=10):
  rows = int(np.ceil(gmap.shape[0] / pixels))
  cols = int(np.ceil(gmap.shape[1] / pixels)) 
  new_map = np.zeros((rows, cols), dtype=np.uint8)
  for i in range(0, rows):
      for j in range(0, cols):
        new_map[i, j] = gmap[i*pixels:i*pixels+pixels, j*pixels:j*pixels+pixels].mean()
  return new_map
