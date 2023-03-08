#! /usr/bin/python3

import os
import sys
import subprocess

if len(sys.argv) != 2:
  print("Provide batch file (line-separated list of .net files)")
  quit()

FILE = sys.argv[1]

if not os.path.exists(FILE):
  print(f"Netlist file {FILE} does not exist, exiting")
  quit()

netlists = []

with open(FILE, "r") as f:
  for line in f:
    if line[0] == "#":
      #print(f"Ignoring netlist: {line[1:]}")
      continue
    netlists.append(line.replace(".net\n", ".raw"))
    
for net in netlists:
  #os.system(f"./frequency.py {net} embedded")
  output = subprocess.check_output(f"./frequency.py {net} embedded", shell=True)
  print(output.decode(sys.stdout.encoding))
  #print()
