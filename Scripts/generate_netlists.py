#! /usr/bin/python3

import numpy as np
import os

NETLIST_FOLDER = "netlists_130_mcRun_7_61/" # Should match NETLIST_FOLDER in ring_oscillator.py
NETLIST_FILE = NETLIST_FOLDER[:-1] + ".txt"

sizes = [7, 61]
#voltages = [round(i, 1) for i in np.arange(1.8, 3.7, 0.1)]
voltages = [round(i, 1) for i in np.arange(1.8, 2.2, 0.1)]
coreVoltage = 1.8
mcTols = [0.0]

print(f"Sizes: {sizes}")
print(f"Voltages: {voltages}")

with open(NETLIST_FILE, "w") as f:
  for m in mcTols:
    for s in sizes:
      for v in voltages:
        os.system(f"./ring_oscillator.py {s} {v} {coreVoltage} {m}")
        f.write(f"{NETLIST_FOLDER}ro_{s}_{v}v_mc{m}.net\n")
