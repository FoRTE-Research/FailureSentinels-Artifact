#! /usr/bin/python3

from pymoo.visualization.scatter import Scatter
import numpy as np
from si_prefix import si_format
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D

import seaborn as sns
sns.set()

# Point is a tuple of (current, sampling_freq, resolution)
# Each element of family is a tuple of similar type
# Point is Pareto dominated if there is an element in family with
# lower resolution and current
def isDominatedRvc(point, family):
  pC = point[0]
  pS = point[1]
  pR = point[2]
  if pC * 1e6 > 3:
    return True
  for i in family:
    iC = i[0]
    iS = i[1]
    iR = i[2]
    if iC < pC and iR < pR:
      return True
  return False

CURRENT_MIN = 0
CURRENT_MAX = 20 * 1e-6
SAMPLING_FREQUENCY_MIN = 1 * 1e3
SAMPLING_FREQUENCY_MAX = 10 * 1e3
RESOLUTION_MIN = 0
RESOLUTION_MAX = 50 * 1e-3
SPACE_MIN = 0
SPACE_MAX = 1 * 128 * 8 # 128 bytes

f = open("pickle_moo_no_nvm_90.dat", "rb")
npzfile = np.load(f, allow_pickle=True)
des = npzfile["des"]
obj = npzfile["obj"]
f.close()

print(des)

print(obj)

current = obj[:,0]
sampling_freq = obj[:,1]
resolution = obj[:,2]

desByCurrent = [x for _,x in sorted(zip(current, des), key=lambda pair: pair[0])]
objByCurrent = [x for _,x in sorted(zip(current, obj), key=lambda pair: pair[0])]
print()
print("-----")
print("Min current config:")
print(f"Duty cycle: {round(desByCurrent[0][0] * 100, 4)}%")
print(f"RO length: {desByCurrent[0][1]}")
print(f"Counter size: {desByCurrent[0][2]}")
print(f"On time: {si_format(desByCurrent[0][3], 3)}s")
print(f"LUT size: {desByCurrent[0][4]}")
print(f"Code size: {desByCurrent[0][5]}")
print()
print(f"Current: {si_format(objByCurrent[0][0], 3)}A")
print(f"Sampling frequency: {si_format(-1 * objByCurrent[0][1], 3)}Hz")
print(f"Resolution: {si_format(objByCurrent[0][2], 3)}V")
print()
print("Max current config:")
print(f"Duty cycle: {round(desByCurrent[-1][0] * 100, 4)}%")
print(f"RO length: {desByCurrent[-1][1]}")
print(f"Counter size: {desByCurrent[-1][2]}")
print(f"On time: {si_format(desByCurrent[-1][3], 3)}s")
print(f"LUT size: {desByCurrent[-1][4]}")
print(f"Code size: {desByCurrent[-1][5]}")
print()
print(f"Current: {si_format(objByCurrent[-1][0], 3)}A")
print(f"Sampling frequency: {si_format(-1 * objByCurrent[-1][1], 3)}Hz")
print(f"Resolution: {si_format(objByCurrent[-1][2], 3)}V")
print("-----")

iToRemove = []

for i in range(len(current)):
  if current[i] * 1e6 > 3:
    iToRemove.append(i)

print(iToRemove)

current = np.delete(current, iToRemove)
sampling_freq = np.delete(sampling_freq, iToRemove)
resolution = np.delete(resolution, iToRemove)

print(f"Min current: {si_format(min(current))}A")
print(f"Max current: {si_format(max(current))}A")

print(f"Min resolution: {min(resolution)}")
print(f"Max resolution: {max(resolution)}")

plt.scatter([i * 1e6 for i in current], [-1 * i * 1e-3 for i in sampling_freq], c=[i * 1e3 for i in resolution], marker='.', cmap='gray')
#plt.scatter([i * 1e6 for i in current], [i * 1e3 for i in resolution], c=[-1 * i * 1e-3 for i in sampling_freq], marker='.', cmap='gray_r')
#plt.scatter([-1 * i * 1e-3 for i in sampling_freq], [i * 1e3 for i in resolution], c=[i * 1e6 for i in current], marker='.', cmap='gray')

cb = plt.colorbar()
#cb.set_label("Current ($\mu$A)")
#plt.xlabel("Sampling Frequency (kHz)")
#plt.ylabel("Resolution (mV)")

cb.set_label("Resolution (mV)")
plt.xlabel("Current ($\mu$A)")
plt.ylabel("Sampling Frequency (kHz)")

plt.tight_layout()
plt.savefig("performance_scatter.pdf")
plt.close()
#plt.show()

#quit()

f = open("pickle_moo_no_nvm_130_1u.dat", "rb")
npzfile = np.load(f, allow_pickle=True)
obj = npzfile["obj"]
f.close()

points = obj

iToRemove = []
for i in range(len(points)):
  points[i][1] = -1 * points[i][1]
  if isDominatedRvc(points[i], points):
    iToRemove.append(i)

p2 = np.delete(points, iToRemove, 0)

current = p2[:,0]
sampling_frequency = p2[:,1]
resolution = p2[:,2]

currentInds = current.argsort()

plt.scatter(y=[i * 1e3 for i in resolution], x=[i * 1e6 for i in current], label="130nm")
#plt.plot(np.array([i * 1e6 for i in current])[currentInds[::1]], np.array([i * 1e3 for i in resolution])[currentInds[::1]],  label="130nm")

f = open("pickle_moo_no_nvm_90_1u.dat", "rb")
npzfile = np.load(f, allow_pickle=True)
obj = npzfile["obj"]
f.close()

f = open("pickle_moo_no_nvm_90_1u_part2.dat", "rb")
npzfile = np.load(f, allow_pickle=True)
obj2 = npzfile["obj"]
obj = np.concatenate((obj, obj2))
f.close()
points = obj

iToRemove = []
for i in range(len(points)):
  points[i][1] = -1 * points[i][1]
  if isDominatedRvc(points[i], points):
    iToRemove.append(i)

p2 = np.delete(points, iToRemove, 0)

current = p2[:,0]
sampling_frequency = p2[:,1]
resolution = p2[:,2]

currentInds = current.argsort()

plt.scatter(y=[i * 1e3 for i in resolution], x=[i * 1e6 for i in current], label="90nm")
#plt.plot(np.array([i * 1e6 for i in current])[currentInds[::1]], np.array([i * 1e3 for i in resolution])[currentInds[::1]],  label="90nm")

f = open("pickle_moo_no_nvm_65_1u.dat", "rb")
npzfile = np.load(f, allow_pickle=True)
obj = npzfile["obj"]
f.close()

f = open("pickle_moo_no_nvm_65_1u_part2.dat", "rb")
npzfile = np.load(f, allow_pickle=True)
obj2 = npzfile["obj"]
obj = np.concatenate((obj, obj2))
f.close()

f = open("pickle_moo_no_nvm_65_1u_part3.dat", "rb")
npzfile = np.load(f, allow_pickle=True)
obj2 = npzfile["obj"]
obj = np.concatenate((obj, obj2))
f.close()

points = obj

iToRemove = []
for i in range(len(points)):
  points[i][1] = -1 * points[i][1]
  if isDominatedRvc(points[i], points):
    iToRemove.append(i)

p2 = np.delete(points, iToRemove, 0)

current = p2[:,0]
sampling_frequency = p2[:,1]
resolution = p2[:,2]

currentInds = current.argsort()

plt.scatter(y=np.array([i * 1e3 for i in resolution])[currentInds[::1]], x=np.array([i * 1e6 for i in current])[currentInds[::1]], label="65nm")
#plt.plot(np.array([i * 1e6 for i in current])[currentInds[::1]], np.array([i * 1e3 for i in resolution])[currentInds[::1]],  label="65nm")

plt.xlabel("Current ($\mu$A)")
plt.ylabel("Resolution (mV)")
plt.legend()
plt.tight_layout()
plt.savefig("res_vs_current.pdf")
#plt.show()

# Design space
#plot = Scatter(title = "Design Space", labels=["Duty Cycle", "RO Length", "Counter Size", "On Time ($\mu$s)"], tight_layout=True)
#plot.add(des)
#plot.show()
