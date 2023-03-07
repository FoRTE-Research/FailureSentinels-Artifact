# Failure Sentinels ISCA 2021 Artifact
Failure Sentinels is a digital, integrated voltage supervisor with variable sample rate and resolution intended to support intermittent computation by continuously monitoring supply voltage in a low-power, low-cost manner.

This repository contains artifacts to enable reproduction of the experiments/results described in the ISCA 2021 paper "Failure Sentinels: Ubiquitous Just-in-time Intermittent Computation via Low-cost Hardware Support for Voltage Monitoring".

## Software pre-requisites
- git client
- LTSpice XVII
- wine
- Python 3
  - [ltspice](https://pypi.org/project/ltspice/) package for parsing LTSpice .raw files
- xvfb

##  Simulation Workflow
Our evaluation is based on simulations of the full system in LTSpice; netlist generation, simulation, and evaluation are all handled in various Python scripts.
This section describes how to run and customize the simulation workflow to generate the results we discuss in the paper.

### Netlist Generation
The high-level script for generating netlists is `generate_netlists.py`, which sets the Ring Oscillator (RO) length in inverters, supply voltages to evaluate the system at, and digital core voltage (the voltage the rest of the microcontroller operates at).
RO length and supply voltage are lists; the script will generate a netlist for each listed RO length operating at each listed supply voltage.
Internally, this script calls `ring_oscillator.py` (once for each RO length/supply voltage combination) which contains the basic LTSpice netlist for the entire system.
`ring_oscillator.py` generates an LTSpice netlist describing Failure Sentinels using the passed voltage/length parameters.
`generate_netlists.py` also produces a text file matching the name of the `NETLIST_FOLDER` variable containing a list of all the netlist filenames produced.

### Running Simulations
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
TODO

## Evaluation Workflow
TODO
