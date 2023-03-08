#! /usr/bin/python3

import sys
import os

# REMEMBER TO CHANGE LIBRARY AS WELL
NETLIST_FOLDER = "netlists_130_mcRun_7_61/"

LIB_NAME = "../Libraries/130nm_bulk.pm"

# Transistor geometry in nanometers
MOS_L = 130
NMOS_W = MOS_L * 2
PMOS_W = MOS_L * 4

SHIFTER_NMOS_W = MOS_L * 4
SHIFTER_PMOS_W = MOS_L * 2

# Oxide thickness in nanometers by technology
TOXM_N_90 = 2.05
TOXM_P_90 = 2.15

TOXM_N_130 = 2.25
TOXM_P_130 = 2.35

# Will probably have to do 180 in a different RO file anyway
TOXM_N_180 = 4
TOXM_P_180 = 4.2

CAP_90 = 7.3
RES_90 = 48.8

CAP_130 = 7.9
RES_130 = 24.4

CAP_180 = 6.4
RES_180 = 17.5

# Interconnect capacitance in femtofarads, resistance in ohms
inter_cap = CAP_130
inter_res = RES_130

toxm_n = TOXM_N_130
toxm_p = TOXM_P_130

print("Hello, world!")
if len(sys.argv) != 5:
  print("Provide an odd number of inverters to generate your RO, the desired operating voltage, the core voltage, and the MC tolerance")
  quit()

length = int(sys.argv[1])
voltage = float(sys.argv[2])
coreVoltage = float(sys.argv[3])
mcTol = float(sys.argv[4])
#TODO SET
toxMcTol = 0.05
interMcTol = 0.05

# Minimum length of 5 due to the way I generate the RO
if length % 2 == 0 or length < 5:
  print("Length must be an odd positive integer >= 5")
  quit()

if voltage > 1.1:
  print("Warning: voltage set higher than nominal 1.1V for 45nm LP PTM")

if not os.path.isdir(NETLIST_FOLDER):
  print(f"Creating netlist folder {NETLIST_FOLDER}")
  os.system(f"mkdir {NETLIST_FOLDER}")

print(f"Generating netlist in {NETLIST_FOLDER}")

name = f"ro_{length}_{voltage}v_mc{mcTol}"

print(f"Generating an RO with {length} inverters operating at {voltage} volts, core voltage = {coreVoltage} volts, mcTol = {mcTol}")
with open(NETLIST_FOLDER + f"{name}.net", "w") as f:
  f.write("* D:\\FailureSentinels\\Inverters\\Scripts\\ro_15.net\n") # This filename doesn't matter, but it has to exist
  # Vdd Vin Vout
  f.write(f"MX0N V_connect0 V0_out 0 0 MX0N_MOD l={MOS_L}n w={NMOS_W}n ad={{2 * {NMOS_W}n *{MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}\n")
  f.write(f"MX0P Vdd V0_out V_connect0 Vdd MX0P_MOD l={MOS_L}n w={PMOS_W}n ad={{2 * {NMOS_W}n *{MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}\n")
  f.write(f".model MX0N_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}\n")
  f.write(f".model MX0P_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}\n")

  #f.write(f"XW0 V_connect0 V1 interconnect\n")
  f.write(f"cw0_1 V_connect0 0 {{mc({inter_cap}f, {interMcTol})}}\n")
  f.write(f"cw0_2 V1 0 {{mc({inter_cap}f, {interMcTol})}}\n")
  f.write(f"rw0_1 V_connect0 V1 {{mc({inter_res}, {interMcTol})}}\n\n")

  # Manually writing first, last, and enable (NAND + NOT) -> 4 stages already
  # Create stages - 4 inverters here
  for i in range(1, length - 3):
    f.write(f"MX{i}N V_connect{i} V{i} 0 0 MX{i}N_MOD l={MOS_L}n w={NMOS_W}n ad={{2 * {NMOS_W}n *{MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}\n")
    f.write(f"MX{i}P Vdd V{i} V_connect{i} Vdd MX{i}P_MOD l={MOS_L}n w={PMOS_W}n ad={{2 * {NMOS_W}n *{MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}\n")
    f.write(f".model MX{i}N_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}\n")
    f.write(f".model MX{i}P_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}\n")
    #f.write(f"XW{i} V_connect{i} V{i+1} interconnect\n")
    f.write(f"cw{i}_1 V_connect{i} 0 {{mc({inter_cap}f, {interMcTol})}}\n")
    f.write(f"cw{i}_2 V{i+1} 0 {{mc({inter_cap}f, {interMcTol})}}\n")
    f.write(f"rw{i}_1 V_connect{i} V{i+1} {{mc({inter_res}, {interMcTol})}}\n\n")

  # Last inverter, connected to enable input
  f.write(f"MX{length - 3}N V0_in V{length - 3} 0 0 MX{length - 3}N_MOD l={MOS_L}n w={NMOS_W}n ad={{2 * {NMOS_W}n *{MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}\n")
  f.write(f"MX{length - 3}P Vdd V{length - 3} V0_in Vdd MX{length - 3}P_MOD l={MOS_L}n w={PMOS_W}n ad={{2 * {NMOS_W}n *{MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}\n")
  f.write(f".model MX{length - 3}N_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}\n")
  f.write(f".model MX{length - 3}P_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}\n")
  # TODO CHANGE TODO DIVIDER TODO MCTOL TODO
  f.write(
f"""
; Vdd is supply to RO
; Vsupply is supply to voltage divider
V_power Vsupply 0 PWL(0 0 0.5u {voltage})
V_enable enable 0 PWL(0 0 0.59u 0 0.6u {coreVoltage} 0.69u {coreVoltage} 0.7u {coreVoltage})
V_core Vcore 0 PWL(0 0 0.5u {coreVoltage})

; Voltage divider
; Drain gate source base
; Vdd is supply to RO, Vsupply is supply to voltage divider
; Divide by 3
M_div1 Vsupply Vdiv Vdiv Vsupply M_div1_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({PMOS_W}n, {mcTol})}} ad={{2 * {PMOS_W}n * {MOS_L}n}} as={{2 * {PMOS_W}n * {MOS_L}n}} pd={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}}
M_div4 Vdiv Vdd Vdd Vdiv M_div4_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({PMOS_W}n, {mcTol})}} ad={{2 * {PMOS_W}n * {MOS_L}n}} as={{2 * {PMOS_W}n * {MOS_L}n}} pd={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}}
M_div2 Vdd Vbottom Vbottom Vdd M_div2_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({PMOS_W}n, {mcTol})}} ad={{2 * {PMOS_W}n * {MOS_L}n}} as={{2 * {PMOS_W}n * {MOS_L}n}} pd={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}}
M_div3 Vbottom enable 0 0 M_div3_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({NMOS_W}n, {mcTol})}} ad={{2 * {NMOS_W}n * {MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}

;.model M_div1_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}
;.model M_div4_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}
;.model M_div2_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}
;.model M_div3_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}

.model M_div1_MOD ako: PMOS toxm={{mc({toxm_p}n, {0.0})}}
.model M_div4_MOD ako: PMOS toxm={{mc({toxm_p}n, {0.0})}}
.model M_div2_MOD ako: PMOS toxm={{mc({toxm_p}n, {0.0})}}
.model M_div3_MOD ako: NMOS toxm={{mc({toxm_n}n, {0.0})}}

; Level shifter
M_shifter_n1 shifter_node V_connect0 0 0 M_shifter_n1_MOD l={MOS_L}n w={SHIFTER_NMOS_W}n ad={{2 * {SHIFTER_NMOS_W}n * {MOS_L}n}} as={{2 * {SHIFTER_NMOS_W}n * {MOS_L}n}} pd={{2 * ({SHIFTER_NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({SHIFTER_NMOS_W}n + 2 * {MOS_L}n)}}
M_shifter_n2 shifter_out v0_out 0 0 M_shifter_n2_MOD l={MOS_L}n w={SHIFTER_NMOS_W}n ad={{2 * {SHIFTER_NMOS_W}n * {MOS_L}n}} as={{2 * {SHIFTER_NMOS_W}n * {MOS_L}n}} pd={{2 * ({SHIFTER_NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({SHIFTER_NMOS_W}n + 2 * {MOS_L}n)}}
M_shifter_p1 Vcore shifter_out shifter_node Vcore M_shifter_p1_MOD l={MOS_L}n w={SHIFTER_PMOS_W}n ad={{2 * {SHIFTER_PMOS_W}n * {MOS_L}n}} as={{2 * {SHIFTER_PMOS_W}n * {MOS_L}n}} pd={{2 * ({SHIFTER_PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({SHIFTER_PMOS_W}n + 2 * {MOS_L}n)}}
M_shifter_p2 Vcore shifter_node shifter_out Vcore M_shifter_p2_MOD l={MOS_L}n w={SHIFTER_PMOS_W}n ad={{2 * {SHIFTER_PMOS_W}n * {MOS_L}n}} as={{2 * {SHIFTER_PMOS_W}n * {MOS_L}n}} pd={{2 * ({SHIFTER_PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({SHIFTER_PMOS_W}n + 2 * {MOS_L}n)}}

.model M_shifter_n1_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}
.model M_shifter_n2_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}
.model M_shifter_p1_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}
.model M_shifter_p2_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}

; Enable circuit
M_en1 internal1 enable 0 0 M_en1_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({NMOS_W}n, {mcTol})}} ad={{2 * {NMOS_W}n * {MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}
M_en2 Vdd V0_in internal2 Vdd M_en2_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({PMOS_W}n, {mcTol})}} ad={{2 * {PMOS_W}n * {MOS_L}n}} as={{2 * {PMOS_W}n * {MOS_L}n}} pd={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}}
M_en3 Vdd enable internal2 Vdd M_en3_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({PMOS_W}n, {mcTol})}} ad={{2 * {PMOS_W}n * {MOS_L}n}} as={{2 * {PMOS_W}n * {MOS_L}n}} pd={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}}
M_en4 internal2 v0_in internal1 0 M_en4_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({NMOS_W}n, {mcTol})}} ad={{2 * {NMOS_W}n * {MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}
M_en5 Vdd internal2 V0_out Vdd M_en5_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({PMOS_W}n, {mcTol})}} ad={{2 * {PMOS_W}n * {MOS_L}n}} as={{2 * {PMOS_W}n * {MOS_L}n}} pd={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({PMOS_W}n + 2 * {MOS_L}n)}}
M_en6 V0_out internal2 0 0 M_en6_MOD l={{mc({MOS_L}n, {mcTol})}} w={{mc({NMOS_W}n, {mcTol})}} ad={{2 * {NMOS_W}n * {MOS_L}n}} as={{2 * {NMOS_W}n * {MOS_L}n}} pd={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}} ps={{2 * ({NMOS_W}n + 2 * {MOS_L}n)}}

.model M_en1_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}
.model M_en2_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}
.model M_en3_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}
.model M_en4_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}
.model M_en5_MOD ako: PMOS toxm={{mc({toxm_p}n, {toxMcTol})}}
.model M_en6_MOD ako: NMOS toxm={{mc({toxm_n}n, {toxMcTol})}}

.model NMOS NMOS
.model PMOS PMOS
.lib "{LIB_NAME}"
.step param seed 0 49 1
;.param seed=0
.tran 0 2u 0.75u 10n
.save V(shifter_out) V(Vsupply) I(V_power) V(v0_out) V(v0_in) V(Vcore) I(V_core)
.end
""")

print("Done")
