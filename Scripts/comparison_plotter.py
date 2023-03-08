#! /usr/bin/python3

import csv
import sys
import os
import matplotlib as mpl
mpl.use('Agg') # Headless
import matplotlib.pyplot as plt
import numpy as np

print("Expected format: feature size in nm,length,freq@0.2v,freq@0.3v,...,freq@3.6v")
voltages = [round(i, 1) for i in np.arange(0.2, 3.7, 0.1)]

if len(sys.argv) != 2:
  print("Provide a frequency vs voltage/feature size file")
  quit()

filename = sys.argv[1]

if not os.path.exists(filename):
  print(f"{filename} does not exist, exiting")
  quit()

sizes = dict()

with open(filename, newline='') as csvfile:
  reader = csv.reader(csvfile)
  for row in reader:
    sizes[(int(row[0]), int(row[1]))] = [float(i) for i in row[2:]]

colors = dict()

for key in sizes:
    if key[1] == 11:
      p = plt.plot(voltages, [i * 1e-6 for i in sizes[key]], label=f"{key[0]} nm, {key[1]}-stage", marker='o')
      colors[key[0]] = p[-1].get_color()
    elif key[1] == 21:
      p = plt.plot(voltages, [i * 1e-6 for i in sizes[key]], label=f"{key[0]} nm, {key[1]}-stage", marker='x', color=colors[key[0]])

plt.xlabel("Supply voltage")
plt.ylabel("Frequency (MHz)")

plt.legend()
plt.tight_layout()
#plt.show()
plt.savefig("freq_unit_size.pdf")

# Derivative of above graph
plt.close()

colors = dict()

vDiff = np.diff(voltages)

senseByVoltage = dict()

for key in sizes:
    sDiff = np.diff(sizes[key])
    #print(voltages)
    #print(f"vDiff: {vDiff}")
    #print(f"sDiff: {sDiff}")
    senseByVoltage[key] = [(sd / vd * 1e-6) for (sd, vd) in zip(sDiff, vDiff)]
    if key[1] == 11:
      p = plt.plot([i + (np.mean(vDiff) / 2) for i in voltages[:-1]], [(sd / vd * 1e-6) for (sd, vd) in zip(sDiff, vDiff)], label=f"{key[0]} nm, {key[1]}-stage", marker='o')
      colors[key[0]] = p[-1].get_color()
    elif key[1] == 21:
      p = plt.plot([i + (np.mean(vDiff) / 2) for i in voltages[:-1]], [(sd / vd * 1e-6) for (sd, vd) in zip(sDiff, vDiff)], label=f"{key[0]} nm, {key[1]}-stage", marker='x', color=colors[key[0]])

avgRatio = 0
count = 0
for k in senseByVoltage:
  print(k)
  #print(f"1.8v - 3.6v sensitivity mean: {np.mean(senseByVoltage[k][16:34])}")
  #print(f"0.9v - 1.8v sensitivity mean: {np.mean(senseByVoltage[k][7:17])}")
  #print(f"Ratio: {np.mean(senseByVoltage[k][7:17]) / np.mean(senseByVoltage[k][16:34])}")
  print(f"Div2 Compensated: {(np.mean(senseByVoltage[k][7:17]) / np.mean(senseByVoltage[k][16:34])) / 2}")
  avgRatio += np.mean(senseByVoltage[k][7:17]) / np.mean(senseByVoltage[k][16:34])
  count += 1

print(f"Average compensated ratio: {avgRatio / count / 2}")
print()

avgRatio = 0
count = 0
for k in senseByVoltage:
  print(k)
  #print(f"0.6v - 1.2v sensitivity mean: {np.mean(senseByVoltage[k][4:11])}")
  #print(f"Ratio: {np.mean(senseByVoltage[k][4:11]) / np.mean(senseByVoltage[k][16:34])}")
  print(f"Div3 Compensated: {(np.mean(senseByVoltage[k][4:11]) / np.mean(senseByVoltage[k][16:34])) / 3}")
  avgRatio += np.mean(senseByVoltage[k][4:11]) / np.mean(senseByVoltage[k][16:34])
  count += 1

print(f"Average ratio: {avgRatio / count}")
print(f"Average compensated ratio: {avgRatio / count / 3}")
print()

avgRatio = 0
count = 0
for k in senseByVoltage:
  print(k)
  #print(f"0.4v - 0.9v sensitivity mean: {np.mean(senseByVoltage[k][2:8])}")
  #print(f"Ratio: {np.mean(senseByVoltage[k][2:8]) / np.mean(senseByVoltage[k][16:34])}")
  print(f"Div4 sort of compensated: {(np.mean(senseByVoltage[k][2:8]) / np.mean(senseByVoltage[k][16:34])) / 4}")
  avgRatio += np.mean(senseByVoltage[k][2:8]) / np.mean(senseByVoltage[k][16:34])
  count += 1

print(f"Average ratio: {avgRatio / count}")
print(f"Average compensated ratio: {avgRatio / count / 4}")
print()

plt.xlabel("Supply voltage")
plt.ylabel("Sensitivity (kHz/mV)")

plt.legend()
plt.tight_layout()
#plt.show()
plt.savefig("freq_unit_size_derivative.pdf")
