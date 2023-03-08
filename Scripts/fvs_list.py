#! /usr/bin/python3

import csv
import os
import sys
import matplotlib as mpl
mpl.use('Agg')  # Headless
import matplotlib.pyplot as plt
import numpy as np
from scipy import stats
from si_prefix import si_format

import seaborn as sns
sns.set()

#print("Hello, world!")

#print("Expected format: length, voltage, freq. mean, freq. std, freq. rsd, power mean, power std, power rsd, amplitude mean, amplitude std, amplitude rsd")

if len(sys.argv) != 2:
  print("Provide a ring oscillator data CSV file")
  quit()

filename = sys.argv[1]

if not os.path.exists(filename):
  print(f"{filename} does not exist, exiting")
  quit()

# One of each plot for each length RO
lengths = dict()

with open(filename, newline='') as csvfile:
  reader = csv.reader(csvfile)
  for row in reader:
    #print(row[1:])
    #if float(row[1]) < 1.8 or float(row[1]) > 3.6:
    #  continue
    if row[0] not in lengths:
      lengths[row[0]] = [[float(i) for i in row[1:]]]
    else:
      lengths[row[0]].append([float(i) for i in row[1:]])

# In case csv isn't in order, need to sort it by voltage: easier to do before transposing
for key in lengths:
  lengths[key].sort(key = lambda x: x[0])

for key in lengths:
  print(f"{key}", end=',')
  for v in lengths[key]:
      print(v[1], end=',')
  print()

#for key in lengths:
#  print(f"Transposing {key}")
#  lengths[key] = np.array(lengths[key]).transpose().tolist()
#  print(lengths[key])

