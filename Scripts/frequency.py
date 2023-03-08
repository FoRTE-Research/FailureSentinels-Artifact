#! /usr/bin/python3
import ltspice
#import matplotlib.pyplot as plt
import numpy as np
import sys
from si_prefix import si_format

if len(sys.argv) < 2:
  print("Supply an LTSpice .raw file with a periodic V(V0) signal")
  quit()

verbose = True

if len(sys.argv) == 3 and sys.argv[2] == "embedded":
  verbose = False

def print_verbose(arg, end=''):
  if verbose:
    print(arg, end)

#ro_61_1.4v_mc0.1.raw
def parse_filename(name):
  length = int(name.split("ro_")[1].split("_")[0])
  voltage = float(name.split(f"ro_{length}_")[1].split("v")[0])
  return (length, voltage)

name = sys.argv[1]

l = ltspice.Ltspice(name)
l.parse()

print_verbose("Hello, world!")
print_verbose("Provide a third command line argument 'embedded' to reduce verbosity")

print_verbose(f"{name}")

freqs = []
powers = []
amplitudes = []

nofreq = False

voltage = parse_filename(name)[1]

# c used to be case but python 3.10 broke it :(
# And python ltspice package update code rot
#for c in range(l.getCaseNumber()):
#  data = l.getData("V(shifter_out)", c)
#  vdd_voltage = l.getData("V(Vsupply)", c)
#  vdd_current = l.getData("I(V_power)", c)
#  time = l.getTime(c)
for c in range(len(l._case_split_point) - 1):
  data = l.get_data("V(shifter_out)", c)
  vdd_voltage = l.get_data("V(Vsupply)", c)
  vdd_current = l.get_data("I(V_power)", c)
  time = l.get_time(c)
  #data = l.get_data("V(shifter_out)", 0)
  #vdd_voltage = l.get_data("V(Vsupply)", 0)
  #vdd_current = l.get_data("I(V_power)", 0)
  #time = l.get_time(0)

  power = abs(np.mean([vdd_voltage[t] * vdd_current[t] for t in range(len(vdd_voltage))]))
  powers.append(power)

  #amplitudes.append(max(data) - min(data))
  amplitudes.append(max(data))

  # Estimate signal frequency by measuring time between rising 0.5 crossings
  
  indices = [i for i in range(len(data) - 1) if data[i] < 0.5 and data[i + 1] >= 0.5]
  crossTimes = [time[i] for i in indices]
  
  if len(crossTimes) == 0 and not nofreq:
    print_verbose(f"No 0.5 crossings detected; did you run the simulation for long enough (slow oscillations)?")
    nofreq = True # Don't attempt to analyze frequency if we run into a problem here
    continue
  if nofreq:
    continue
  
  periods = np.diff(crossTimes)
  freq = 1 / np.mean(periods)
  freqs.append(freq)
  
  #print(f"Case: {c}")
  #print(f"Frequency estimate: {si_format(freq)}")
  #print()

#d = l.getData("V(V0)", 24)
#t = l.getTime(24)
#
#plt.plot(t[0:300], d[0:300])
#plt.savefig("test.pdf")

if not verbose:
  print(f"{parse_filename(name)[0]},{parse_filename(name)[1]}", end=",")

if nofreq:
  #print("No frequency measurement")
  if verbose:
    print(f"Frequency mean, std, RSD: 0, 0, 0")
  else:
    print("0,0,0", end=",")
elif verbose:
  print(f"Frequency mean, std, RSD: {si_format(np.mean(freqs), precision=3)}, {si_format(np.std(freqs), precision=3)}, {round(100 * np.std(freqs) / np.mean(freqs), 4)}%")
else:
  print(f"{np.mean(freqs)},{np.std(freqs)},{100 * np.std(freqs) / np.mean(freqs)}", end=",")

if verbose:
  print(f"Power mean, std, RSD: {si_format(np.mean(powers), precision=3)}, {si_format(np.std(powers), precision=3)}, {round(100 * np.std(powers) / np.mean(powers), 4)}%")
else:
  print(f"{np.mean(powers)},{np.std(powers)},{100 * np.std(powers) / np.mean(powers)}", end=",")

if np.mean(amplitudes) == 0:
  if verbose:
    print(f"Amplitude mean, std, RSD: 0, 0, 0")
  else:
    print("0,0,0", end="")
elif verbose:
  print(f"Amplitude mean, std, RSD: {si_format(np.mean(amplitudes), precision=3)}, {si_format(np.std(amplitudes), precision=3)}, {round(100 * np.std(amplitudes) / np.mean(amplitudes), 4)}%")
else:
  print(f"{np.mean(amplitudes)},{np.std(amplitudes)},{100 * np.std(amplitudes) / np.mean(amplitudes)}", end="")
