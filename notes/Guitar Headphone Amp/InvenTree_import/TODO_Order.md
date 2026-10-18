# TODO — JLC order: new parts (headphone amp Rev A)

Everything else on the BOM is already ordered; this is only what's left. Stock is as of 2026-10-11 from LCSC product pages. Quantities are **per board**; multiply by your build quantity and add JLC's attrition extras.
`headphone_amp_jlc_bom_revised.csv` is your original JLC BOM with exactly these changes applied (same 112 references).

| #   | Refs               | Qty/board | JLCPCB C#    | MPN                       | Spec                                | Footprint                                             | LCSC stock                |
| --- | ------------------ | --------- | ------------ | ------------------------- | ----------------------------------- | ----------------------------------------------------- | ------------------------- |
| 1   | C9, C13, C29       | 3         | **C703147**  | Murata GRT155C81E105KE13D | 1 µF ±10% 25 V X6S                  | 0402 ✔                                                | 28,920                    |
| 2   | C15, C20           | 2         | **C86020**   | Murata GRM188R71E105KA12D | 1 µF ±10% 25 V X7R                  | 0603 ✔                                                | 127,210                   |
| 3   | C16, C27, C28, C32 | 4         | **C99228**   | Fenghua 0603B225K250NT    | 2.2 µF ±10% 25 V X7R                | 0603 ✔                                                | 515,600                   |
| 4   | C14, C22, C30, C31 | 4         | **C417145**  | Murata GRM188C81E475KE11D | 4.7 µF ±10% 25 V X6S                | 0603 ✔                                                | 75,760                    |
| 5   | C11                | 1         | **C95841**   | Samsung CL21B106KOQNNNE   | 10 µF ±10% 16 V X7R                 | 0805 ✔                                                | 266,260                   |
| 6   | C1, C17            | 2         | **C2168305** | Murata GRM155R71E104KE14J | 100 nF ±10% 25 V X7R                | 0402 ✔                                                | 12,250                    |
| 7   | **C12**            | 1         | **C338028**  | TDK C2012X7R1E155KT000N   | 1.5 µF ±10% 25 V X7R                | **0805: change the footprint to `C_0805_2012Metric`** | 2,045                     |
| 8   | L1                 | 1         | **C161085**  | Murata DFE252012P-3R3M=P2 | 3.3 µH ±20%, Isat 2.3 A, Irms 1.7 A | 1008 / 2520 ✔ (see note)                              | 3,035                     |
| 9   | R20                | 1         | **C274351**  | Yageo RC0402FR-0718K2L    | 18.2 kΩ ±1%                         | 0402 ✔                                                | **0, so global sourcing** |
| 10  | SW1                | 1         | **C160388**  | JST BM02B-SRSS-TB(LF)(SN) | SH 2-pin vertical                   | matches footprint ✔                                   | 29,200                    |

**Total: 10 line items, 20 placements per board.**

## In-stock alternates (checked on LCSC; same package and rating)
- #2: C106858 (Yageo CC0603KRX7R8BB105)
- #3: C162267 (Murata GRM188C71E225KE11D, X7S)
- #5: C326595 (Yageo CC0805KKX7R7BB106), C162430 (Murata GRM21BZ71C106KE15L)
- #6: C155422 (Samsung CL05B104KA5NNNC), C105883 (Yageo CC0402KRX7R8BB104)
- #7: TDK C2012X7R1E155K125AC is your original pick; it's the same spec, but not at LCSC (global sourcing only)
- #1: no second 25 V source is in stock (C182246, GRM155C81E105KE11D, is out of stock)

## Already purchased, now unused (keep as spares / log in InvenTree)
| C# | Part | Was for |
|---|---|---|
| C528974 | GRM155Z71A105KE01D 1 µF 10 V 0402 | C9, C13, C15, C20, C29 |
| C338105 | CGA3E3X7S1A225KT000N 2.2 µF 10 V | C16, C27, C28, C32 |
| C342955 | C1608X6S1C475KT000E 4.7 µF 16 V | C14, C22, C30, C31 |
| C1952580 | CC0805KKX7R6BB106 10 µF 10 V | C11 |
| C361193 | C1608X7R1A155KT000E 1.5 µF 10 V 0603 | C12 |
| C5589769 | ASMPH-1008-3R3M-T | L1 |
| C138044 | RC0402FR-0718KL 18 kΩ | R20 |
| C160389 | BM03B-SRSS-TB (1 extra per board) | SW1 |
| C106994 | GRM155R71C104KA88J 100 nF 16 V (2 extra per board) | C1, C17 |

## Before ordering
- [x] **C12 footprint → 0805** in KiCad (you're doing this now). Re-run DRC; it's on the boost output, so keep it tight to the IC's VOUT pin.
- [ ] **L1 land pattern:** Murata confirms the 2.5 × 2.0 mm body and Isat 2.3 A. KiCad's `L_1008_2520Metric` pads (1.25 × 2.2 mm, 2.15 mm pitch) suit that body. Murata's recommended land drawing is an image I couldn't read, so lay it over the footprint.
- [ ] **KiCad:** set C1 and C17 to IPN 301-0018 (splits them from the 0.1 µF group) and change R20's value to 18.2K. The full IPN mapping is in `TODO.md` §3.
