#! /usr/bin/python3

import sys
import numpy as np
import matplotlib as mpl
#mpl.use('Agg')
import matplotlib.pyplot as plt
import math
import seaborn as sns
sns.set()

#from pymoo.model.problem import FunctionalProblem
from pymoo.problems.functional import FunctionalProblem
#from pymoo.algorithms.nsga2 import NSGA2
from pymoo.algorithms.moo.nsga2 import NSGA2
from pymoo.optimize import minimize
from pymoo.visualization.scatter import Scatter
#from pymoo.factory import get_sampling, get_crossover, get_mutation, get_decomposition
from pymoo.factory import get_sampling, get_crossover, get_mutation
from pymoo.operators.mixed_variable_operator import MixedVariableSampling, MixedVariableMutation, MixedVariableCrossover

import pymoo.operators
from pymoo.operators.sampling.rnd import FloatRandomSampling
from pymoo.interface import sample

from si_prefix import si_format as si_format_base

def si_format(number):
  return si_format_base(number, precision=6)

print("Hello, world!")
print("CL argument order: Duty cycle, RO length, counter size, on time, LUT entries, code size")

if not (len(sys.argv) == 1 or len(sys.argv) == 7):
  print("Run without arguments or alternatively run with 6 arguments:")
  print("Duty cycle, RO length, Counter size, on time, NVM entries, and code size")
  quit()
elif len(sys.argv) == 7:
  cl_ia = []
  try:
    cl_ia.append(float(sys.argv[1]))
    cl_ia.append(int(sys.argv[2]))
    cl_ia.append(int(sys.argv[3]))
    cl_ia.append(float(sys.argv[4]))
    cl_ia.append(int(sys.argv[5]))
    cl_ia.append(int(sys.argv[6]))
  except:
    print("Failed to convert CL arguments to numbers")
    quit()
  #print(cl_ia)

TEMP_PERCENT_ERROR = 0.02

# Technology-specific parameters

# Low voltage is ~0.5x that of mean voltage
# High voltage is ~1.5x that of mean voltage
RO_FREQ_OFF_MEAN_LOW_130 = 0.4646797238702799
RO_FREQ_OFF_MEAN_HIGH_130 = 1.374897514536071

RO_FREQ_OFF_MEAN_LOW_90 = 0.4522985159483429
RO_FREQ_OFF_MEAN_HIGH_90 = 1.4732373635137397

RO_FREQ_OFF_MEAN_LOW_65 = 0.4107094591450497
RO_FREQ_OFF_MEAN_HIGH_65 = 1.4519827466152433

RO_FREQ_OFF_MEAN_LOW = RO_FREQ_OFF_MEAN_LOW_90
RO_FREQ_OFF_MEAN_HIGH = RO_FREQ_OFF_MEAN_HIGH_90

# Average current consumption of a free-running RO
RO_CURRENT_130 = 133.8 * 1e-6

RO_CURRENT_90 = 115.8 * 1e-6

RO_CURRENT_65 = 99.1 * 1e-6

RO_CURRENT = RO_CURRENT_90

# Current consumption of a single DFF switching at frequency x
DFF_CURRENT_130 = lambda x: (1.9174964 * 1e-14) * x - (7.1813107 * 1e-8)

DFF_CURRENT_90 = lambda x: (9.3298475 * 1e-15) * x - (4.1054039 * 1e-8)

DFF_CURRENT_65 = lambda x: (5.3145545 * 1e-15) * x - (3.1629207 * 1e-8)

DFF_CURRENT = DFF_CURRENT_90

# Current consumption of the level shifter operating at core voltage

SHIFTER_CURRENT_130 = lambda x: (1.9174964e-14) * x - (7.1813107e-8)

SHIFTER_CURRENT_90 = lambda x: (9.3298475e-15) * x - (4.1054039e-8)

SHIFTER_CURRENT_65 = lambda x: (5.3145545e-15) * x - (3.162907e-8)

SHIFTER_CURRENT = SHIFTER_CURRENT_90

# On-frequency at 2.7 V of RO based on regression coefficients from sense_vs_len.py
# Units: Hertz/Stage
RO_LEN_TO_FREQ_130 = lambda x: -16308142.117956843 + (4401575124.343806 / x) # UPDATED

RO_LEN_TO_FREQ_90 = lambda x: -24484159.96893492 + (4553675598.239259 / x) # UPDATED

RO_LEN_TO_FREQ_65 = lambda x: -21223759.384857353 + (4055664769.368738 / x) # UPDATED

RO_LEN_TO_FREQ = RO_LEN_TO_FREQ_90

# Mean sensitivity of RO based on regression coefficients from sense_vs_len.py
# Units: Hertz/Volt
RO_LEN_TO_SENSE_130 = lambda x: -8772384.356746912 + (2306189177.108131 / x) # UPDATED

RO_LEN_TO_SENSE_90 = lambda x: -13355210.473697366 + (2610661089.989201 / x) # UPDATED

RO_LEN_TO_SENSE_65 = lambda x: -11291019.015327066 + (2381049801.8618693 / x) # UPDATED

RO_LEN_TO_SENSE = RO_LEN_TO_SENSE_90

# Max first derivative of frequency-to-voltage function for RO based on
# values from freq_csv_reader.py (needed for temperature error)
# calculated in regression.py
# Units: Volts/Hertz
RO_LEN_TO_1DER_130 = lambda x: (7.22387618e-10) * x + (-1.24136382e-09) # UPDATED

RO_LEN_TO_1DER_90 = lambda x: (8.11301355e-10) * x + (-2.60140018e-09) # UPDATED

RO_LEN_TO_1DER_65 = lambda x: (8.70321821e-10) * x + (-3.69075909e-09) # UPDATED

RO_LEN_TO_1DER = RO_LEN_TO_1DER_90

# Max second derivative of frequency-to-voltage function for RO based on
# values from freq_csv_reader.py
# calculated in regression.py
# Units: Volts/Hertz^2
RO_LEN_TO_2DER_130 = lambda x: (1.89788681e-17) * x + (-2.55522145e-16) # UPDATED

RO_LEN_TO_2DER_90 = lambda x: (1.30402907e-16) * x + (-2.11917736e-15)  # UPDATED

RO_LEN_TO_2DER_65 = lambda x: (6.64689307e-16) * x + (-1.07531551e-14)  # UPDATED

RO_LEN_TO_2DER = RO_LEN_TO_2DER_90

# Voltage range we must measure across
VOLTAGE_RANGE = 1.8

# Input array is array of: [Duty cycle D, RO length L, counter size S, on time T]
# Input array constraints:
# Duty cycle constraints
D_MIN = 0
D_MAX = 1
# RO length constraints
L_MIN = 5
L_MAX = 73 # Limit set by regressions, which go negative below this point
# Counter size constraints
S_MIN = 1
S_MAX = 16
# LUT size constraints
B_MIN = 1
B_MAX = 128
# On time constraints
#T_MIN = 200 * 1e-9
T_MIN = 1 * 1e-6 # 1 MHz clock
T_MAX = 1 * 1e-3
# Code size constraints
C_MIN = 1
C_MAX = 16

# I will likely move these around to further constrain the problem as I learn things

# Inequality constraints:
CURRENT_MIN = 0
CURRENT_MAX = 5 * 1e-6
#CURRENT_MAX = 5 * 1e-6
SAMPLING_FREQUENCY_MIN = 1 * 1e3
SAMPLING_FREQUENCY_MAX = 10 * 1e3
#RESOLUTION_MIN = 24.5 * 1e-3
#RESOLUTION_MAX = 25.5 * 1e-3
RESOLUTION_MIN = 0 * 1e-3
RESOLUTION_MAX = 50 * 1e-3
SPACE_MIN = 0
SPACE_MAX = 1 * 128 * 8 # 128 bytes

# Helper functions
# Current in amps
def counter_current(counterSize, frequency):
  totalCurrent = 0
  for i in range(0, int(round(counterSize))):
    totalCurrent += DFF_CURRENT(frequency) / (2**i)
  return totalCurrent

# Interpolation resolution
def interpResolution(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]
  lutSize = ia[4]
  h = ((RO_FREQ_OFF_MEAN_HIGH * RO_LEN_TO_FREQ(roLength)) - (RO_FREQ_OFF_MEAN_LOW * RO_LEN_TO_FREQ(roLength))) / lutSize
  #print(f"h: {si_format(h)}Hz")
  #print(f"1d: {si_format(RO_LEN_TO_1DER(roLength))}V/Hz")

  # Piecewise-linear interpolation
  #interpRes = ((h ** 2) / 8) * RO_LEN_TO_2DER(roLength)
  # Piecewise-constant interpolation
  interpRes = h * RO_LEN_TO_1DER(roLength)
  return interpRes


# Objective functions: minimize current, maximize sampling frequency, minimize resolution, minimize space overhead

def current(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]
  
  counterFrequency = RO_LEN_TO_FREQ(roLength)
  counterCurrent = counter_current(counterSize, counterFrequency)
  levelShifterCurrent = SHIFTER_CURRENT(counterFrequency)
  return dutyCycle * (RO_CURRENT + counterCurrent + levelShifterCurrent)

def sampling_frequency(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]
  lutSize = ia[4]

  # Duty cycle D = T_on / T_s
  # Sampling period T_s = T_on / D
  # Sampling frequency F_s = D / T_on
  # Maximize sampling frequency: pymoo only minimizes
  # Flip with -1
  return -1 * dutyCycle / onTime

def resolution(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]
  lutSize = ia[4]
  codeSize = ia[5]

  # Resolution is roughly the maximum of many sources of error
  # Minimize resolution

  # We are either limited by:
  # T_on * RO_sense
  roRes = 1 / (onTime * RO_LEN_TO_SENSE(roLength))

  # Counter size
  countRes = VOLTAGE_RANGE / (2 ** counterSize)

  # Code size
  codeRes = VOLTAGE_RANGE / (2 ** codeSize)

  # Interpolation error
  interpRes = interpResolution(ia)

  # Temperature-induced error
  # RO frequency * temperature error * Volts/Hertz
  tempRes = TEMP_PERCENT_ERROR * RO_LEN_TO_FREQ(roLength) * RO_LEN_TO_1DER(roLength)
  #return round(max(roRes, countRes, interpRes, tempRes), 3)
  return max(roRes, countRes, interpRes, tempRes, codeRes)

def space(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]
  lutSize = ia[4]
  codeSize = ia[5]

  # LUT size in bits
  return lutSize * codeSize

# Constraints must all be <= 0
def current_max(ia):
  return current(ia) - CURRENT_MAX

# Sampling frequency value is negative so need to flip sign here
def sampling_frequency_max(ia):
  return -1 * sampling_frequency(ia) - SAMPLING_FREQUENCY_MAX

def resolution_max(ia):
  return resolution(ia) - RESOLUTION_MAX

# Constraints must be <= 0
# value >= min --> -value <= -min -> -value + min <= 0 --> min - value <= 0
def current_min(ia):
  return CURRENT_MIN  - current(ia)

# Sampling frequency value is negative so need to flip sign here
def sampling_frequency_min(ia):
  return SAMPLING_FREQUENCY_MIN + sampling_frequency(ia)

def resolution_min(ia):
  return RESOLUTION_MIN - resolution(ia)

def space_min(ia):
  return -1 * (space(ia) - SPACE_MIN)

def space_max(ia):
  return space(ia) - SPACE_MAX

# Counter size places a constraint on the maximum resolution by constraining the
# count value
def counter_constraint_max(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]

  return -1 * (RO_FREQ_OFF_MEAN_HIGH * RO_LEN_TO_FREQ(roLength) * onTime) + (2 ** counterSize)

def counter_constraint_min(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]
  
  return -1 * (RO_FREQ_OFF_MEAN_LOW * RO_LEN_TO_FREQ(roLength) * onTime) * (2 ** counterSize)

# Never any reason for more LUT levels than RO levels
# However, I can have more RO levels than LUT levels: implies I am interpolating
def lut_counter_constraint(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]
  lutSize = ia[4]

  return lutSize - (2 ** counterSize)

# RO length must be odd
def ro_odd_constraint(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]

  if roLength % 2 == 0:
    return 1
  else:
    return 0

# Input array is array of: [Duty cycle D, RO length L, counter size S, on time T, LUT size B]

functional_problem = FunctionalProblem(6,                                               # Number of design variables
                                      #[current, sampling_frequency, resolution, space], # Objectives
                                      [current, sampling_frequency, resolution], # Objectives
                                      #[sampling_frequency, resolution], # Objectives
                                      #[current, resolution],
                                      constr_ieq=[current_max,                          # Inequality constraints
                                                  sampling_frequency_max,
                                                  resolution_max,
                                                  counter_constraint_max,
                                                  space_max,
                                                  current_min,
                                                  sampling_frequency_min,
                                                  resolution_min,
                                                  space_min,
                                                  counter_constraint_min,
                                                  #ro_odd_constraint,
                                                  lut_counter_constraint],
                                      xl=np.array([D_MIN, L_MIN, S_MIN, T_MIN, B_MIN, C_MIN]),  # Design variable lower bounds
                                      xu=np.array([D_MAX, L_MAX, S_MAX, T_MAX, B_MAX, C_MAX]))  # Design variable upper bounds

# Define data types for each input argument

# Duty cycle is real, RO length is int, counter size is int, on time is real, LUT size is int, counter size is int
mask = ["real", "int", "int", "real", "int", "int"]

sampling = MixedVariableSampling(mask, {
  "real": get_sampling("real_random"),
  "int": get_sampling("int_random"),
})


# I don't know what any of these parameters are
crossover = MixedVariableCrossover(mask, {
  "real": get_crossover("real_sbx", prob=1.0, eta=10.0),
  "int": get_crossover("int_sbx", prob=1.0, eta=10.0)
})

mutation = MixedVariableMutation(mask, {
    "real": get_mutation("real_pm", eta=10.0),
    "int": get_mutation("int_pm", eta=10.0)
})

algorithm = NSGA2(pop_size=500,
                  sampling=sampling,
                  crossover=crossover,
                  mutation=mutation)

res = minimize(functional_problem,
              algorithm,
              ("n_gen", 100),
              return_least_infeasible=True,
              eliminate_duplicates=False,
              verbose=True,
              seed=1)

with open("pickle_moo_no_nvm.dat", "wb") as f:
  np.savez(f, obj=res.F, des=res.X)

def counter_current_ia(ia):
  dutyCycle = ia[0]
  roLength = ia[1]
  counterSize = ia[2]
  onTime = ia[3]

  counterFrequency = RO_LEN_TO_FREQ(roLength)
  counterCurrent = counter_current(counterSize, counterFrequency)
  return dutyCycle * (counterCurrent)

print("Design space values: duty cycle, length, counter size, on time, LUT level count, code size")
print()
roForced = 0
countForced = 0
interpForced = 0
tempForced = 0
codeForced = 0

roResMean = 0
countResMean = 0
interpResMean = 0
tempResMean = 0

for i in res.X:
  print("--- Design Parameters ---")
  print(f"Duty cycle: {i[0]}")
  print(f"Length: {i[1]}")
  print(f"Counter size: {i[2]}")
  print(f"On time: {si_format(i[3])}S")
  print(f"LUT level count: {i[4]}")
  print(f"Code size: {i[5]}")

  print("--- Intermediate Results ---")
  print(f"RO on frequency: {si_format(RO_LEN_TO_FREQ(i[1]))}Hz")
  print(f"RO sensitivity: {si_format(RO_LEN_TO_SENSE(i[1]))}Hz/V")
  print(f"RO current: {si_format(RO_CURRENT * i[0])}A")
  print(f"Counter current: {si_format(counter_current_ia(i))}A")
  counterFrequency = RO_LEN_TO_FREQ(i[1])
  print(f"Shifter current: {si_format(SHIFTER_CURRENT(counterFrequency) * i[0])}A")
  print(f"Space consumption: {space(i) / 8}B")
  print()
  roRes = 1 / (i[3] * RO_LEN_TO_SENSE(i[1]))
  countRes = VOLTAGE_RANGE / (2 ** i[2])
  interpRes = interpResolution(i)
  tempRes = TEMP_PERCENT_ERROR * RO_LEN_TO_FREQ(i[1]) * RO_LEN_TO_1DER(i[1])
  codeRes = VOLTAGE_RANGE / (2 ** i[5])
  print(f"RO resolution: {si_format(roRes)}V")
  print(f"Counter resolution: {si_format(countRes)}V")
  print(f"Interpolation resolution: {si_format(interpRes)}V")
  print(f"Temperature-forced resolution: {si_format(tempRes)}V")
  print(f"Code resolution: {si_format(codeRes)}V")

  roResMean += roRes
  countResMean += countRes
  interpResMean += interpRes
  tempResMean += tempRes

  if resolution(i) == roRes:
    roForced += 1
  elif resolution(i) == countRes:
    countForced += 1
  elif resolution(i) == interpRes:
    interpForced += 1
  elif resolution(i) == tempRes:
    tempForced += 1
  elif resolution(i) == codeRes:
    codeForced += 1
  else:
    print("uuuuhhh")
    quit()

  print("--- Objectives ---")
  print(f"Current consumption: {si_format(current(i))}A")
  print(f"Sampling Frequency: {si_format(-1 * sampling_frequency(i))}Hz")
  print(f"Resolution: {si_format(resolution(i))}V")
  print()

count = len(res.X)
print("Resolution summary statistics")
print(f"{round(100 * roForced / count, 2)}% limited by RO resolution")
print(f"{round(100 * countForced / count, 2)}% limited by counter resolution")
print(f"{round(100 * interpForced / count, 2)}% limited by interpolation resolution")
print(f"{round(100 * tempForced / count, 2)}% limited by temperature resolution")
print(f"{round(100 * codeForced / count, 2)}% limited by code resolution")

for i in range(len(res.F)):
  res.F[i][0] = res.F[i][0] * 1e6           # Current (to micro-amps)
  res.F[i][1] = res.F[i][1] * 1e-3 * -1     # Sampling Frequency (to kilohertz)
  res.F[i][2] = res.F[i][2] * 1e3           # Resolution (to millivolts)
  #res.F[i][3] = res.F[i][3] / 1024          # NVM size (to kilobytes)

for i in range(len(res.X)):
  res.X[i][0] = res.X[i][0]                 # Duty cycle
  res.X[i][1] = res.X[i][1]                 # Length
  res.X[i][2] = res.X[i][2]                 # Counter size
  res.X[i][3] = res.X[i][3] * 1e6           # On time (to microseconds)
  res.X[i][4] = res.X[i][4]                 # LUT level count
  #res.X[i][4] = int(math.log2(res.X[i][4])) # LUT level count (to effective LUT bits)

# Objective space without plotting NVM size
plot = Scatter(title = "NVM Hidden", labels=["Current ($\mu$A)", "$F_s (kHz)$", "Resolution (mV)"])
plot.add(res.F)
plot.show()

print("Unique RO lengths:")
print(list(set(res.X[:,1])))
print("Unique counter sizes:")
print(list(set(res.X[:,2])))
print("Unique NVM entry counts:")
print(list(set(res.X[:,4])))
print("Unique code sizes:")
print(list(set(res.X[:,5])))
