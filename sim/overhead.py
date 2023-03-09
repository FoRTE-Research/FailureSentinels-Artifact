#!/usr/bin/python3

import matplotlib
#matplotlib.use('Agg')

import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
sns.set()

import csv
import math

from si_prefix import si_format
from scipy import interpolate

FILENAME = "nyc_night_trace.txt"
PANEL_EFFICIENCY = 0.15  # Fractional value (0.2 = 20%)
PANEL_SIZE = 5           # In square centimeters

CHECKPOINT_TIME = 8.192 * 1e-3  # In seconds

CAPACITOR_SIZE = 47 * 1e-6  # In farads

# Current values from MSP430FR6989 datasheet
MCU_LEAKAGE_CURRENT = 0.5 * 1e-6 # Encompasses all leakage draining capacitor energy (amps)
#MCU_LEAKAGE_CURRENT = 50 * 1e-6 # Encompasses all leakage draining capacitor energy (amps)

#MCU_ACTIVE_CURRENT = 112.3 * 1e-6  # MCU current draw when running (amps)
#RESOLUTION = 0                      # Volts
#print(f"Ideal operation: {si_format(MCU_ACTIVE_CURRENT)}A")

#MCU_ACTIVE_CURRENT = 113.6 * 1e-6 # MCU current draw when running (amps)
#RESOLUTION = 38 * 1e-3            # Volts
#print(f"FS High Performance: {si_format(MCU_ACTIVE_CURRENT)}A")

MCU_ACTIVE_CURRENT = 112.5 * 1e-6 # MCU current draw when running (amps)
RESOLUTION = 50 * 1e-3            # Volts
print(f"FS Low Power: {si_format(MCU_ACTIVE_CURRENT)}A")

#MCU_ACTIVE_CURRENT = 377.3 * 1e-6 # MCU current draw when running (amps)
#RESOLUTION = 293 * 1e-6           # Volts
#print(f"ADC: {si_format(MCU_ACTIVE_CURRENT)}A")

#MCU_ACTIVE_CURRENT = 147.3 * 1e-6 # MCU current draw when running (amps)
#RESOLUTION = 30 * 1e-3            # Volts
#print(f"Comparator: {si_format(MCU_ACTIVE_CURRENT)}A")

MCU_DATASHEET_VOLTAGE = 3.0     # Voltage at which above values are extracted, for power calculation (volts)

MAX_VOLTAGE = 3.6      # Voltage above which we burn off any energy (volts)
ENABLE_VOLTAGE = 3.5    # Voltage at which the MCU turns on and begins draining the capacitor (volts)
# Voltage at which the MCU must stop executing application code and take a checkpoint
DISABLE_VOLTAGE = 1.8 + (CHECKPOINT_TIME * (MCU_ACTIVE_CURRENT + MCU_LEAKAGE_CURRENT) / CAPACITOR_SIZE) + RESOLUTION

print(f"Calculated disable voltage: {DISABLE_VOLTAGE}")

# Capacitor input in terms of power and energy, not current and charge; convert MCU draw to
# power for ease of computation.
MCU_ACTIVE_POWER = MCU_ACTIVE_CURRENT * MCU_DATASHEET_VOLTAGE   # Models MCU as constant power load, not sure about that

TIMESTEP = 5 * 1e-3     # Simulation timestep

print(f"Capacitor size: {si_format(CAPACITOR_SIZE)}F")

fileTimes = []              # In seconds
fileIrradiances = []        # In watts per square centimeter

with open(FILENAME) as csv_file:
  csv_reader = csv.reader(csv_file, delimiter='\t')
  next(csv_reader)  # Skip header row
  for row in csv_reader:
    r = [i.strip() for i in row]
    fileTimes.append(int(r[0]))
    fileIrradiances.append(float(r[1]) * 1e-6)  # CSV file reports in micro-watts per square centimeter, convert to watts

irradiance = interpolate.interp1d(fileTimes, fileIrradiances)

times = np.linspace(0, fileTimes[-1], num=int(len(fileTimes)/TIMESTEP))
#print(len(fileTimes))
#print(len(fileTimes) / TIMESTEP)
#print(fileTimes[-1] * TIMESTEP)
#print(times)

# Quick simulation of operation in the environment defined above
# For each sim step:
#   1.  Add harvested energy to capacitor; irradiance is provided for every second, so
#       simply reading out the irradiance gives us joules per square centimeter
#       harvested over the course of that second
#   2.  Subtract operating energy for the current mode; at the second scale, so simply
#       reading out MCU_ACTIVE_POWER gives us joules drawn over the course of that second
#   3.  If supply voltage => ENABLE_VOLTAGE or < DISABLE_VOLTAGE, change accordingly.

capVoltage = [0 for i in times]
capEnergy = [0 for i in times]
deviceOn = [False for i in times]

point25 =  int(0.25 * len(times))
point50 =  int(0.5 * len(times))
point75 =  int(0.75 * len(times))
point100 = len(times) - 1

# Initialize capacitor to some value

capVoltage[0] = 3.3
capEnergy[0] = 0.5 * CAPACITOR_SIZE * (capVoltage[0] ** 2)

for t in range(1, len(times)):
  inputEnergy = irradiance(TIMESTEP * (times[t - 1])) * PANEL_EFFICIENCY * PANEL_SIZE * TIMESTEP
  outputEnergy = MCU_ACTIVE_POWER * TIMESTEP if deviceOn[t - 1] else MCU_LEAKAGE_CURRENT * capVoltage[t - 1] * TIMESTEP

  capEnergy[t] = capEnergy[t - 1] + inputEnergy - outputEnergy
  # U = 0.5CV^2
  # V = sqrt(2U/C)
  capVoltage[t] = math.sqrt(2 * capEnergy[t] / CAPACITOR_SIZE)

  if capVoltage[t] >= MAX_VOLTAGE:
    capVoltage[t] = MAX_VOLTAGE
    capEnergy[t] = 0.5 * CAPACITOR_SIZE * (capVoltage[t] ** 2)

  if capVoltage[t] >= ENABLE_VOLTAGE and not deviceOn[t - 1]: # If device is off and reaches enable voltage, turn on
    deviceOn[t] = True
  elif capVoltage[t] >= DISABLE_VOLTAGE and deviceOn[t - 1]:  # If device is on and can operate at this voltage, stay on
    deviceOn[t] = True
  else:
    deviceOn[t] = False                                       # Otherwise, turn off

  #print()
  #print(f"Harvested energy at time {t}: {si_format(inputEnergy, 3)}J")
  #print(f"Dissipated energy at time {t}: {si_format(outputEnergy, 3)}J")
  #print(f"Capacitor voltage at time {t}: {si_format(capVoltage[t], 3)}V")
  #print(f"Device on? {deviceOn[t]}")
  #if t == point25:
  #  print("25% done")
  #if t == point50:
  #  print("50% done")
  #if t == point75:
  #  print("75% done")
  #if t == point100:
  #  print("Done")

print(sum([1 if on else 0 for on in deviceOn]))

onPeriod = False

# Number of "on times"
executionCount = 0

for i in range(len(deviceOn)):
  if deviceOn[i] and not deviceOn[i - 1]: # Count posedges of deviceOn
    executionCount += 1

print(f"On time: {si_format(sum([1 if on else 0 for on in deviceOn]) * TIMESTEP)}s")
print(f"Execution count: {executionCount}")
print(f"Trace time: {max(times)}s")
print(f"Duty cycle: {np.mean([1 if on else 0 for on in deviceOn])}")
print(f"Average power input: {si_format(np.mean(fileIrradiances) * PANEL_EFFICIENCY * PANEL_SIZE)}W")

#plt.plot(times, capVoltage, marker='x', label="Supply voltage (V)")
#plt.plot(times, [1 if on else 0 for on in deviceOn], marker='+', label="Device on")

plt.plot(times, capVoltage, label="Supply voltage (V)")
plt.plot(times, [1 if on else 0 for on in deviceOn], label="Device on")
#plt.legend()
plt.show()
