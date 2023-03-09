# Failure Sentinels ISCA 2021 Artifact
Failure Sentinels is a digital, integrated voltage supervisor with variable sample rate and resolution intended to support intermittent computation by continuously monitoring supply voltage in a low-power, low-cost manner.

This repository contains artifacts to enable reproduction of the experiments/results described in the ISCA 2021 paper "Failure Sentinels: Ubiquitous Just-in-time Intermittent Computation via Low-cost Hardware Support for Voltage Monitoring".

## Software pre-requisites
- git client
- LTSpice XVII
- wine
- Python 3
  - [ltspice](https://pypi.org/project/ltspice/) package for parsing LTSpice .raw files
  - [pymoo version 0.5.0](https://pypi.org/project/pymoo/0.5.0/) package for multi-objective optimization
- xvfb

##  Circuit Simulation Workflow
Our evaluation is based on simulations of the full system in LTSpice; netlist generation, simulation, and evaluation are all handled in various Python scripts.
This section describes how to run and customize the simulation workflow to generate the results we discuss in the paper.

### Netlist Generation
The high-level script for generating netlists is `generate_netlists.py`, which sets the Ring Oscillator (RO) length in inverters, supply voltages to evaluate the system at, and digital core voltage (the voltage the rest of the microcontroller operates at).
RO length and supply voltage are lists; the script will generate a netlist for each listed RO length operating at each listed supply voltage.
Internally, this script calls `ring_oscillator.py` (once for each RO length/supply voltage combination) which contains the basic LTSpice netlist for the entire system.
`ring_oscillator.py` generates an LTSpice netlist describing Failure Sentinels using the passed voltage/length parameters.
`generate_netlists.py` also produces a text file matching the name of the `NETLIST_FOLDER` variable containing a list of all the netlist filenames produced.

### Running SPICE Simulations
LTSpice is Windows-only software; we have to run it using wine, which in turn requires more support as we want to programatically call it from Python and ignore the grapical output.
Generate a virtual "display" for wine by calling `xvfb` (X Virtual FrameBuffer) from the command line: `Xvfb :2 -screen 0 1024x768x24 &`.
Once this is done, we are ready to run the simulations.

The high-level script controlling simulation is `mt_runner.py` (Multithread Runner), which launches an LTSpice instance to simulate each netlist.
SPICE simulations of large ROs can take a long time and are difficult to multi-thread; to speed up simulation, `mt_runner.py` parallelizes at the process level by running a separate LTSpice instance for each netlist across different threads.
The script defaults to 8 threads, but this can be changed based on your machine's core count.
Once each netlist's simulation is complete, the results will be available in the netlist folder with names corresponding to each individual netlist (e.g., `netlists_130_mcRun_7_61/ro_7_2.0v_mc0.0.net` --> `netlists_130_mcRun_7_61/ro_7_2.0v_mc0.0.log`).

### Simulation Results
LTSpice outputs simulation results in binary .raw files which can be read by the Python `ltspice` package.
The netlist specifies what to write to the output file.
To reduce filesize and increase simulation speed, our netlists by default only save several voltages and currents:
- Voltage level output of the RO -> core level shifter
- RO supply voltage
- Current into Failure Sentinels through the voltage divider
- Voltage level at two internal RO nodes (before and after the enable gate)
- Core voltage
- Core current

These are specified at the bottom of the netlist (and generated at the bottom of `ring_oscillator.py`).
The simulations also include partial support for Monte-Carlo simulations; the values subject to random variation are the transistor oxide thickness, interconnect equivalent resistance, and interconnect equivalent capacitance.
By default, each netlist runs 50 times to generate a statistically significant dataset for evaluation: this is specified by the `.step param seed 0 49 1` line also at the bottom of the netlist.
If you do not need the Monte-Carlo results, you can remove this line and replace it with the following which is by default commented out (`.param seed=0`).
This should speed up the simulations by about 50x.

### Changing Technologies
We evaluate Failure Sentinels across several transistor technology nodes (130nm, 90nm, and 65nm).
To simulate with a different technology, just change the `LIB_NAME` variable in `ring_oscillator.py` to point to a new transistor model file.

## Circuit Evaluation Workflow
Similar to the simulation workflow, the evaluation is based on a set of Python scripts.

### RO Frequency
The low-level script that measures RO frequency from an LTSpice .raw file is `frequency.py`; running this on a single .raw file will output a summary of the RO's performance at that point (frequency, power, and output amplitude).
The `auto_freq.py` script takes as an argument the text file produced by the `generate_netlists.py` script pointing to all of the individual netlists within a directory and runs `frequency.py` on each of them.
The output for each netlist is an abridged version of the regular `frequency.py` output in a csv format for easier processing later.
Pipe the output of this file to a new file (e.g., `./auto_freq.py netlists_130.txt > netlists_130_freq.csv`).
Because we are interested in frequency versus voltage, we have the `fvs_list.py` script to isolate frequency and voltage in a more convenient format: run it on the frequency csv file just generated and pipe the output to another file (`./fvs_list.py netlists_130_freq.csv > netlists_130_fvs.csv`).
The information in this csv can be combined with similar csv files for other technology nodes by prepending the feature size in nm and concatenating the files (do this manually).
A properly formatted frequency file is a csv with the format:
```
[feature size in nm],[RO length in inverters],[frequency at 1.8v],[frequency at 1.9v], ... ,[frequency at 3.6v]
```
Finally, the `comparison_plotter.py` script uses this file to plot RO frequency versus voltage, feature size, and RO length similar to what is seen in Figure 1 of the paper; it also plots the derivative of frequency with respect to voltage (Figure 3 in the paper).

### LUT Interpolation Error
Accuracy of the system also depends on error introduced by LUT interpolation.
The `error.py` script takes no arguments and outputs a plot showing the interpolation error of piecewise constant interpolation and piecewise linear interpoluation (Figure 4 in the paper).
The accuracy of interpolation depends on the maximum values of the first and second derivatives of the function being represented, which are available to change in the script as `MAX_FIRST` and `MAX_SECOND`, respectively.

### Design Space Exploration
There are a variety of hardware configurations available to implement Failure Sentinels; performance in each metric (current consumption, sampling rate, accuracy) is interconnected and depends on various design choices (RO length, duty cycle, counter size, LUT design).
We explore the design space using the `pymoo` optimization library.
The `moo_no_nvm_updated_rvc.py` script runs the optimization and outputs a set of optimal design points based on analytical models of each system in each technology node (these are defined in the beginning of the script).
It outputs a data file `pickle_moo_no_nvm.dat` containing the design and performance metrics.
The `unpickle_moo.py` script unpacks several of these data files to produce the plots shown in Figures 5 and 6 of the paper.
This repo contains the .dat files the `unpickle_moo.py` script looks for by default (i.e., our previous runs on the 130nm, 90nm, and 65nm nodes) so that you can run it and quickly reproduce the figures in the paper.

## System Evaluation Workflow
We quantify Failure Sentinels's system-level effect using a simulated solar energy harvester (more details in the paper).
The files for the system simulation are in the `sim/` directory.
The simulator is implemented in `overhead.py`, and by default simulates the system using the low-power implementation of Failure Sentinels.
Values for the high-performance version and the baseline systems (ADC and comparator) are commented out in the script and can be easily switched in; the relevant values are `MCU_ACTIVE_CURRENT` and `RESOLUTION`.
Changing any of the other values (e.g., checkpointing performance, voltage thresholds, capacitor size, etc.) allows you to test the system under different conditions.
The `plot_overhead.py` script shows the runtime reduction of each system (Figure 8 in the paper); the specific values are coded into the script and are from running the `overhead.py` script under each condition shown.
