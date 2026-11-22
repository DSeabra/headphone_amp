# Condor cab-sim insert (Rev A trial board)

KiCad 7+ project, 1.0 x 1.0 in, 4 layers (OSH Park 4-layer). In1 = VMID plane, In2 = GND0 plane.

## Before ordering (required)
1. Open `condor_insert.kicad_pro` in KiCad.
2. Schematic: run ERC. PCB: Tools > Update PCB from Schematic (tick "re-link by reference" if offered), then
   Tools > Update Footprints from Library to pull the official pad geometry (JST SH especially).
3. Press **B** (fill all zones). The inner planes are saved unfilled; without this step the VMID/GND0 planes are missing.
4. Run DRC, save, then upload the .kicad_pcb (or Gerbers) to OSH Park, 4-layer service.

## Wiring
- J1 <- short JST-SH 3-way cable, pin 1 to pin 1, from main-board J6 (pin3 = recovery out, pin2 = wiper, pin1 = VMID).
- J2 <- the volume pot pigtail (unplugged from J6).
- J3 <- flying leads: pin 1 (square) = +9 V (V+9A), pin 2 = GND0.
- A/B test: unplug the insert and plug the pot straight back into J6.

## Build options
See the notes on the schematic and condor_insert_BOM.csv (input level, notch depth, Marshall voicing, U1 alternative).
