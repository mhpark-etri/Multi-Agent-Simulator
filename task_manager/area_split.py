
import matplotlib.pyplot as plt
import seaborn as sns
import os
import numpy as np


os.chdir('d:/temp')

mapfile = 'map.pgm'
with open(mapfile, 'rb') as imap:
    gmap = plt.imread(imap)
