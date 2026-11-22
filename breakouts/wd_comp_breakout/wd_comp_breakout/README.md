# Watchdog comparator breakout (TLV7011), Rev A rework board

**Date:** 2026-11-21 (v4: four M2.5 unplated mounting holes, rounded corners; JST SH 6-pin right-angle connector, full value silkscreen, RV1 removed) · Implements the comparator from `RevA-Watchdog-Comparator-Plan.md` / `RevA-Comparator-Starting-Values.md` (Set A) as a small board you wire into a Rev A unit in place of the U7A → AUDIO_DETECT path. Not built or measured; thresholds are calculated.

## Board

- 25.4 × 25.4 mm (1 × 1 in), 2 layers, 1.6 mm, **2 mm corner radius**.
- **Four M2.5 mounting holes**: 2.7 mm unplated (NPTH), centred 3.0 mm from each edge, so the hole edge sits 1.65 mm from the board edge. Hole centres are 19.4 mm apart in both directions. Each hole has a 3 mm radius keepout (6 mm diameter, enough for a 5 mm screw head, M2.5 washer or standoff): no copper, vias or silk inside it, and the bottom GND pour is cut back to 3.2 mm. Unplated holes add no copper rings on the bottom, so VHB mounting still works; use screws or VHB, or both.
- **Everything is surface-mount on the top side**: 0603 passives, SOT-23-5 comparator, and J1 = JST SH 6-pin right-angle header (SM06B-SRSS-TB, 1.0 mm pitch). The bottom has no through-hole pads, only tented vias, bottom traces and the GND pour under solder mask. That makes it flat for VHB.
- **J1 placement:** centred on the bottom edge with the opening facing out, so the plug goes in from the board edge. The mounting tabs are toward the edge, 0.5 mm in from it, and the header body ends about 0.8 mm inside the edge. Footprint geometry matches KiCad's stock `Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal` (signal pads 0.6 × 1.55 mm at y = −2, tabs 1.2 × 1.8 mm at ±3.8, +1.875). The tabs are left unconnected (mechanical only).
- **Mounting:** VHB on the bottom (the silk there says so), or M2.5 screws/standoffs through the corner holes. The bottom silk (Set A values and the hookup map) will be hidden once mounted, so the same information is in this README.
- **Top silk:** reference, value and "DNP" next to every part (0.8 mm text, 0.13 mm stroke, above OSH Park's 5 mil minimum line width), a J1 pin legend on the left edge (J1-1 GND … J1-6 GND, moved out of the hole keepouts) plus a pin‑1 triangle at the connector, and "SET A" by the reference divider.
- Rules used: 0.25 mm signal / 0.4 mm power tracks, ≥ 0.35 mm copper clearance, 0.6/0.3 mm vias, ≥ 1.9 mm copper to edge. OSH Park 2-layer limits are 6 mil / 6 mil, 10 mil drill; Board Setup is preset to those.
- Bottom layer has a GND pour (zone, **unfilled in the file**). Every GND pad is also connected by a track, so the board works even if the pour is never filled.

## J1 pinout (JST SH 6; pin 1 is on the left looking down at the top with the opening toward you)

| Pin | Silk | Net | Wire to on Rev A |
|---|---|---|---|
| 1 | GND | GND | U8 pin 7 |
| 2 | DET | AUDIO_DETECT (comparator OUT) | U8 pin 9 / TP8 side **after cutting** AUDIO_DETECT between U7.2 and U8.9 (the diagonal F.Cu segment near (95.64, 77.26)) |
| 3 | THR | ENV_THRESHOLD (comparator IN+) | R30/R31 junction (also U7 pin 1) |
| 4 | VL | V_LOGIC (2.5 V) | C26 |
| 5 | REF | VREF (IN−) | probe only, expect about 0.30 V (calc) |
| 6 | GND | GND | probe ground / second GND wire |

The SH cable's far end gets soldered to the Rev A points above. Pin numbering follows the housing, so check which wire color lands on pin 1 in your cable before soldering the Rev A end.

THR is a high-impedance node (about 235 kΩ from R30 ∥ R31, with R3 feeding back). Keep that wire short and twisted with a GND wire. If it picks up hum, fit C3 (about 1 nF; 0.24 ms against R30 ∥ R31, negligible next to the 0.2 s envelope).

## Schematic summary

- U1 TLV7011 on V_LOGIC with C1 100 nF. Pinout per TI SLVSDM5F (SOT-23-5): 1 OUT, 2 VEE, 3 IN+, 4 IN−, 5 VCC.
- IN− = Vref from R1 (Rt) / R2 (Rb) with C2 10 nF.
- R3 (Rh) from OUT to IN+ for hysteresis.
- Rb = R2 + R5, two 0603s in series to GND (R5 = 0 Ω for Set A). Swap either one to tune. For an adjustable threshold, remove R5 and wire a small trimmer across its pads. The through-hole RV1 footprint from v1 is gone, because its leads would have stuck out of the bottom.
- R4 (DNP) pull-up to V_LOGIC, only needed for the open-drain TLV7021.

Math (also printed on the schematic and bottom silk), R30 = R31 = 470 k on the main board:

- Vref = 2.5 × 30 k / 250 k = 0.30 V
- Trip (at ENV_HOLD) = Vref × (1 + R30/R31 + R30/R3) = 0.30 × 2.1 = 0.63 V
- Release = Trip − V_LOGIC × R30/R3 = 0.63 − 0.25 = 0.38 V
- The TLV7011's internal hysteresis moves each threshold by about 4 mV (simulation note).

## BOM

| Ref | Value | Package | Fit | Note |
|---|---|---|---|---|
| U1 | TLV7011DBVR (silk/value "TLV7011") | SOT-23-5 | yes | TLV7021DBVR also fits (then fit R4) |
| R1 | 220 k 1 % | 0603 | yes | Rt |
| R2 | 30 k 1 % | 0603 | yes | Rb; Set B and B+: 20 k |
| R3 | 4.7 M 1 % | 0603 | yes | Rh; Set B and B+: 10 M |
| R4 | 100 k | 0603 | DNP | TLV7021 only |
| R5 | 0 Ω | 0603 | yes | second Rb element (Rb = R2 + R5); or a solder bridge |
| C1 | 100 nF X7R | 0603 | yes | |
| C2 | 10 nF X7R | 0603 | yes | |
| C3 | 1 nF C0G | 0603 | DNP | IN+ filter, only if needed |
| H1–H4 | M2.5 mounting hole | 2.7 mm NPTH | — | no part; KiCad `MountingHole:MountingHole_2.7mm_M2.5` |
| J1 | JST SM06B-SRSS-TB(LF)(SN) | SH 6-pin R/A SMD | yes | mates with SHR-06V-S(-B) housing / pre-crimped SH cables (28 to 32 AWG) |

| Set | R2 | R3 | R5 | Trip / release at ENV_HOLD (calc) |
|---|---|---|---|---|
| A (default) | 30 k | 4.7 M | R5 0 Ω | 0.63 / 0.38 V |
| B | 20 k | 10 M | R5 0 Ω | 0.43 / 0.31 V |
| B+ | 20 k | 10 M | R5 removed, 20 k trimmer wired across R5 pads | 0.43 to 0.79 / 0.31 to 0.67 V |

## Before ordering (KiCad)

These files were generated by script without a KiCad install. I parsed them back and checked: every net fully routed, no shorts, clearances, track ends, copper-to-edge, silk on pads, and schematic netlist against PCB pad nets (27 pins, 0 mismatches), and silk size, silk-on-pad/via, silk-on-silk, no through-hole pads, a closed outline with 2 mm arcs, and the 3 mm hole keepouts (nearest copper 4.0 mm, nearest silk 3.1 mm from a hole centre). KiCad's own ERC and DRC have **not** been run.

1. Open `wd_comp_breakout.kicad_pro` in KiCad. The files are in KiCad 7 format, so KiCad 8 and later will convert them on save.
2. Schematic: run ERC. Expect at most library-mismatch warnings. The project library `wd_comp_breakout` holds TLV7011DBV and V_LOGIC (plus an unused R_Trim symbol), J1 uses the stock KiCad footprint name, so no project footprint library is needed.
3. PCB: press **B** (fill zones), then run DRC. A rotation-convention error on my side would show up here at once as unconnected pads. Optional: Tools → Update Footprints from Library to swap my hand-written copies of the stock SOT-23-5 / 0603 / JST SH / mounting-hole footprints for the library ones. Updating also resets the silk text positions, so only do it if you're happy to re-place the labels.
4. Save, then order:
   - OSH Park accepts `.kicad_pcb` directly but **does not refill zones**, so fill and save first. Their docs say they process with KiCad 8, so a file saved by a newer KiCad may not import.
   - Safer route from a newer KiCad: File → Plot Gerbers (F.Cu, B.Cu, F/B Mask, F/B Silk, Edge.Cuts) plus an Excellon drill file. Zip them and upload. Leave vias tented (the KiCad default) so the VHB side is all mask.

## After wiring (from the Starting Values note)

- Idle: THR about 0 V, DET low, REF about 0.30 V.
- Pluck, then hard strum: DET goes high, and releases about 0.2 s after the last note.
- Full drive and volume with nothing played: DET must stay low. This decides Set A versus B.
- Then D4, and the timed shutdown (about 10.2 min calc, or about 6 s with C23 temporarily at 6.8 nF).

## Files

- `wd_comp_breakout.kicad_pro / .kicad_sch / .kicad_pcb`: project, schematic, layout
- `wd_comp_breakout.kicad_sym`, `sym-lib-table`: project symbol library
- `preview_top.png`, `preview_bottom.png`, `preview_sch.png`: renders from my own plotter (approximate fonts), not KiCad
