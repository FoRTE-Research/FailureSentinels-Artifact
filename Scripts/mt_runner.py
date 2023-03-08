#! /usr/bin/python3

import os
import multiprocessing as mp
import sys
import time

def worker(runCmd):
  os.system(runCmd)

if __name__ == "__main__":
  RUN_CMD = "DISPLAY=:2 wine ~/.wine/drive_c/Program\ Files/LTC/LTspiceXVII/XVIIx64.exe -Run -b {}"
  THREAD_LIMIT = 8

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
      if line[0] == '#':
        print(f"Skipping line {line}")
        continue
      netlists.append(line.replace("\n", "")) # Get rid of the \n character
  
  print("Starting processes + timer")
  start_time = time.time()
  processArray = []
  for net in netlists:
    processArray.append(mp.Process(target=worker, args=(RUN_CMD.format(net),)))
    #processArray[-1].start()

  for i in range(0, len(processArray), THREAD_LIMIT):
    runningArray = processArray[i:i+THREAD_LIMIT]
    print(f"Starting running array: {runningArray}")
    sub_time = time.time()
    for p in runningArray:
      p.start()
    for p in runningArray:
      p.join()
    print(f"Finished running array: {runningArray}")
    print(f"Time elapsed: {time.time() - sub_time}")
    print()

  print(f"Done, run time = {time.time() - start_time}")
