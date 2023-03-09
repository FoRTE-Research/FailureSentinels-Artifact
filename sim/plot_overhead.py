#!/usr/bin/python3

import matplotlib
matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

import csv
import math

from si_prefix import si_format
from scipy import interpolate

barLabels = ["FS LP", "FS HP", "Comparator", "ADC"]
#percentIncreases = [0.00201929549, 0.01086464464, 0.312371437, 2.368024133]
idealDutyCycle = 4.64 # Percent
percentDecreases = [4.63 / idealDutyCycle, 4.58 / idealDutyCycle, 3.51 / idealDutyCycle, 1.34 / idealDutyCycle]
overheadsInv = [1.0 - i for i in percentDecreases]
barPositions = [i for i in range(1, len(overheadsInv) + 1)]

plt.xticks(ticks=barPositions, labels=barLabels)
plt.bar(barPositions, overheadsInv)

for i in range(len(barPositions)):
  plt.text(barPositions[i], overheadsInv[i] + 0.01, f"{round(100 * overheadsInv[i], 2)}%", horizontalalignment='center')

plt.xlabel("Voltage Monitor")
plt.ylabel("Available Runtime Reduction")

plt.tight_layout()
plt.savefig("runtime_reduction.pdf")
#plt.show()
