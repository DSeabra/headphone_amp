---
title: Guitar Headphone Amp — Connectivity & Netlist (living doc)
project: pocket guitar headphone amp (rev A)
status: design in progress
tags: [electronics, schematic, netlist, guitar]
---

# Connectivity & Netlist — rev A (working)

> [!info] How to read this
> This is the **source-of-truth wiring** as a human netlist: each stage has a light ASCII signal-flow line for gestalt, then a **connection table** (`Ref · Value · Net A · Net B · Notes`) that is unambiguous and easy to edit. Values shown are defined so far; `TBD` marks open items. Render a *picture* of any stage in KiCad/SchemDraw when wanted — this text stays the master.

## Global nets (rails)

| Net | Meaning |
|---|---|
| `V+6` | +6 V rail (boost output) |
| `VGND` | virtual ground = 3 V (mid-rail signal reference, from TLE2426) |
| `GND0` | 0 V = battery-negative (power return + headphone return) |

All op-amps are powered `V+6` / `GND0`. All AC signals are referenced to `VGND`.

---

## Power section

```
USB-C ─▶ power-path charger ─┬─▶ SYS ─▶ boost(+6V) ─▶ TLE2426 ─▶ VGND (3V)
                             └── BAT ── Li-ion cell
```

**USB-C + charger**

| Ref | Value | Net A | Net B | Notes |
|---|---|---|---|---|
| J_USB VBUS | — | `VBUS` | charger VIN | |
| R_CC1 | 5.1 kΩ | CC1 | `GND0` | sink identification |
| R_CC2 | 5.1 kΩ | CC2 | `GND0` | sink identification |
| D_ESD | — | `VBUS`/D± | `GND0` | ESD array |
| U_CHG | power-path (BQ2407x / MCP73871 class — **TBD**) | `VBUS`→VIN | `SYS`, `BAT` | SYS feeds boost, not BAT |
| R_ISET | **TBD** | ISET | `GND0` | sets charge current |
| D_STAT | — | STAT | LED | charge-status indicator |
| BT1 | Li-ion, protected, 3.0–4.2 V | `BAT` | `GND0` | protection IC on cell |

**Boost + rail splitter**

| Ref | Value | Net A | Net B | Notes |
|---|---|---|---|---|
| U_BOOST | plain boost → 6 V, high Fsw (**part TBD**) | `SYS` (VIN) | `V+6` (VOUT) | EN gated by charger PG or own UVLO |
| L_BOOST | **TBD** | — | — | keep away from input / feedback nets |
| C_IN_B | **TBD** | `SYS` | `GND0` | input cap |
| C_OUT_B | **TBD** | `V+6` | `GND0` | output cap |
| FB divider | **TBD** | FB | — | sets 6 V |
| FB_BEAD | ferrite bead | `V+6` | `V+6A` | bead + caps = clean audio rail (`V+6A`) |
| U_SPLIT | TLE2426 (SOIC-8) | `V+6` (IN) | `VGND` (OUT) | COMMON → `GND0` |
| C_NR | 1 µF | NR pin | `GND0` | drops splitter noise 120→30 µV |
| DNP: LDO | — | — | — | footprint only, not populated |

---

## Stage A — DRIVE  (OPA1678-A, non-inverting)

Does three jobs: hi-Z input, gain, soft clip. Feedback leg = `Rf_fixed + drive pot`; clip diodes and `C_fb` sit **across that leg**; the `Rg`-in-series-with-`Cg` leg sets DC gain = 1 and the ~720 Hz low cut.

```
TIP ─[R_ser 1k]─┬─[C_in 0.1µ]─▶ (+)┐
                │                   │ OPA1678-A ─▶ N_DRV_OUT ─▶ (to Stage B)
             [C_rf 470p]         (−)┘        ▲
                │              N_A_MINUS ─────┘ feedback leg + diodes + C_fb
               GND0
```

**Connections**

| Ref | Value | Net A | Net B | Notes |
|---|---|---|---|---|
| R_ser | 1 kΩ | `TIP` | `N_RF` | RF/input series R |
| C_rf | 470 pF | `N_RF` | `GND0` | RF/hum shunt (~340 kHz w/ R_ser) |
| C_in | 0.1 µF film | `N_RF` | `N_A_PLUS` | input DC block (~1.6 Hz w/ R_bias) |
| R_bias | 1 MΩ | `N_A_PLUS` | `VGND` | high-Z input + mid-rail bias |
| U1A + in | — | `N_A_PLUS` | — | OPA1678-A pin |
| U1A − in | — | `N_A_MINUS` | — | OPA1678-A pin |
| U1A out | — | `N_DRV_OUT` | — | OPA1678-A pin |
| Rg | 4.7 kΩ | `N_A_MINUS` | `N_A_G` | lower gain leg |
| Cg | 47 nF | `N_A_G` | `VGND` | DC-block (gain=1 @ DC) + low-cut ~720 Hz |
| Rf_fixed | 51 kΩ | `N_DRV_OUT` | `N_A_FB` | sets min gain (~12×) |
| RV_DRIVE | 500 kΩ **taper TBD** (start linear) | `N_A_FB` | `N_A_MINUS` | drive control; max gain ~118× |
| D_clip1 | 1N4148 (**socketed**) | `N_DRV_OUT` | `N_A_MINUS` | soft clip, anti-parallel |
| D_clip2 | 1N4148 (**socketed**) | `N_A_MINUS` | `N_DRV_OUT` | (swap types/asym to taste) |
| C_fb | 51 pF | `N_DRV_OUT` | `N_A_MINUS` | high-cut, stability |

> [!note] Open in this stage
> `RV_DRIVE` taper (start linear, try audio) · `Cg` value (bass into clipper) · diode recipe (Si/Ge/LED, sym/asym) — all bench-tuned, diodes socketed.

---

## Stage B — RECOVERY + VOLUME  (OPA1678-B, inverting, gain ≈ 3×)

Inverting, so the **+ input** carries the mid-rail reference and signal enters the **− input** through `R_in`. Needs a series DC-block on `R_in`. Hard-clip diodes provisioned **before** the volume pot (fixed-level node) so they clip consistently if ever populated.

```
N_DRV_OUT ─[C_inB 0.1µ]─[R_in 33k]─▶ (−)┐
                                         │ OPA1678-B ─▶ N_B_OUT ─▶ Vol ─▶ (to OPA1622)
                          VGND ─[R_ref]─▶(+)┘     ▲
                                    N_B_MINUS ─────┘ Rf_B 100k (feedback)
```

**Connections**

| Ref | Value | Net A | Net B | Notes |
|---|---|---|---|---|
| C_inB | 0.1 µF | `N_DRV_OUT` | `N_B_IN` | DC block (~48 Hz w/ R_in) |
| R_in | 33 kΩ | `N_B_IN` | `N_B_MINUS` | inverting input resistor |
| R_ref | 100 kΩ | `N_B_PLUS` | `VGND` | sets mid-rail bias on + input |
| U1B + in | — | `N_B_PLUS` | — | OPA1678-B pin |
| U1B − in | — | `N_B_MINUS` | — | OPA1678-B pin |
| U1B out | — | `N_B_OUT` | — | OPA1678-B pin |
| Rf_B | 100 kΩ | `N_B_OUT` | `N_B_MINUS` | feedback; gain = −Rf_B/R_in ≈ −3.03× |
| C_fbB | 100 pF | `N_B_OUT` | `N_B_MINUS` | high-cut / stability |
| D_hard1 | 1N4148 **DNP** | `N_B_OUT` | `VGND` | optional hard clip (anti-parallel) |
| D_hard2 | 1N4148 **DNP** | `VGND` | `N_B_OUT` | fixed-level node, before volume |
| RV_VOL | 10 kΩ audio | top `N_B_OUT` / btm `VGND` | wiper `N_VOL_W` | master volume (no DC across it: both ends at 3 V) |

---

## Output stage — OPA1622 driver  (config TBD)

Wiper sits at 3 V DC, so it self-biases the OPA1622 + input at mid-rail. Gain-vs-buffer config, GND-pin reference, and EN scheme are the **next open items**.

```
N_VOL_W ─▶ (+) OPA1622 ─▶ N_HP_OUT ─[C_out 220–470µ]─▶ HP TIP
              feedback TBD                              HP SLEEVE ─ GND0
```

**Connections**

| Ref | Value | Net A | Net B | Notes |
|---|---|---|---|---|
| U2 + in | — | `N_VOL_W` | — | biased at 3 V by volume wiper |
| U2 − in / fb | **TBD** | `N_HP_OUT` | `N_VOL_W`/`VGND` | buffer vs gain — **open** |
| U2 out | — | `N_HP_OUT` | — | |
| U2 GND pin | **TBD** | GND pin | `VGND` or `GND0` | **open** — sets EN ref & PSRR |
| U2 EN | via divider (**TBD**) | EN | — | anti-thump (datasheet Fig 48) + soft on/off |
| U2 thermal pad | — | pad | `GND0` | pad → most-negative rail |
| C_out | 220–470 µF | `N_HP_OUT` | HP `TIP` | AC-couple; return via `GND0` |
| J_HP sleeve | — | HP `SLEEVE` | `GND0` | |

---

## Still-open (matches the block diagram's amber `?`)

- **Power on/off** method: TRS-ring vs toggle vs OPA1622 EN soft-power
- **Charger** exact part + `R_ISET` charge current; **boost** part + Fsw + `L`
- **OPA1622**: GND-pin reference, EN/thump divider, and buffer-vs-gain config
- **Reverse-polarity**: likely delete · **low-battery indicator**: TBD
- Bench-tune: `RV_DRIVE` taper, `Cg`, diode recipe

## Format notes (for future me)

- This netlist is the master. For a *drawn* schematic of a stage, use **KiCad** (export SVG) or **SchemDraw** (Python→SVG) and embed the image next to the relevant table.
- To draw inside Obsidian instead: **Excalidraw** plugin (sketchy, flexible) or **diagrams.net/draw.io** plugin (has EE symbol libraries).
