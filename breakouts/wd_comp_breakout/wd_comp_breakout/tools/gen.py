#!/usr/bin/env python3
"""Generate the TLV7011 watchdog-comparator breakout KiCad project (KiCad 7 file format,
opens in KiCad 7/8/9/10). Board 25.4 x 25.4 mm, 2 layers."""
import json, os, uuid, math, re

PROJ = "wd_comp_breakout"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "out", PROJ)
os.makedirs(OUT, exist_ok=True)

_uu = uuid.UUID("6f1c2a1e-0000-4000-8000-000000000000").int
def U():
    global _uu
    _uu += 1
    return str(uuid.UUID(int=_uu))

def f(v):
    s = f"{v:.4f}".rstrip("0").rstrip(".")
    return "0" if s in ("-0", "") else s

ROOT = U()
DATE = "2026-11-21"

# ----------------------------------------------------------------------------- nets
NETS = ["", "GND", "V_LOGIC", "AUDIO_DETECT", "ENV_THRESHOLD", "VREF", "RB_MID"]
NID = {n: i for i, n in enumerate(NETS)}

# ----------------------------------------------------------------------------- parts
# ref: (lib_id_sch, footprint, value, dnp, {pin: net}, description)
PARTS = {
    "U1": ("wd_comp_breakout:TLV7011DBV", "Package_TO_SOT_SMD:SOT-23-5", "TLV7011", False,
           {"1": "AUDIO_DETECT", "2": "GND", "3": "ENV_THRESHOLD", "4": "VREF", "5": "V_LOGIC"},
           "Comparator, push-pull. TLV7021 (open-drain) also fits: then fit R4."),
    "R1": ("Device:R", "Resistor_SMD:R_0603_1608Metric", "220k", False, {"1": "V_LOGIC", "2": "VREF"}, "Rt"),
    "R2": ("Device:R", "Resistor_SMD:R_0603_1608Metric", "30k", False, {"1": "VREF", "2": "RB_MID"}, "Rb"),
    "R3": ("Device:R", "Resistor_SMD:R_0603_1608Metric", "4.7M", False, {"1": "ENV_THRESHOLD", "2": "AUDIO_DETECT"}, "Rh"),
    "R4": ("Device:R", "Resistor_SMD:R_0603_1608Metric", "100k", True, {"1": "V_LOGIC", "2": "AUDIO_DETECT"}, "Pull-up, TLV7021 only"),
    "R5": ("Device:R", "Resistor_SMD:R_0603_1608Metric", "0R", False, {"1": "RB_MID", "2": "GND"}, "Second Rb element: Rb = R2 + R5 (0R for Set A)"),
    "C1": ("Device:C", "Capacitor_SMD:C_0603_1608Metric", "100n", False, {"1": "V_LOGIC", "2": "GND"}, "VCC decoupling"),
    "C2": ("Device:C", "Capacitor_SMD:C_0603_1608Metric", "10n", False, {"1": "VREF", "2": "GND"}, "Cref"),
    "C3": ("Device:C", "Capacitor_SMD:C_0603_1608Metric", "1n", True, {"1": "ENV_THRESHOLD", "2": "GND"}, "Optional IN+ filter"),
    "J1": ("Connector_Generic:Conn_01x06", "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal", "SM06B-SRSS-TB", False,
           {"1": "GND", "2": "AUDIO_DETECT", "3": "ENV_THRESHOLD", "4": "V_LOGIC", "5": "VREF", "6": "GND"},
           "JST SH 6-pin right-angle SMD header, 1.0 mm pitch"),
}
HOLE_POS = {"H1": (3.0, 3.0), "H2": (22.4, 3.0), "H3": (3.0, 22.4), "H4": (22.4, 22.4)}
HOLE_KEEPOUT = 3.0     # mm radius kept clear of copper and silk (screw head / washer / standoff)
for _h in HOLE_POS:
    PARTS[_h] = ("Mechanical:MountingHole", "MountingHole:MountingHole_2.7mm_M2.5", "MountingHole_M2.5", False, {}, "M2.5 unplated mounting hole")
SYM_UUID = {r: U() for r in PARTS}

# ============================================================================ FOOTPRINTS
def rot(x, y, deg):
    t = math.radians(deg)
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))

def fp_line(x1, y1, x2, y2, layer, w):
    return f'    (fp_line (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(w)}) (type solid)) (layer "{layer}") (tstamp {U()}))\n'

def fp_rect(x1, y1, x2, y2, layer, w):
    return f'    (fp_rect (start {f(x1)} {f(y1)}) (end {f(x2)} {f(y2)}) (stroke (width {f(w)}) (type solid)) (fill none) (layer "{layer}") (tstamp {U()}))\n'

def fp_poly(pts, layer, w, fill=True):
    p = " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts)
    return f'    (fp_poly (pts {p}) (stroke (width {f(w)}) (type solid)) (fill {"solid" if fill else "none"}) (layer "{layer}") (tstamp {U()}))\n'

# local footprint definitions: pads [(num, type, shape, x, y, w, h, drill, extra)], graphics fn
def chip_pads(pitch_half, w, h):
    return [("1", "smd", "roundrect", -pitch_half, 0, w, h, None), ("2", "smd", "roundrect", pitch_half, 0, w, h, None)]

FOOTPRINTS = {
    "Resistor_SMD:R_0603_1608Metric": dict(
        pads=chip_pads(0.825, 0.8, 0.95), attr="smd", ref_at=(0, -1.43), val_at=(0, 1.43),
        gfx=lambda: fp_line(-0.237258, -0.5225, 0.237258, -0.5225, "F.SilkS", 0.12) + fp_line(-0.237258, 0.5225, 0.237258, 0.5225, "F.SilkS", 0.12)
        + fp_rect(-1.48, -0.73, 1.48, 0.73, "F.CrtYd", 0.05) + fp_rect(-0.8, -0.4125, 0.8, 0.4125, "F.Fab", 0.1)),
    "Capacitor_SMD:C_0603_1608Metric": dict(
        pads=chip_pads(0.775, 0.9, 0.95), attr="smd", ref_at=(0, -1.43), val_at=(0, 1.43),
        gfx=lambda: fp_line(-0.14058, -0.51, 0.14058, -0.51, "F.SilkS", 0.12) + fp_line(-0.14058, 0.51, 0.14058, 0.51, "F.SilkS", 0.12)
        + fp_rect(-1.48, -0.73, 1.48, 0.73, "F.CrtYd", 0.05) + fp_rect(-0.8, -0.4, 0.8, 0.4, "F.Fab", 0.1)),
    "Package_TO_SOT_SMD:SOT-23-5": dict(
        pads=[("1", "smd", "roundrect", -1.1375, -0.95, 1.325, 0.6, None), ("2", "smd", "roundrect", -1.1375, 0, 1.325, 0.6, None),
              ("3", "smd", "roundrect", -1.1375, 0.95, 1.325, 0.6, None), ("4", "smd", "roundrect", 1.1375, 0.95, 1.325, 0.6, None),
              ("5", "smd", "roundrect", 1.1375, -0.95, 1.325, 0.6, None)],
        attr="smd", ref_at=(0, -2.4), val_at=(0, 2.4),
        gfx=lambda: fp_line(0, -1.56, -0.8, -1.56, "F.SilkS", 0.12) + fp_line(0, -1.56, 0.8, -1.56, "F.SilkS", 0.12)
        + fp_line(0, 1.56, -0.8, 1.56, "F.SilkS", 0.12) + fp_line(0, 1.56, 0.8, 1.56, "F.SilkS", 0.12)
        + fp_poly([(-1.3, -1.51), (-1.54, -1.84), (-1.06, -1.84), (-1.3, -1.51)], "F.SilkS", 0.12)
        + fp_rect(-2.05, -1.7, 2.05, 1.7, "F.CrtYd", 0.05)
        + fp_poly([(-0.4, -1.45), (0.8, -1.45), (0.8, 1.45), (-0.8, 1.45), (-0.8, -1.05)], "F.Fab", 0.1, fill=False)),
    "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical": dict(
        pads=[(str(i + 1), "thru_hole", "rect" if i == 0 else "oval", 0, i * 2.54, 1.7, 1.7, 1.0) for i in range(6)],
        attr="through_hole", ref_at=(0, -2.33), val_at=(0, 15.03),
        gfx=lambda: fp_line(-1.33, 1.27, -1.33, 14.03, "F.SilkS", 0.12) + fp_line(1.33, 1.27, 1.33, 14.03, "F.SilkS", 0.12)
        + fp_line(-1.33, 14.03, 1.33, 14.03, "F.SilkS", 0.12) + fp_line(-1.33, 1.27, 1.33, 1.27, "F.SilkS", 0.12)
        + fp_line(-1.33, 0, -1.33, -1.33, "F.SilkS", 0.12) + fp_line(-1.33, -1.33, 0, -1.33, "F.SilkS", 0.12)
        + fp_rect(-1.8, -1.8, 1.8, 14.5, "F.CrtYd", 0.05) + fp_rect(-1.27, -1.27, 1.27, 13.97, "F.Fab", 0.1)),
    "Connector_JST:JST_SH_SM06B-SRSS-TB_1x06-1MP_P1.00mm_Horizontal": dict(
        pads=[(str(i + 1), "smd", "roundrect", -2.5 + i, -2.0, 0.6, 1.55, None) for i in range(6)]
             + [("MP", "smd", "roundrect", -3.8, 1.875, 1.2, 1.8, None), ("MP", "smd", "roundrect", 3.8, 1.875, 1.2, 1.8, None)],
        attr="smd", ref_at=(0, -3.9), val_at=(0, 3.9),
        gfx=lambda: fp_line(-4.51, -1.785, -3.06, -1.785, "F.SilkS", 0.12) + fp_line(3.06, -1.785, 4.51, -1.785, "F.SilkS", 0.12)
        + fp_line(-4.51, -1.785, -4.51, 0.715, "F.SilkS", 0.12) + fp_line(4.51, -1.785, 4.51, 0.715, "F.SilkS", 0.12)
        + fp_line(-2.94, 2.735, 2.94, 2.735, "F.SilkS", 0.12)
        + fp_poly([(-2.5, -2.98), (-2.8, -3.38), (-2.2, -3.38)], "F.SilkS", 0.12)
        + fp_rect(-4.9, -3.28, 4.9, 3.28, "F.CrtYd", 0.05) + fp_rect(-4.0, -1.675, 4.0, 2.525, "F.Fab", 0.1)),
    f"{PROJ}:WirePads_1x06_P2.54mm_SMD": dict(
        pads=[(str(i + 1), "smd", "rect", i * 2.54, 0, 1.6, 3.0, None) for i in range(6)],
        attr="smd exclude_from_bom", ref_at=(-2.4, 0), val_at=(6.35, 2.3),
        gfx=lambda: fp_poly([(-1.25, -1.0), (-1.25, -1.9), (-0.95, -1.45)], "F.SilkS", 0.12)
        + fp_rect(-1.3, -1.75, 14.0, 1.75, "F.CrtYd", 0.05) + fp_rect(-0.8, -1.5, 13.5, 1.5, "F.Fab", 0.1)),
    f"{PROJ}:Trimmer_3pin_P2.54mm_Inline": dict(
        pads=[(str(i + 1), "thru_hole", "rect" if i == 0 else "circle", i * 2.54, 0, 1.7, 1.7, 1.0) for i in range(3)],
        attr="through_hole", ref_at=(2.54, -2.2), val_at=(2.54, 2.2),
        gfx=lambda: fp_rect(-1.8, -1.8, 6.88, 1.8, "F.CrtYd", 0.05) + fp_rect(-1.3, -1.3, 6.38, 1.3, "F.Fab", 0.1)
        + fp_line(-1.27, -1.35, 6.35, -1.35, "F.SilkS", 0.12) + fp_line(-1.27, 1.35, 6.35, 1.35, "F.SilkS", 0.12)),
}

PAD_LAYERS = {"smd": '"F.Cu" "F.Paste" "F.Mask"', "thru_hole": '"*.Cu" "*.Mask"', "np_thru_hole": '"*.Cu" "*.Mask"'}
def fp_circle(r, layer, w):
    return f'    (fp_circle (center 0 0) (end {f(r)} 0) (stroke (width {f(w)}) (type solid)) (fill none) (layer "{layer}") (tstamp {U()}))\n'
FOOTPRINTS["MountingHole:MountingHole_2.7mm_M2.5"] = dict(
    pads=[("", "np_thru_hole", "circle", 0, 0, 2.7, 2.7, 2.7)],
    attr="exclude_from_pos_files exclude_from_bom", ref_at=(0, -3.7), val_at=(0, 3.7),
    gfx=lambda: fp_circle(2.7, "Cmts.User", 0.15) + fp_circle(2.95, "F.CrtYd", 0.05))

SILK_H, SILK_T = 0.8, 0.13          # OSH Park: min silk line 5 mil (0.127 mm)
def footprint_body(fpid, ref, value, at, angle, nets, pcb=True, ref_off=None, ref_size=SILK_H, val_off=None, dnp_off=None):
    d = FOOTPRINTS[fpid]
    s = f'  (footprint "{fpid}" (layer "F.Cu")\n'
    s += f"    (tstamp {U()})\n"
    if pcb:
        s += f"    (at {f(at[0])} {f(at[1])}{(' ' + f(angle)) if angle else ''})\n"
        s += f'    (property "Sheetfile" "{PROJ}.kicad_sch")\n    (property "Sheetname" "")\n'
        s += f'    (path "/{SYM_UUID[ref]}")\n'
    s += f"    (attr {d['attr']})\n"
    if ref_off is not None:
        ro = rot(ref_off[0], ref_off[1], -angle)   # absolute board offset -> footprint-local
    else:
        ro = d["ref_at"]
    th = SILK_T if ref_size == SILK_H else round(ref_size * 0.16, 3)
    rlayer = "F.Fab" if ref.startswith("H") else "F.SilkS"
    s += (f'    (fp_text reference "{ref}" (at {f(ro[0])} {f(ro[1])}{"" if (ref_off is not None or not angle) else " " + f(angle)}) (layer "{rlayer}")'
          f' (effects (font (size {f(ref_size)} {f(ref_size)}) (thickness {f(th)}))) (tstamp {U()}))\n')
    if val_off is not None:
        va = rot(val_off[0], val_off[1], -angle)
        s += (f'    (fp_text value "{value}" (at {f(va[0])} {f(va[1])}) (layer "F.SilkS")'
              f' (effects (font (size {f(SILK_H)} {f(SILK_H)}) (thickness {f(SILK_T)}))) (tstamp {U()}))\n')
    else:
        va = d["val_at"]
        s += (f'    (fp_text value "{value}" (at {f(va[0])} {f(va[1])}{(" " + f(angle)) if angle else ""}) (layer "F.Fab")'
              f' (effects (font (size 0.6 0.6) (thickness 0.09))) (tstamp {U()}))\n')
    if dnp_off is not None:
        da = rot(dnp_off[0], dnp_off[1], -angle)
        s += (f'    (fp_text user "DNP" (at {f(da[0])} {f(da[1])}) (layer "F.SilkS")'
              f' (effects (font (size {f(SILK_H)} {f(SILK_H)}) (thickness {f(SILK_T)}))) (tstamp {U()}))\n')
    s += (f'    (fp_text user "${{REFERENCE}}" (at 0 0{(" " + f(angle)) if angle else ""}) (layer "F.Fab")'
          f' (effects (font (size 0.4 0.4) (thickness 0.06))) (tstamp {U()}))\n')
    s += d["gfx"]()
    for (num, typ, shape, x, y, w, h, drill) in d["pads"]:
        net = nets.get(num) if nets else None
        a = f" {f(angle)}" if angle else ""
        s += f'    (pad "{num}" {typ} {shape} (at {f(x)} {f(y)}{a}) (size {f(w)} {f(h)})'
        if drill:
            s += f" (drill {f(drill)})"
        s += f" (layers {PAD_LAYERS[typ]})"
        if shape == "roundrect":
            s += " (roundrect_rratio 0.25)"
        if net:
            s += f' (net {NID[net]} "{net}")'
        s += (f' (pintype "passive")' if typ != "np_thru_hole" else "") + f' (tstamp {U()}))\n'
    s += "  )\n"
    return s

# ============================================================================ PCB
BX, BY = 100.0, 100.0          # board origin (top-left)
BW = 25.4
def A(x, y): return (BX + x, BY + y)

PLACE = {  # ref: (x, y, angle, ref_off, val_off, dnp_off)  offsets are absolute board offsets from the part centre
    "U1": (12.0, 11.0, 0, (-2.7, 2.45), (1.0, 2.45), None),
    "R4": (12.0, 7.6, 180, (-2.8, -1.4), (-0.4, -1.4), (2.5, -1.4)),
    "C1": (15.2, 9.6, 270, (-0.9, -1.95), (1.4, -1.95), None),
    "R1": (18.0, 9.6, 270, (1.4, -0.6), (2.3, 0.5), None),
    "C2": (20.6, 11.95, 0, (-0.9, 1.25), (1.3, 1.25), None),
    "R2": (18.0, 14.0, 270, (1.6, 0.6), (3.9, 0.6), None),
    "R5": (18.0, 17.0, 270, (1.6, 0.0), (3.4, 0.0), None),
    "R3": (7.5, 11.0, 90, (-4.7, -1.0), (-4.7, 0.0), None),
    "C3": (9.4, 14.5, 0, (-1.6, 1.25), (0.2, 1.25), (2.2, 1.25)),
    "J1": (12.7, 22.1, 0, (6.3, -2.2), None, None),
    **{h: (x, y, 0, None, None, None) for h, (x, y) in HOLE_POS.items()},
}

W_SIG, W_PWR = 0.25, 0.4
TRACKS = []   # (layer, net, width, [points rel])
def T(layer, net, w, *pts): TRACKS.append((layer, net, w, pts))
F, B = "F.Cu", "B.Cu"
# AUDIO_DETECT
T(F, "AUDIO_DETECT", W_SIG, (10.8625, 10.05), (7.5, 10.175))
T(F, "AUDIO_DETECT", W_SIG, (7.5, 10.175), (5.6, 10.175), (5.0, 10.775), (5.0, 16.6), (5.6, 17.2), (10.6, 17.2), (11.2, 17.8), (11.2, 20.1))
T(F, "AUDIO_DETECT", W_SIG, (10.8625, 10.05), (10.8625, 8.2), (11.175, 7.6))
# ENV_THRESHOLD
T(F, "ENV_THRESHOLD", W_SIG, (10.8625, 11.95), (7.5, 11.825))
T(F, "ENV_THRESHOLD", W_SIG, (7.5, 11.825), (7.5, 14.5))
T(F, "ENV_THRESHOLD", W_SIG, (7.5, 14.5), (8.625, 14.5))
T(F, "ENV_THRESHOLD", W_SIG, (7.5, 14.5), (7.5, 15.6), (8.1, 16.2), (11.6, 16.2), (12.2, 16.8), (12.2, 20.1))
# V_LOGIC
T(F, "V_LOGIC", W_PWR, (13.1375, 10.05), (13.1375, 8.825))
T(F, "V_LOGIC", W_PWR, (13.1375, 8.825), (13.1375, 8.2), (12.825, 7.6))
T(F, "V_LOGIC", W_PWR, (13.1375, 8.825), (14.2, 8.825))
T(F, "V_LOGIC", W_PWR, (14.2, 8.825), (15.2, 8.825))
T(F, "V_LOGIC", W_PWR, (15.2, 8.825), (18.0, 8.775))
T(B, "V_LOGIC", W_PWR, (14.2, 8.825), (14.2, 17.0), (13.2, 18.0))
T(F, "V_LOGIC", W_PWR, (13.2, 18.0), (13.2, 20.1))
# VREF
T(F, "VREF", W_SIG, (13.1375, 11.95), (16.0, 11.95))
T(F, "VREF", W_SIG, (16.0, 11.95), (18.0, 11.95))
T(F, "VREF", W_SIG, (18.0, 11.95), (19.825, 11.95))
T(F, "VREF", W_SIG, (18.0, 10.425), (18.0, 11.95))
T(F, "VREF", W_SIG, (18.0, 11.95), (18.0, 13.175))
T(F, "VREF", W_SIG, (16.0, 11.95), (16.0, 17.0), (14.2, 18.8), (14.2, 20.1))
# RB_MID
T(F, "RB_MID", W_SIG, (18.0, 14.825), (18.0, 15.5))
T(F, "RB_MID", W_SIG, (18.0, 15.5), (18.0, 16.175))
# GND top
T(F, "GND", W_PWR, (10.8625, 11.0), (9.6, 11.0))
T(F, "GND", W_PWR, (10.175, 14.5), (11.2, 14.5))
T(F, "GND", W_PWR, (15.2, 10.375), (16.4, 10.375))
T(F, "GND", W_PWR, (21.375, 11.95), (22.4, 11.95))
T(F, "GND", W_PWR, (18.0, 17.825), (18.0, 18.4))
T(F, "GND", W_PWR, (18.0, 18.4), (16.2, 18.4), (15.2, 19.4), (15.2, 20.1))
# GND bottom
T(B, "GND", W_PWR, (9.6, 11.0), (9.6, 6.0), (16.4, 6.0), (16.4, 10.375))
T(B, "GND", W_PWR, (9.6, 11.0), (11.2, 12.6), (11.2, 14.5))
T(B, "GND", W_PWR, (11.2, 14.5), (11.2, 16.0), (10.0, 17.2), (9.4, 18.3))
T(F, "GND", W_PWR, (9.4, 18.3), (10.2, 19.1), (10.2, 20.1))
T(B, "GND", W_PWR, (16.4, 10.375), (21.0, 10.375), (22.4, 11.95))
T(B, "GND", W_PWR, (22.4, 11.95), (22.4, 17.0), (21.0, 18.4), (18.0, 18.4))

VIAS = [((14.2, 8.825), "V_LOGIC"), ((13.2, 18.0), "V_LOGIC"), ((9.4, 18.3), "GND"), ((18.0, 18.4), "GND"), ((9.6, 11.0), "GND"), ((11.2, 14.5), "GND"), ((16.4, 10.375), "GND"), ((22.4, 11.95), "GND")]
VIA_SIZE, VIA_DRILL = 0.6, 0.3

TOP_TEXT = [  # (text, x, y, size)
    ("WD COMPARATOR", 12.7, 1.5, 1.0),
    ("TLV7011 - 2026-11", 12.7, 2.9, 0.8),
    ("J1-1 GND", 3.4, 12.2, 0.8), ("J1-2 DET", 3.4, 13.4, 0.8), ("J1-3 THR", 3.4, 14.6, 0.8),
    ("J1-4 VL", 3.4, 15.8, 0.8), ("J1-5 REF", 3.4, 17.0, 0.8), ("J1-6 GND", 3.4, 18.2, 0.8),
    ("SET A", 22.1, 18.5, 0.8),
]
BOT_TEXT = [
    ("SET A", 12.7, 1.6, 0.8),
    ("R1 220k R2 30k", 12.7, 2.8, 0.8),
    ("R3 4.7M C1 100n", 12.7, 4.0, 0.8),
    ("C2 10n  R5 0R", 12.7, 5.2, 0.8),
    ("DNP: R4 C3", 12.7, 6.4, 0.8),
    ("Trip 0.63V  Rel 0.38V", 12.7, 7.6, 0.8),
    ("(at ENV_HOLD, calc)", 12.7, 15.6, 0.8),
    ("Rb=R2+R5  TLV7021: fit R4", 12.7, 16.8, 0.8),
    ("DET->U8.9 (cut side)", 12.7, 19.6, 0.8),
    ("THR->ENV_THRESHOLD", 12.7, 20.8, 0.8),
    ("VL->C26  GND->U8.7", 12.7, 22.0, 0.8),
    ("J1 JST SH6", 12.7, 23.2, 0.8),
    ("VHB THIS SIDE", 12.7, 24.4, 0.8),
]

CORNER_R = 2.0
def zone_outline(rz=3.2, n=24):
    """Board square with a circular bite (radius rz) around each corner hole; holes sit 3 mm from both edges."""
    def arc(c, a0, a1, ai):
        # sweep from a0 to a1 in the direction that passes through ai
        d = (a1 - a0) % (2 * math.pi)
        if not (0 < (ai - a0) % (2 * math.pi) < d): d -= 2 * math.pi
        return [(c[0] + rz * math.cos(a0 + d * t / n), c[1] + rz * math.sin(a0 + d * t / n)) for t in range(n + 1)]
    off = math.sqrt(rz ** 2 - 3.0 ** 2)
    TL, TR, BR, BL = HOLE_POS["H1"], HOLE_POS["H2"], HOLE_POS["H4"], HOLE_POS["H3"]
    ang = lambda c, p: math.atan2(p[1] - c[1], p[0] - c[0])
    pts = []
    for c, p_in, p_out, interior in [(TL, (0, 3.0 + off), (3.0 + off, 0), (1, 1)), (TR, (BW - 3.0 - off, 0), (BW, 3.0 + off), (-1, 1)),
                                     (BR, (BW, BW - 3.0 - off), (BW - 3.0 - off, BW), (-1, -1)), (BL, (3.0 + off, BW), (0, BW - 3.0 - off), (1, -1))]:
        pts += arc(c, ang(c, p_in), ang(c, p_out), math.atan2(interior[1], interior[0]))
    return pts

def gen_pcb():
    s = f'(kicad_pcb (version 20221018) (generator pcbnew)\n\n  (general\n    (thickness 1.6)\n  )\n\n  (paper "A4")\n'
    s += f'  (title_block\n    (title "WD comparator breakout (TLV7011)")\n    (date "{DATE}")\n    (rev "A")\n    (comment 1 "Rework board for headphone amp Rev A watchdog, Set A values")\n  )\n\n'
    s += """  (layers
    (0 "F.Cu" signal)
    (31 "B.Cu" signal)
    (32 "B.Adhes" user "B.Adhesive")
    (33 "F.Adhes" user "F.Adhesive")
    (34 "B.Paste" user)
    (35 "F.Paste" user)
    (36 "B.SilkS" user "B.Silkscreen")
    (37 "F.SilkS" user "F.Silkscreen")
    (38 "B.Mask" user)
    (39 "F.Mask" user)
    (40 "Dwgs.User" user "User.Drawings")
    (41 "Cmts.User" user "User.Comments")
    (42 "Eco1.User" user "User.Eco1")
    (43 "Eco2.User" user "User.Eco2")
    (44 "Edge.Cuts" user)
    (45 "Margin" user)
    (46 "B.CrtYd" user "B.Courtyard")
    (47 "F.CrtYd" user "F.Courtyard")
    (48 "B.Fab" user)
    (49 "F.Fab" user)
  )

  (setup
    (pad_to_mask_clearance 0)
    (aux_axis_origin 100 125.4)
    (grid_origin 100 125.4)
  )

"""
    for i, n in enumerate(NETS):
        s += f'  (net {i} "{n}")\n'
    s += "\n"
    for ref, (x, y, ang, roff, voff, doff) in PLACE.items():
        sym, fpid, val, dnp, nets, _ = PARTS[ref]
        s += footprint_body(fpid, ref, val, A(x, y), ang, nets, ref_off=roff, val_off=voff, dnp_off=doff)
    # outline
    rc = CORNER_R; k = rc * (1 - 1 / math.sqrt(2))
    for (p, q) in [((rc, 0), (BW - rc, 0)), ((BW, rc), (BW, BW - rc)), ((BW - rc, BW), (rc, BW)), ((0, BW - rc), (0, rc))]:
        a, b = A(*p), A(*q)
        s += f'  (gr_line (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (tstamp {U()}))\n'
    for (p, m, q) in [((0, rc), (k, k), (rc, 0)), ((BW - rc, 0), (BW - k, k), (BW, rc)),
                      ((BW, BW - rc), (BW - k, BW - k), (BW - rc, BW)), ((rc, BW), (k, BW - k), (0, BW - rc))]:
        a, mm, b = A(*p), A(*m), A(*q)
        s += f'  (gr_arc (start {f(a[0])} {f(a[1])}) (mid {f(mm[0])} {f(mm[1])}) (end {f(b[0])} {f(b[1])}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (tstamp {U()}))\n'
    for (t, x, y, sz) in TOP_TEXT:
        ax, ay = A(x, y)
        s += f'  (gr_text "{t}" (at {f(ax)} {f(ay)}) (layer "F.SilkS") (tstamp {U()})\n    (effects (font (size {f(sz)} {f(sz)}) (thickness {f(max(0.13, round(sz * 0.16, 3)))}))))\n'
    for (t, x, y, sz) in BOT_TEXT:
        ax, ay = A(x, y)
        s += f'  (gr_text "{t}" (at {f(ax)} {f(ay)}) (layer "B.SilkS") (tstamp {U()})\n    (effects (font (size {f(sz)} {f(sz)}) (thickness {f(max(0.13, round(sz * 0.16, 3)))})) (justify mirror)))\n'
    for (layer, net, w, pts) in TRACKS:
        for p, q in zip(pts[:-1], pts[1:]):
            a, b = A(*p), A(*q)
            s += f'  (segment (start {f(a[0])} {f(a[1])}) (end {f(b[0])} {f(b[1])}) (width {f(w)}) (layer "{layer}") (net {NID[net]}) (tstamp {U()}))\n'
    for (p, net) in VIAS:
        a = A(*p)
        s += f'  (via (at {f(a[0])} {f(a[1])}) (size {f(VIA_SIZE)}) (drill {f(VIA_DRILL)}) (layers "F.Cu" "B.Cu") (net {NID[net]}) (tstamp {U()}))\n'
    # bottom GND pour (connectivity does not depend on it; fill with B before plotting/upload)
    pts = [A(*p) for p in zone_outline()]
    s += f'  (zone (net {NID["GND"]}) (net_name "GND") (layer "B.Cu") (tstamp {U()}) (hatch edge 0.5)\n'
    s += '    (connect_pads (clearance 0.3))\n    (min_thickness 0.25) (filled_areas_thickness no)\n'
    s += '    (fill (thermal_gap 0.4) (thermal_bridge_width 0.4))\n'
    s += "    (polygon\n      (pts\n        " + " ".join(f"(xy {f(x)} {f(y)})" for x, y in pts) + "\n      )\n    )\n  )\n"
    s += ")\n"
    return s

# ============================================================================ SCHEMATIC
FONT = "(effects (font (size 1.27 1.27)))"
FONT_H = "(effects (font (size 1.27 1.27)) hide)"

LIB = {}
LIB["Device:R"] = dict(pins=[("1", 0, 3.81, 270, 1.27, "~", "passive"), ("2", 0, -3.81, 90, 1.27, "~", "passive")], text=f'''  (symbol "Device:R" (pin_numbers hide) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "R" (at 2.032 0 90) {FONT})
      (property "Value" "R" (at 0 0 90) {FONT})
      (property "Footprint" "" (at -1.778 0 90) {FONT_H})
      (property "Datasheet" "~" (at 0 0 0) {FONT_H})
      (property "ki_keywords" "R res resistor" (at 0 0 0) {FONT_H})
      (property "ki_description" "Resistor" (at 0 0 0) {FONT_H})
      (property "ki_fp_filters" "R_*" (at 0 0 0) {FONT_H})
      (symbol "R_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
      )
      (symbol "R_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "~" {FONT}) (number "1" {FONT}))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "~" {FONT}) (number "2" {FONT}))
      )
    )
''')
LIB["Device:C"] = dict(pins=[("1", 0, 3.81, 270, 2.794, "~", "passive"), ("2", 0, -3.81, 90, 2.794, "~", "passive")], text=f'''  (symbol "Device:C" (pin_numbers hide) (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "C" (at 0.635 2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "C" (at 0.635 -2.54 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "" (at 0.9652 -3.81 0) {FONT_H})
      (property "Datasheet" "~" (at 0 0 0) {FONT_H})
      (property "ki_keywords" "cap capacitor" (at 0 0 0) {FONT_H})
      (property "ki_description" "Unpolarized capacitor" (at 0 0 0) {FONT_H})
      (property "ki_fp_filters" "C_*" (at 0 0 0) {FONT_H})
      (symbol "C_0_1"
        (polyline (pts (xy -2.032 -0.762) (xy 2.032 -0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
        (polyline (pts (xy -2.032 0.762) (xy 2.032 0.762)) (stroke (width 0.508) (type default)) (fill (type none)))
      )
      (symbol "C_1_1"
        (pin passive line (at 0 3.81 270) (length 2.794) (name "~" {FONT}) (number "1" {FONT}))
        (pin passive line (at 0 -3.81 90) (length 2.794) (name "~" {FONT}) (number "2" {FONT}))
      )
    )
''')
LIB["Mechanical:MountingHole"] = dict(pins=[], text=f'''  (symbol "Mechanical:MountingHole" (pin_names (offset 1.016)) (in_bom no) (on_board yes)
      (property "Reference" "H" (at 0 5.08 0) {FONT})
      (property "Value" "MountingHole" (at 0 3.175 0) {FONT})
      (property "Footprint" "" (at 0 0 0) {FONT_H})
      (property "Datasheet" "~" (at 0 0 0) {FONT_H})
      (property "ki_keywords" "mounting hole" (at 0 0 0) {FONT_H})
      (property "ki_description" "Mounting Hole without connection" (at 0 0 0) {FONT_H})
      (property "ki_fp_filters" "MountingHole*" (at 0 0 0) {FONT_H})
      (symbol "MountingHole_0_1"
        (circle (center 0 0) (radius 1.27) (stroke (width 1.27) (type default)) (fill (type none)))
      )
    )
''')
LIB["power:GND"] = dict(pins=[("1", 0, 0, 270, 0, "GND", "power_in")], text=f'''  (symbol "power:GND" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -6.35 0) {FONT_H})
      (property "Value" "GND" (at 0 -3.81 0) {FONT})
      (property "Footprint" "" (at 0 0 0) {FONT_H})
      (property "Datasheet" "" (at 0 0 0) {FONT_H})
      (property "ki_keywords" "global power" (at 0 0 0) {FONT_H})
      (property "ki_description" "Power symbol creates a global label with name \\"GND\\" , ground" (at 0 0 0) {FONT_H})
      (symbol "GND_0_1"
        (polyline (pts (xy 0 0) (xy 0 -1.27) (xy 1.27 -1.27) (xy 0 -2.54) (xy -1.27 -1.27) (xy 0 -1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "GND_1_1"
        (pin power_in line (at 0 0 270) (length 0) hide (name "GND" {FONT}) (number "1" {FONT}))
      )
    )
''')
LIB["power:PWR_FLAG"] = dict(pins=[("1", 0, 0, 90, 0, "pwr", "power_out")], text=f'''  (symbol "power:PWR_FLAG" (power) (pin_numbers hide) (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "#FLG" (at 0 1.905 0) {FONT_H})
      (property "Value" "PWR_FLAG" (at 0 3.81 0) {FONT})
      (property "Footprint" "" (at 0 0 0) {FONT_H})
      (property "Datasheet" "~" (at 0 0 0) {FONT_H})
      (property "ki_keywords" "flag power" (at 0 0 0) {FONT_H})
      (property "ki_description" "Special symbol for telling ERC where power comes from" (at 0 0 0) {FONT_H})
      (symbol "PWR_FLAG_0_0"
        (pin power_out line (at 0 0 90) (length 0) (name "pwr" {FONT}) (number "1" {FONT}))
      )
      (symbol "PWR_FLAG_0_1"
        (polyline (pts (xy 0 0) (xy 0 1.27) (xy -1.016 1.905) (xy 0 2.54) (xy 1.016 1.905) (xy 0 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
    )
''')

def custom_syms(prefix):
    """Custom symbols; prefix = 'wd_comp_breakout:' for embedding, '' for the .kicad_sym library."""
    p = prefix
    vl = f'''  (symbol "{p}V_LOGIC" (power) (pin_names (offset 0)) (in_bom yes) (on_board yes)
      (property "Reference" "#PWR" (at 0 -3.81 0) {FONT_H})
      (property "Value" "V_LOGIC" (at 0 3.81 0) {FONT})
      (property "Footprint" "" (at 0 0 0) {FONT_H})
      (property "Datasheet" "" (at 0 0 0) {FONT_H})
      (property "ki_description" "Power symbol: V_LOGIC (2.5 V watchdog rail on Rev A)" (at 0 0 0) {FONT_H})
      (symbol "V_LOGIC_0_1"
        (polyline (pts (xy -0.762 1.27) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 0) (xy 0 2.54)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0 2.54) (xy 0.762 1.27)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "V_LOGIC_1_1"
        (pin power_in line (at 0 0 90) (length 0) hide (name "V_LOGIC" {FONT}) (number "1" {FONT}))
      )
    )
'''
    cmp = f'''  (symbol "{p}TLV7011DBV" (pin_names (offset 0.254)) (in_bom yes) (on_board yes)
      (property "Reference" "U" (at 2.54 6.35 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Value" "TLV7011DBV" (at 2.54 3.81 0) (effects (font (size 1.27 1.27)) (justify left)))
      (property "Footprint" "Package_TO_SOT_SMD:SOT-23-5" (at 0 -10.16 0) {FONT_H})
      (property "Datasheet" "https://www.ti.com/lit/ds/symlink/tlv7011.pdf" (at 0 0 0) {FONT_H})
      (property "ki_keywords" "comparator push-pull nanopower" (at 0 0 0) {FONT_H})
      (property "ki_description" "Nanopower comparator, push-pull, SOT-23-5 (DBV). Pinout per TI SLVSDM5F: 1 OUT, 2 VEE, 3 IN+, 4 IN-, 5 VCC" (at 0 0 0) {FONT_H})
      (symbol "TLV7011DBV_0_1"
        (polyline (pts (xy -5.08 5.08) (xy 5.08 0) (xy -5.08 -5.08) (xy -5.08 5.08)) (stroke (width 0.254) (type default)) (fill (type background)))
      )
      (symbol "TLV7011DBV_1_1"
        (pin output line (at 7.62 0 180) (length 2.54) (name "~" {FONT}) (number "1" {FONT}))
        (pin power_in line (at -2.54 -7.62 90) (length 3.81) (name "VEE" {FONT}) (number "2" {FONT}))
        (pin input line (at -7.62 2.54 0) (length 2.54) (name "+" {FONT}) (number "3" {FONT}))
        (pin input line (at -7.62 -2.54 0) (length 2.54) (name "-" {FONT}) (number "4" {FONT}))
        (pin power_in line (at -2.54 7.62 270) (length 3.81) (name "VCC" {FONT}) (number "5" {FONT}))
      )
    )
'''
    trim = f'''  (symbol "{p}R_Trim" (pin_names (offset 0) hide) (in_bom yes) (on_board yes)
      (property "Reference" "RV" (at -4.445 0 90) {FONT})
      (property "Value" "R_Trim" (at -2.54 0 90) {FONT})
      (property "Footprint" "" (at 0 0 0) {FONT_H})
      (property "Datasheet" "~" (at 0 0 0) {FONT_H})
      (property "ki_description" "Trim potentiometer, pins 1/3 ends, 2 wiper" (at 0 0 0) {FONT_H})
      (symbol "R_Trim_0_1"
        (rectangle (start -1.016 -2.54) (end 1.016 2.54) (stroke (width 0.254) (type default)) (fill (type none)))
        (polyline (pts (xy 1.27 0) (xy 0.508 0)) (stroke (width 0) (type default)) (fill (type none)))
        (polyline (pts (xy 0.508 0) (xy 1.016 0.508) (xy 1.016 -0.508) (xy 0.508 0)) (stroke (width 0) (type default)) (fill (type outline)))
        (polyline (pts (xy -1.524 -1.524) (xy 1.524 1.524)) (stroke (width 0) (type default)) (fill (type none)))
      )
      (symbol "R_Trim_1_1"
        (pin passive line (at 0 3.81 270) (length 1.27) (name "1" {FONT}) (number "1" {FONT}))
        (pin passive line (at 2.54 0 180) (length 1.27) (name "2" {FONT}) (number "2" {FONT}))
        (pin passive line (at 0 -3.81 90) (length 1.27) (name "3" {FONT}) (number "3" {FONT}))
      )
    )
'''
    conn = f'''  (symbol "{p}Conn_01x06" (pin_names (offset 1.016) hide) (in_bom yes) (on_board yes)
      (property "Reference" "J" (at 0 7.62 0) {FONT})
      (property "Value" "Conn_01x06" (at 0 -10.16 0) {FONT})
      (property "Footprint" "" (at 0 0 0) {FONT_H})
      (property "Datasheet" "~" (at 0 0 0) {FONT_H})
      (property "ki_description" "Generic connector, single row, 01x06" (at 0 0 0) {FONT_H})
      (symbol "Conn_01x06_1_1"
        (rectangle (start -1.27 6.35) (end 1.27 -8.89) (stroke (width 0.254) (type default)) (fill (type background)))
''' + "".join(f'''        (rectangle (start -1.27 {f(5.207 - 2.54 * i)}) (end 0 {f(4.953 - 2.54 * i)}) (stroke (width 0.1524) (type default)) (fill (type none)))
''' for i in range(6)) + "".join(f'''        (pin passive line (at -5.08 {f(5.08 - 2.54 * i)} 0) (length 3.81) (name "Pin_{i + 1}" {FONT}) (number "{i + 1}" {FONT}))
''' for i in range(6)) + '''      )
    )
'''
    return vl, cmp, trim, conn

vl, cmp, trim, conn = custom_syms("wd_comp_breakout:")
LIB["wd_comp_breakout:V_LOGIC"] = dict(pins=[("1", 0, 0, 90, 0, "V_LOGIC", "power_in")], text=vl)
LIB["wd_comp_breakout:TLV7011DBV"] = dict(pins=[("1", 7.62, 0, 180, 2.54, "~", "output"), ("2", -2.54, -7.62, 90, 3.81, "VEE", "power_in"),
    ("3", -7.62, 2.54, 0, 2.54, "+", "input"), ("4", -7.62, -2.54, 0, 2.54, "-", "input"), ("5", -2.54, 7.62, 270, 3.81, "VCC", "power_in")], text=cmp)
LIB["wd_comp_breakout:R_Trim"] = dict(pins=[("1", 0, 3.81, 270, 1.27, "1", "passive"), ("2", 2.54, 0, 180, 1.27, "2", "passive"), ("3", 0, -3.81, 90, 1.27, "3", "passive")], text=trim)
LIB["Connector_Generic:Conn_01x06"] = dict(pins=[(str(i + 1), -5.08, 5.08 - 2.54 * i, 0, 3.81, f"Pin_{i+1}", "passive") for i in range(6)],
                                          text=conn.replace('"wd_comp_breakout:Conn_01x06"', '"Connector_Generic:Conn_01x06"'))
# J1 uses the stock lib_id; the custom lib keeps its own copy too.

# --- schematic instances
SCH_SYMS = []   # (lib_id, ref, value, at(x,y), angle, dnp, footprint, props_positions, description)
WIRES, JUNCTIONS, LABELS, TEXTS = [], [], [], []
pwr_n = [0]; flg_n = [0]

def sym(lib_id, ref, value, x, y, angle=0, dnp=False, fp="", ref_at=None, val_at=None, hide_ref=False, desc=""):
    SCH_SYMS.append(dict(lib_id=lib_id, ref=ref, value=value, at=(x, y), angle=angle, dnp=dnp, fp=fp,
                         ref_at=ref_at, val_at=val_at, hide_ref=hide_ref, desc=desc))

def part(ref, x, y, angle=0, ref_at=None, val_at=None):
    lib, fp, val, dnp, nets, desc = PARTS[ref]
    sym(lib, ref, val, x, y, angle, dnp, fp, ref_at, val_at, desc=desc)

def gnd(x, y, angle=0):
    pwr_n[0] += 1
    sym("power:GND", f"#PWR0{pwr_n[0]:02d}", "GND", x, y, angle, hide_ref=True)

def vlogic(x, y, angle=0):
    pwr_n[0] += 1
    sym("wd_comp_breakout:V_LOGIC", f"#PWR0{pwr_n[0]:02d}", "V_LOGIC", x, y, angle, hide_ref=True)

def flag(x, y, angle=0):
    flg_n[0] += 1
    sym("power:PWR_FLAG", f"#FLG0{flg_n[0]:02d}", "PWR_FLAG", x, y, angle, hide_ref=True)

def W(*pts):
    for p, q in zip(pts[:-1], pts[1:]):
        WIRES.append((p, q))

def J(x, y): JUNCTIONS.append((x, y))
def L(name, x, y, angle=0, just="left bottom"): LABELS.append((name, x, y, angle, just))

# Comparator
part("U1", 127, 88.9, ref_at=(129.54, 82.55), val_at=(129.54, 85.09))
vlogic(124.46, 81.28)
gnd(124.46, 96.52)
# IN+ / Rh loop
W((119.38, 86.36), (111.76, 86.36))
W((111.76, 86.36), (106.68, 86.36))
W((106.68, 86.36), (96.52, 86.36))
J(111.76, 86.36); J(106.68, 86.36)
L("ENV_THRESHOLD", 96.52, 86.36)
W((111.76, 86.36), (111.76, 71.12), (123.19, 71.12))
part("R3", 127, 71.12, angle=90, ref_at=(127, 66.04), val_at=(127, 68.58))
W((130.81, 71.12), (142.24, 71.12), (142.24, 88.9))
W((134.62, 88.9), (142.24, 88.9))
W((142.24, 88.9), (147.32, 88.9))
W((147.32, 88.9), (154.94, 88.9))
J(142.24, 88.9); J(147.32, 88.9)
L("AUDIO_DETECT", 154.94, 88.9)
part("R4", 147.32, 82.55, ref_at=(149.86, 81.28), val_at=(149.86, 83.82))
vlogic(147.32, 78.74)
W((147.32, 86.36), (147.32, 88.9))
part("C3", 106.68, 90.17, ref_at=(108.585, 88.9), val_at=(108.585, 92.71))
gnd(106.68, 93.98)
# Reference network
W((119.38, 91.44), (114.3, 91.44), (114.3, 101.6))
part("R1", 99.06, 97.79, ref_at=(101.6, 96.52), val_at=(101.6, 99.06))
vlogic(99.06, 93.98)
W((99.06, 101.6), (106.68, 101.6))
W((106.68, 101.6), (114.3, 101.6))
J(106.68, 101.6); J(114.3, 101.6)
L("VREF", 99.06, 101.6)
part("R2", 106.68, 105.41, ref_at=(109.22, 104.14), val_at=(109.22, 106.68))
part("C2", 114.3, 105.41, ref_at=(116.205, 104.14), val_at=(116.205, 106.68))
gnd(114.3, 109.22)
W((106.68, 109.22), (106.68, 110.49))
W((106.68, 110.49), (106.68, 111.76))
J(106.68, 110.49)
W((99.06, 110.49), (106.68, 110.49))
L("RB_MID", 99.06, 110.49)
part("R5", 106.68, 115.57, ref_at=(109.22, 114.3), val_at=(109.22, 116.84))
gnd(106.68, 119.38)
# Decoupling + power flags
part("C1", 139.7, 106.68, ref_at=(141.605, 105.41), val_at=(141.605, 107.95))
W((139.7, 100.33), (139.7, 102.87))
vlogic(139.7, 100.33)
W((139.7, 100.33), (149.86, 100.33))
J(139.7, 100.33)
flag(149.86, 100.33)
W((139.7, 110.49), (139.7, 113.03))
gnd(139.7, 113.03)
W((139.7, 113.03), (149.86, 113.03))
J(139.7, 113.03)
flag(149.86, 113.03)
# Connector
part("J1", 190.5, 101.6, ref_at=(190.5, 93.98), val_at=(190.5, 111.76))
for i, net in enumerate(["GND", "AUDIO_DETECT", "ENV_THRESHOLD", "V_LOGIC", "VREF", "GND"]):
    y = 96.52 + 2.54 * i
    W((170.18, y), (185.42, y))
    if net == "GND":
        gnd(170.18, y, 270)
    elif net == "V_LOGIC":
        vlogic(170.18, y, 90)
    else:
        L(net, 170.18, y)

for _i, _h in enumerate(HOLE_POS):
    part(_h, 101.6 + 15.24 * _i, 50.8, ref_at=(104.14 + 15.24 * _i, 49.53), val_at=(104.14 + 15.24 * _i, 52.07))
NOTE = ("Watchdog comparator breakout for Rev A rework (Daniel's units), Set A values.\\n"
        "IN+ = ENV_THRESHOLD node on Rev A (R30 = R31 = 470k stay on the main board).\\n"
        "Vref = V_LOGIC x R2/(R1+R2) = 2.5 x 30k/250k = 0.30 V\\n"
        "Trip (ENV_HOLD) = Vref x (1 + R30/R31 + R30/R3) = 0.30 x (1 + 1 + 0.1) = 0.63 V\\n"
        "Release (ENV_HOLD) = Trip - V_LOGIC x R30/R3 = 0.63 - 0.25 = 0.38 V   (calculated; TLV7011 internal hyst. shifts each by ~4 mV)\\n"
        "Set B: R2 = 20k, R3 = 10M (trip 0.43 V, release 0.31 V).  Set B+: R2 = 20k, R5 = trimmer wired across its pads (Rb = R2 + R5).\\n"
        "TLV7021 (open-drain): fit R4 100k pull-up.  C3 (DNP): optional IN+ filter if the wire picks up hum, ~1 nF.\\n"
        "J1 = JST SH 6-pin right angle (SM06B-SRSS-TB); all SMD, flat bottom for VHB.  Rb = R2 + R5: two 0603s in series, swap either to tune.\n"
        "Rev A hookup: cut AUDIO_DETECT between U7.2 and U8.9; J1.2 (DET) -> U8.9 / TP8 side.\\n"
        "J1.3 (THR) -> ENV_THRESHOLD (R30/R31 junction).  J1.4 (VL) -> V_LOGIC at C26.  J1.1 (GND) -> U8.7.")
TEXTS.append((NOTE, 88.9, 134.62))
TEXTS.append(("Pinout per TI SLVSDM5F (SOT-23-5): 1 OUT, 2 VEE, 3 IN+, 4 IN-, 5 VCC", 88.9, 60.96))

FIELD_ID = {"Reference": 0, "Value": 1, "Footprint": 2, "Datasheet": 3}
def add_ids(txt):
    out = []
    for block in re.split(r'(?=\(symbol )', txt):
        n = [4]
        def rep(m):
            name = m.group(1)
            if name in FIELD_ID: i = FIELD_ID[name]
            else: i = n[0]; n[0] += 1
            return f'(property "{name}" "{m.group(2)}" (id {i}) (at'
        out.append(re.sub(r'\(property "([^"]+)" "((?:[^"\\]|\\.)*)" \(at', rep, block))
    return "".join(out)

def gen_sch():
    s = f'(kicad_sch (version 20230121) (generator eeschema)\n\n  (uuid {ROOT})\n\n  (paper "A4")\n\n'
    s += f'  (title_block\n    (title "WD comparator breakout (TLV7011)")\n    (date "{DATE}")\n    (rev "A")\n    (company "Headphone amp project")\n    (comment 1 "Rework board for Rev A watchdog: replaces U7A as the AUDIO_DETECT driver")\n  )\n\n'
    s += "  (lib_symbols\n"
    used = sorted({d["lib_id"] for d in SCH_SYMS})
    for lid in used:
        s += "  " + LIB[lid]["text"].lstrip().replace("\n  ", "\n    ")
    s += "  )\n\n"
    for (x, y) in JUNCTIONS:
        s += f"  (junction (at {f(x)} {f(y)}) (diameter 0) (color 0 0 0 0)\n    (uuid {U()})\n  )\n"
    for (p, q) in WIRES:
        s += f"  (wire (pts (xy {f(p[0])} {f(p[1])}) (xy {f(q[0])} {f(q[1])}))\n    (stroke (width 0) (type default))\n    (uuid {U()})\n  )\n"
    for (n, x, y, a, just) in LABELS:
        s += f'  (label "{n}" (at {f(x)} {f(y)} {a}) (fields_autoplaced)\n    (effects (font (size 1.27 1.27)) (justify {just}))\n    (uuid {U()})\n  )\n'
    for (t, x, y) in TEXTS:
        s += f'  (text "{t}" (at {f(x)} {f(y)} 0)\n    (effects (font (size 1.27 1.27)) (justify left bottom))\n    (uuid {U()})\n  )\n'
    for d in SCH_SYMS:
        x, y = d["at"]
        ref = d["ref"]
        uid = SYM_UUID.get(ref) or U()
        s += f'  (symbol (lib_id "{d["lib_id"]}") (at {f(x)} {f(y)} {d["angle"]}) (unit 1)\n'
        s += f'    (in_bom {"no" if ref.startswith("H") else "yes"}) (on_board yes) (dnp {"yes" if d["dnp"] else "no"})\n    (uuid {uid})\n'
        if d["hide_ref"]:
            ra = (x, y + (3.81 if "GND" in d["lib_id"] else -3.81))
            s += f'    (property "Reference" "{ref}" (at {f(ra[0])} {f(ra[1])} 0) {FONT_H})\n'
            # value position follows lib default, rotated
            lib = d["lib_id"]
            if lib == "power:GND":
                vx, vy = {0: (0, 3.81), 90: (3.81, 0), 180: (0, -3.81), 270: (-3.81, 0)}[d["angle"]]
                just = "" if d["angle"] in (0, 180) else (" (justify right)" if d["angle"] == 270 else " (justify left)")
            elif lib == "power:PWR_FLAG":
                vx, vy = (0, -3.81); just = ""
            else:
                vx, vy = {0: (0, -3.81), 90: (-3.81, 0), 180: (0, 3.81), 270: (3.81, 0)}[d["angle"]]
                just = "" if d["angle"] in (0, 180) else (" (justify right)" if d["angle"] == 90 else " (justify left)")
            s += f'    (property "Value" "{d["value"]}" (at {f(x + vx)} {f(y + vy)} 0) (effects (font (size 1.27 1.27)){just}))\n'
            s += f'    (property "Footprint" "" (at {f(x)} {f(y)} 0) {FONT_H})\n'
            s += f'    (property "Datasheet" "" (at {f(x)} {f(y)} 0) {FONT_H})\n'
        else:
            ra, va = d["ref_at"], d["val_at"]
            j = " (justify left)" if d["angle"] == 0 and d["lib_id"] != "Connector_Generic:Conn_01x06" else ""
            s += f'    (property "Reference" "{ref}" (at {f(ra[0])} {f(ra[1])} 0) (effects (font (size 1.27 1.27)){j}))\n'
            s += f'    (property "Value" "{d["value"]}" (at {f(va[0])} {f(va[1])} 0) (effects (font (size 1.27 1.27)){j}))\n'
            s += f'    (property "Footprint" "{d["fp"]}" (at {f(x)} {f(y)} 0) {FONT_H})\n'
            ds = "https://www.ti.com/lit/ds/symlink/tlv7011.pdf" if ref == "U1" else "~"
            s += f'    (property "Datasheet" "{ds}" (at {f(x)} {f(y)} 0) {FONT_H})\n'
            s += f'    (property "Description" "{d["desc"]}" (at {f(x)} {f(y)} 0) {FONT_H})\n'
        for pin in LIB[d["lib_id"]]["pins"]:
            s += f'    (pin "{pin[0]}" (uuid {U()}))\n'
        s += f'    (instances\n      (project "{PROJ}"\n        (path "/{ROOT}"\n          (reference "{ref}") (unit 1)\n        )\n      )\n    )\n  )\n'
    s += '\n  (sheet_instances\n    (path "/" (page "1"))\n  )\n)\n'
    return add_ids(s)

def gen_symlib():
    vl, cmp, trim, conn = custom_syms("")
    s = "(kicad_symbol_lib (version 20220914) (generator kicad_symbol_editor)\n"
    for t in (vl, cmp, trim):
        s += t
    s += ")\n"
    return add_ids(s)

def gen_trim_mod():
    name = "WirePads_1x06_P2.54mm_SMD"
    fpid = f"{PROJ}:{name}"
    body = footprint_body(fpid, "REF**", name, (0, 0), 0, {}, pcb=False)
    body = body.replace(f'  (footprint "{fpid}"', f'(footprint "{name}" (version 20221018) (generator pcbnew)', 1)
    body = body.replace('(layer "F.Cu")\n', '(layer "F.Cu")\n    (descr "Six 1.6 x 3.0 mm SMD pads at 2.54 mm pitch for soldering wires; top side only so the board bottom stays flat")\n', 1)
    # de-indent closing paren
    return body.rstrip().rstrip(")").rstrip() + "\n)\n"

def gen_pro():
    pro = {
        "board": {"design_settings": {
            "defaults": {"board_outline_line_width": 0.1, "copper_line_width": 0.2, "copper_text_size_h": 1.5,
                         "copper_text_size_v": 1.5, "copper_text_thickness": 0.3, "silk_line_width": 0.12,
                         "silk_text_size_h": 0.8, "silk_text_size_v": 0.8, "silk_text_thickness": 0.12},
            "rules": {"min_clearance": 0.1524, "min_track_width": 0.1524, "min_via_diameter": 0.508,
                      "min_through_hole_diameter": 0.254, "min_via_annular_width": 0.127, "min_hole_clearance": 0.254,
                      "min_copper_edge_clearance": 0.381, "min_hole_to_hole": 0.254, "min_silk_clearance": 0.0,
                      "min_text_height": 0.6, "min_text_thickness": 0.09},
            "track_widths": [0.0, 0.25, 0.4], "via_dimensions": [{"diameter": 0.0, "drill": 0.0}, {"diameter": 0.6, "drill": 0.3}]}},
        "meta": {"filename": f"{PROJ}.kicad_pro", "version": 1},
        "net_settings": {"classes": [{"name": "Default", "clearance": 0.2, "track_width": 0.25, "via_diameter": 0.6,
                                      "via_drill": 0.3, "microvia_diameter": 0.3, "microvia_drill": 0.1,
                                      "diff_pair_gap": 0.25, "diff_pair_width": 0.2, "line_style": 0, "wire_width": 6,
                                      "bus_width": 12, "pcb_color": "rgba(0, 0, 0, 0.000)", "schematic_color": "rgba(0, 0, 0, 0.000)"}],
                         "meta": {"version": 3}},
        "sheets": [[ROOT, ""]],
        "text_variables": {},
    }
    return json.dumps(pro, indent=2) + "\n"

if __name__ == "__main__":
    files = {
        f"{PROJ}.kicad_pcb": gen_pcb(),
        f"{PROJ}.kicad_sch": gen_sch(),
        f"{PROJ}.kicad_pro": gen_pro(),
        f"{PROJ}.kicad_sym": gen_symlib(),
        "sym-lib-table": f'(sym_lib_table\n  (version 7)\n  (lib (name "{PROJ}")(type "KiCad")(uri "${{KIPRJMOD}}/{PROJ}.kicad_sym")(options "")(descr "Project symbols"))\n)\n',
    }
    for name, txt in files.items():
        with open(os.path.join(OUT, name), "w") as fh:
            fh.write(txt)
    print("wrote", ", ".join(files))
