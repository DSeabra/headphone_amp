# InvenTree import — new parts for headphone amp Rev A

Generated 2026-10-11 from the KiCad BOM export + netlist (`headphone_amp.net`) and the InvenTree 1.5.0 exports.
30 new parts · 56 manufacturer parts · 55 JLCPCB supplier parts.

---

## 1. Before importing — create these in InvenTree

The importer matches **Category** and **Company** by exact name, so these must exist first (spelling and case must match, or edit the CSV to match yours).

### Categories (new)
| Category name | Used by | Suggested parent |
|---|---|---|
| `MOSFETs` | 303-0001 BSS138 | Transistors |
| `Inductors` | 305-0001 L1 | Inductors / Magnetics |
| `Logic` | 307-0006/7/8 (4060, 74HC14, 74HC02) | ICs |
| `Switching Diodes` | 308-0002 1N4148W | Diodes |
| `LEDs` | 308-0003 IN-S42ATA | Diodes / Optoelectronics |
| `Audio Connectors` | 310-0007/8 (3.5 mm jacks) | Connectors |

Existing categories reused: `Ceramic Capacitors`, `Polymer Capacitors`, `Surface Mount Resistors`, `Ferrite Beads`, `Analog`, `Power`, `Signal Connectors`.
- [ ] If any of these names appears **twice** in your tree (e.g. a `Power` under both ICs and Connectors), the lookup is ambiguous and those rows will error — either rename, or replace the value in `1_parts.csv` with the full path (e.g. `ICs/Power`).
- I put the TLE2426 (rail splitter) and TLV7A0325 (LDO) under `Power`. Move them if you'd rather have a Voltage References category.

### Companies (check which already exist)
Already seen in your exports (names used exactly as exported): `Yageo`, `Vishay`, `Panasonic`, `Murata Electronics`, `Samsung Electro-Mechanics`, `Texas Instruments`, `JLCPCB`.

Probably new — create as **Manufacturer**:
- [ ] `Kyocera AVX` — if your film cap (301-0001) already uses a company like "AVX" or "KYOCERA AVX", edit `2_manufacturer_parts.csv` to match instead of creating a duplicate
- [ ] `TDK`
- [ ] `Diodes Incorporated`
- [ ] `Nexperia`
- [ ] `onsemi`
- [ ] `Same Sky` (formerly CUI Devices — LCSC still lists it as CUI)
- [ ] `JST`
- [ ] `Inolux`
- [ ] `Walsin`
- [ ] `FOJAN`
- [ ] `Fenghua` (LCSC brand "FH" — Guangdong Fenghua Advanced Tech)

---

## 2. Import order

| Step | File | Session type | Notes |
|---|---|---|---|
| 1 | `1_parts.csv` | Part, create | Columns auto-map by field name. Category matched by name. |
| 2 | `2_manufacturer_parts.csv` | Manufacturer Part, create | `part` matched by IPN, `manufacturer` by company name. |
| 3 | `3_supplier_parts.csv` | Supplier Part, create | `manufacturer_part` matched by MPN; `primary` marks the preferred source. |
| 4 | `4_existing_parts_update.csv` | Part, **update** (Admin Center → "Update Existing Records") | Map `ID`. Fixes keyword/description typos on 6 existing parts. Every row has both fields, so nothing gets blanked. |
| 5 | Parameters | — | Send me a fresh Part export after step 1 and I'll fill in the Model IDs in `parameters_DRAFT_needs_part_ids.csv` (template 1 = Value, 3 = Footprint, 4 = Symbol). |

- [ ] **Caution:** if a category has parameter templates attached, InvenTree may copy them onto new parts at creation (`copy_category_parameters`). That's harmless, but it means step 5 should *update* those parameters rather than create duplicates. Tell me if you see that happen.

---

## 3. KiCad updates (link IPNs)

| Refs | IPN | Notes |
|---|---|---|
| C9, C13, C29 | 301-0007 | |
| **C1, C17** | **301-0018** | Moved off 301-0003 (16 V) to a 25 V part; they sit on V+F / V+ (9 V). C8, C24, C25 and C26 stay on 301-0003 |
| C10 | 301-0008 | |
| C11 | 301-0009 | |
| **C12** | 301-0010 | **Footprint → `Capacitor_SMD:C_0805_2012Metric`** (1.5 µF 25 V X7R 0805) |
| C14, C22, C30, C31 | 301-0012 | |
| C15, C20 | 301-0013 | |
| C16, C27, C28, C32 | 301-0014 | |
| C21 | 301-0015 | |
| C23 | 301-0016 | |
| C33 | 301-0017 | Value field will become `10uF` (was the MPN) |
| **R20** | 302-0017 | **Change value 18K → 18.2K** |
| R21 | 302-0018 | |
| R36 | 302-0019 | |
| **R37** | **302-0008** | Existing 100K part — no new part |
| R42 | 302-0020 | |
| R19, R24–R28, R49–R52 | 302-0021 | R50/R51 stay DNP |
| Q1 | 303-0001 | |
| L1 | 305-0001 | Murata DFE252012P-3R3M=P2 (approved swap from Abracon); check land pattern vs `L_1008_2520Metric` |
| FB3 | 306-0003 | |
| U3 | 307-0004 | |
| U4 | 307-0005 | |
| U6 | 307-0006 | |
| U7 | 307-0007 | Symbol is currently `:74HC14_1` (an embedded symbol with no library). The parameter draft points it at `74xx:74HC14` |
| U8 | 307-0008 | TI SN74HC02PWR (as ordered) |
| U9 | 307-0009 | Symbol is now `integrated_circuits:PWR_LDO_2V5_TLV7A0325PDBVR`, which fixes the old TPS7A0508 mismatch ✔ |
| D2, D3, D4 | 308-0002 | D2/D3 stay DNP |
| D5, D6 | 308-0003 | |
| J8 | 310-0007 | |
| J10 | 310-0008 | |
| SW1 | 310-0009 | Part is the on-board JST SH 2-pin header (LCSC C160388), not the panel switch |

- [ ] **D7 IPN (your call):** D7 (CD0603-B0340R Schottky) is `306-0002`, but under your scheme diodes are 308. Renumbering means changing the IPN in InvenTree **and** on D7 in KiCad. The next free number would be `308-0004`. I left it out of the update file so you can decide.

---

## 4. Decisions / issues for you

### L1 saturation current — RESOLVED: switched to Murata DFE252012P-3R3M=P2 (approved 2026-10-11)
`ASMPH-1008-3R3M-T` has **Isat = 450 mA** (Irms 1.2 A, DCR 100 mΩ), per Abracon's spec page. Peak inductor current, from the TPS61379 datasheet equations (I_pk = I_in + ΔI/2, f_sw 2.177 MHz, η 0.9):

| Condition | Vin 3.0 V | Vin 4.2 V |
|---|---|---|
| Idle (9.4 mA load) | 177 mA | 192 mA |
| Cranked average (32 mA) | 253 mA | 246 mA |
| Full-scale peak (both channels, 2.1 V RMS into 32 Ω, at crest) | **796 mA** | **634 mA** |
| Switch current limit (startup, overload, or fault) | 1.58 A min · 2.25 A max | |

Normal playing has about 1.8× margin. Loud transients near clipping, and anything that hits the switch current limit, will saturate it. The TPS61379-Q1 datasheet (§9.2.2.3) says Isat must exceed the peak current during operation.
**Drop-in alternative:** Murata `DFE252012P-3R3M=P2`: 3.3 µH, same 1008 (2520) size, **Isat 2.3 A** (above even the max current limit), Irms 1.7 A, DCR 140 mΩ. These numbers come from LCSC's listing, so confirm them on Murata's datasheet. It's **at LCSC (C161085, ~3k in stock)**, so JLC can place it; the Abracon part isn't stocked there. Check its land pattern against your `L_1008_2520Metric` footprint before swapping.

### C12 — RESOLVED (2026-10-11)
Moved to **0805**: 1.5 µF ±10% 25 V X7R (301-0010). Your pick, TDK C2012X7R1E155K125AC, isn't at LCSC. The same TDK spec under series code C2012X7R1E155KT000N (**C338028**, ~2k in stock) is, so that's the JLCPCB supplier record. Both MPNs are recorded as manufacturer parts.
- ~~C23~~ **Resolved:** the part you ordered, Murata GCM155C71A684KE38D (X7S, 10 V, C710661), meets the rule.

### Fewer than 3 alternates (no more qualifying parts at LCSC)
- 301-0007 (1 µF 0402 25 V): only two Murata X6S parts. 25 V X7R/X7S/X6S 1 µF parts in 0402 are rare.
- 301-0012 (4.7 µF 0603 25 V): only Murata X6S (±10% and ±20% versions).
- 301-0014 (2.2 µF 0603 25 V): Fenghua X7R (primary) + Murata X7S.
- 301-0017 (TCJA polymer tantalum): single source, like the film cap.
- 301-0008 (10 nF): switched to the **C0G** part you ordered (Murata GRM1555C1H103JE01D). It's better than X7R for a compensation cap, but only one source is listed.
- 301-0016 (0.68 µF X7S): single source (the part you ordered).

### LCSC stock problems (as of 2026-10-11)
- **18.2K (302-0017): all three sources are out of stock** (Yageo, Vishay, Walsin). You need either a different in-stock part at order time, or your Digi-Key stock consigned.
- Out of stock, but an in-stock alternate exists and is marked primary: GRM155C81E105KE11D (1 µF 0402), CL10B105KA8NNNC (1 µF 0603), Yageo/Walsin 46.4K (Panasonic is primary).
- Low stock: TLE2426QDRG4Q1 (21 pcs), MJ-3523-SMT-TR (42 pcs).

### Correction: global-sourcing C-numbers added
Earlier I said five parts weren't at LCSC. That was wrong: they're listed (some out of stock), and your JLC BOM has their C-numbers. They now have JLCPCB supplier records: TLV7A0325PDBVR C49261910 (210 in stock), IN-S42ATA C5771919, MDF2016BSS600CTD25 C3716673, TCJA106M016R0200 C194304.
Also aligned with your order: Q1 primary is Diodes Inc **BSS138-7-F** (C40912), with onsemi BSS138 as alternate. U8 primary is TI **SN74HC02PWR** (C484750), with Nexperia as alternate. The ordered 0R (C2073756) and 220 nF (C126524) parts are listed as alternates.

### Smaller checks
- [ ] **FB3** is a TDK part on a Würth `PMFI-201610` footprint. Both are 2.0 × 1.6 mm, but compare the pads with TDK's recommended land pattern for MDF2016.
- [ ] **FB3 impedance** "60 Ω @ 2 MHz" is inferred from TDK's MDF part numbering (the 270 version is 27 Ω @ 2 MHz). The 850 mA rating and 330 mΩ DCR come from element14. Worth checking against TDK's datasheet.
- [ ] Your 2.2 µF primary is X7R (Fenghua); the Murata alternate is X7S (±22% tempco vs ±15%). Both are in your allowed set.

---

## 5. Voltage rating check (2× margin, from netlist rails)
| IPN | Refs → nets | Max V | Rating |
|---|---|---|---|
| 301-0007 | C9 Boost VCC · C13 V+ (9 V) · C29 VBUS | 9 V | 25 V ✔ |
| 301-0008 | C10 Boost COMP | < 3 V | 50 V C0G ✔ |
| 301-0009 | C11 Boost Vin (= VSYS ≤ 5.5 V) | 5.5 V | 16 V ✔ |
| 301-0010 | C12 Boost OUT (9 V) | 9 V | 25 V X7R 0805 ✔ |
| 301-0012 | C14 V+ · C22 POR_IN · C30 VBAT · C31 charger OUT | 9 V | 25 V ✔ |
| 301-0013 | C15 TLE2426 NR · C20 audio coupling (4.5 V DC) | ~9 V | 25 V ✔ |
| 301-0014 | C16 VMID · C27 VSYS · C28 V_LOGIC · C32 OPA1622 EN | ~9 V | 25 V ✔ |
| 301-0015 | C21 ENV_HOLD | 2.5 V | 16 V ✔ |
| 301-0016 | C23 timing | 2.5 V | 10 V X7S ✔ |
| 301-0017 | C33 VBUS | 5 V (TVS clamps at 12 V) | 16 V ✔ |
| 301-0018 | C1 V+F · C17 V+ | 9 V | 25 V ✔ |

Each KiCad BOM group gets one part, rated for the highest-voltage net in the group.
