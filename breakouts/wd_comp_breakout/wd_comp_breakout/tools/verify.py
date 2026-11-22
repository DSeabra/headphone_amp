#!/usr/bin/env python3
"""Independent checks on the generated KiCad files: parses the files themselves (not gen.py data)."""
import math, sys, itertools, re
from collections import defaultdict

D = sys.argv[1]
P = "wd_comp_breakout"

# ------------------------------------------------------------------ s-expression parser
def parse(txt):
    toks = re.findall(r'\(|\)|"(?:[^"\\]|\\.)*"|[^\s()]+', txt)
    stack, cur = [], []
    for t in toks:
        if t == "(":
            stack.append(cur); cur = []
        elif t == ")":
            done = cur; cur = stack.pop(); cur.append(done)
        else:
            cur.append(t[1:-1] if t.startswith('"') else t)
    assert not stack, "unbalanced parens"
    assert len(cur) == 1, f"top-level items: {len(cur)}"
    return cur[0]

def kids(n, name): return [c for c in n if isinstance(c, list) and c and c[0] == name]
def kid(n, name):
    k = kids(n, name); return k[0] if k else None

problems = []
def bad(msg): problems.append(msg); print("  !!", msg)

# ------------------------------------------------------------------ PCB
pcb = parse(open(f"{D}/{P}.kicad_pcb").read())
assert pcb[0] == "kicad_pcb"
netname = {int(n[1]): n[2] for n in kids(pcb, "net")}

def rot(x, y, deg):
    t = math.radians(deg)
    return (x * math.cos(t) + y * math.sin(t), -x * math.sin(t) + y * math.cos(t))

items = []  # dict(kind, layers, geom, net, ref)
npth = []   # (ref, centre, drill)
pads = {}
for fp in kids(pcb, "footprint"):
    at = kid(fp, "at"); fx, fy = float(at[1]), float(at[2]); fa = float(at[3]) if len(at) > 3 else 0
    ref = [c for c in kids(fp, "fp_text") if c[1] == "reference"][0][2]
    for pd in kids(fp, "pad"):
        num, typ, shape = pd[1], pd[2], pd[3]
        if typ == "np_thru_hole":
            pa = kid(pd, "at"); dx, dy = rot(float(pa[1]), float(pa[2]), fa)
            npth.append((ref, (fx + dx, fy + dy), float(kid(pd, "drill")[1])))
            continue
        pa = kid(pd, "at"); lx, ly = float(pa[1]), float(pa[2]); pang = float(pa[3]) if len(pa) > 3 else 0
        if abs(pang - fa) > 1e-6:
            bad(f"{ref}.{num}: pad angle {pang} != footprint angle {fa}")
        sz = kid(pd, "size"); w, h = float(sz[1]), float(sz[2])
        dx, dy = rot(lx, ly, fa); cx, cy = fx + dx, fy + dy
        # rectangle corners (pad local axes rotated by pad angle)
        hw, hh = w / 2, h / 2
        corners = [(cx + a, cy + b) for a, b in (rot(-hw, -hh, pang), rot(hw, -hh, pang), rot(hw, hh, pang), rot(-hw, hh, pang))]
        nn = kid(pd, "net"); net = nn[2] if nn else None
        layers = {"F.Cu"} if typ == "smd" else {"F.Cu", "B.Cu"}
        if shape in ("circle", "oval") and abs(w - h) < 1e-9:
            geom = ("circle", (cx, cy), w / 2)
        else:
            geom = ("poly", corners)
        it = dict(kind="pad", layers=layers, geom=geom, net=net, ref=f"{ref}.{num}", center=(cx, cy))
        if typ == "thru_hole":
            it["drill"] = float(kid(pd, "drill")[1])
        items.append(it); pads[f"{ref}.{num}" if num != "MP" else f"{ref}.MP{'L' if dx < 0 else 'R'}"] = it
for sg in kids(pcb, "segment"):
    a = kid(sg, "start"); b = kid(sg, "end")
    w = float(kid(sg, "width")[1]); layer = kid(sg, "layer")[1]; net = netname[int(kid(sg, "net")[1])]
    items.append(dict(kind="seg", layers={layer}, geom=("cap", (float(a[1]), float(a[2])), (float(b[1]), float(b[2])), w / 2), net=net,
                      ref=f"seg {layer} {net} ({a[1]},{a[2]})-({b[1]},{b[2]})"))
for v in kids(pcb, "via"):
    at = kid(v, "at"); net = netname[int(kid(v, "net")[1])]
    sz = float(kid(v, "size")[1]); dr = float(kid(v, "drill")[1])
    if (sz - dr) / 2 < 0.127: bad(f"via annular ring {(sz-dr)/2}")
    items.append(dict(kind="via", layers={"F.Cu", "B.Cu"}, geom=("circle", (float(at[1]), float(at[2])), sz / 2), net=net,
                      ref=f"via {net} ({at[1]},{at[2]})", center=(float(at[1]), float(at[2]))))

# geometry
def pt_seg(p, a, b):
    ax, ay = a; bx, by = b; px, py = p
    dx, dy = bx - ax, by - ay; L2 = dx * dx + dy * dy
    t = 0 if L2 == 0 else max(0, min(1, ((px - ax) * dx + (py - ay) * dy) / L2))
    return math.hypot(px - (ax + t * dx), py - (ay + t * dy))
def seg_inter(a, b, c, d):
    def cr(o, p, q): return (p[0] - o[0]) * (q[1] - o[1]) - (p[1] - o[1]) * (q[0] - o[0])
    d1, d2, d3, d4 = cr(c, d, a), cr(c, d, b), cr(a, b, c), cr(a, b, d)
    return (d1 * d2 < 0) and (d3 * d4 < 0)
def seg_seg(a, b, c, d):
    if seg_inter(a, b, c, d): return 0.0
    return min(pt_seg(a, c, d), pt_seg(b, c, d), pt_seg(c, a, b), pt_seg(d, a, b))
def in_poly(p, poly):
    x, y = p; ins = False
    for (x1, y1), (x2, y2) in zip(poly, poly[1:] + poly[:1]):
        if (y1 > y) != (y2 > y) and x < (x2 - x1) * (y - y1) / (y2 - y1) + x1: ins = not ins
    return ins
def as_core(g):  # -> (list of segments as point pairs, radius, polygon or None)
    if g[0] == "circle": return [(g[1], g[1])], g[2], None
    if g[0] == "cap": return [(g[1], g[2])], g[3], None
    poly = g[1]; return list(zip(poly, poly[1:] + poly[:1])), 0.0, poly
def dist(g1, g2):
    s1, r1, p1 = as_core(g1); s2, r2, p2 = as_core(g2)
    d = min(seg_seg(a, b, c, e) for (a, b) in s1 for (c, e) in s2)
    if p1 and any(in_poly(c, p1) for seg in s2 for c in seg): d = 0
    if p2 and any(in_poly(c, p2) for seg in s1 for c in seg): d = 0
    return d - r1 - r2

# connectivity + clearance
parent = list(range(len(items)))
def find(i):
    while parent[i] != i: parent[i] = parent[parent[i]]; i = parent[i]
    return i
min_clr = (9, None)
for i, j in itertools.combinations(range(len(items)), 2):
    A, B = items[i], items[j]
    if not (A["layers"] & B["layers"]): continue
    d = dist(A["geom"], B["geom"])
    if d <= 1e-6:
        if A["net"] != B["net"]:
            bad(f"SHORT {A['ref']} [{A['net']}] <-> {B['ref']} [{B['net']}]")
        parent[find(i)] = find(j)
    elif A["net"] != B["net"] and d < min_clr[0]:
        min_clr = (d, f"{A['ref']} <-> {B['ref']}")
print(f"min copper clearance between different nets: {min_clr[0]:.3f} mm ({min_clr[1]})")
if min_clr[0] < 0.2: bad("clearance below 0.2 mm")

# hole-to-copper (drills vs other-net copper on any layer) and hole-to-hole
holes = [(it["center"], it.get("drill", 0.3) / 2, it) for it in items if it["kind"] in ("via",) or "drill" in it]
for (c, r, it) in holes:
    for o in items:
        if o is it or o["net"] == it["net"]: continue
        d = dist(("circle", c, r), o["geom"])
        if d < 0.25: bad(f"hole {it['ref']} to {o['ref']} {d:.3f}")

comp = defaultdict(set)
for i, it in enumerate(items):
    if it["kind"] == "pad" and it["net"]: comp[it["net"]].add(find(i))
for net, cs in sorted(comp.items()):
    status = "OK" if len(cs) == 1 else f"SPLIT into {len(cs)}"
    print(f"  net {net:14s} pads: {sorted(p for p, it in pads.items() if it['net'] == net)}  -> {status}")
    if len(cs) != 1: bad(f"net {net} not fully routed")

# dangling track ends: each segment endpoint must be inside a pad/via of same net or coincide with another segment end/body
segs = [it for it in items if it["kind"] == "seg"]
for s in segs:
    for e in (s["geom"][1], s["geom"][2]):
        ok = False
        for o in items:
            if o is s or o["net"] != s["net"] or not (o["layers"] & s["layers"]): continue
            if o["kind"] == "seg":
                if min(math.hypot(e[0] - q[0], e[1] - q[1]) for q in (o["geom"][1], o["geom"][2])) < 1e-6: ok = True
            elif dist(("circle", e, 0), o["geom"]) <= 1e-6: ok = True
            if ok: break
        if not ok: bad(f"dangling end {e} of {s['ref']}")

# board edge
def P2(n, k): c = kid(n, k); return (float(c[1]), float(c[2]))
edge = []
for gl in kids(pcb, "gr_line"):
    if kid(gl, "layer")[1] == "Edge.Cuts": edge.append((P2(gl, "start"), P2(gl, "end")))
for ga in kids(pcb, "gr_arc"):
    if kid(ga, "layer")[1] != "Edge.Cuts": continue
    p1, p2, p3 = P2(ga, "start"), P2(ga, "mid"), P2(ga, "end")
    ax_, ay_ = p1; bx_, by_ = p2; cx_, cy_ = p3
    d = 2 * (ax_ * (by_ - cy_) + bx_ * (cy_ - ay_) + cx_ * (ay_ - by_))
    ux = ((ax_**2 + ay_**2) * (by_ - cy_) + (bx_**2 + by_**2) * (cy_ - ay_) + (cx_**2 + cy_**2) * (ay_ - by_)) / d
    uy = ((ax_**2 + ay_**2) * (cx_ - bx_) + (bx_**2 + by_**2) * (ax_ - cx_) + (cx_**2 + cy_**2) * (bx_ - ax_)) / d
    r_ = math.hypot(ax_ - ux, ay_ - uy)
    a0 = math.atan2(ay_ - uy, ax_ - ux); am = math.atan2(by_ - uy, bx_ - ux); a1 = math.atan2(cy_ - uy, cx_ - ux)
    sw = (a1 - a0) % (2 * math.pi)
    if not ((am - a0) % (2 * math.pi) < sw): sw -= 2 * math.pi
    pts_ = [(ux + r_ * math.cos(a0 + sw * t / 16), uy + r_ * math.sin(a0 + sw * t / 16)) for t in range(17)]
    edge += list(zip(pts_[:-1], pts_[1:]))
    print(f"  corner arc radius {r_:.2f} mm")
# closed-outline check: every endpoint shared by exactly two segments
from collections import Counter
cnt = Counter(key(*p) if False else (round(p[0], 3), round(p[1], 3)) for sgm in edge for p in sgm)
if any(c != 2 for c in cnt.values()): bad("board outline is not a closed loop")
xs = [p[0] for sgm in edge for p in sgm]; ys = [p[1] for sgm in edge for p in sgm]
x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
print(f"board outline {x1-x0:.2f} x {y1-y0:.2f} mm, closed loop of {len(edge)} segments")
me = min((dist(it["geom"], ("cap", a, b, 0)), it["ref"]) for it in items for (a, b) in edge)
print(f"min copper-to-edge: {me[0]:.3f} mm ({me[1]})")
if me[0] < 0.5: bad("edge clearance < 0.5")

# silk text vs exposed pads (rough bbox, KiCad stroke font ~0.9*size advance per char)
def text_box(t, x, y, sz, ang=0):
    w = len(t) * sz * 0.92; h = sz
    if round(ang) % 180 == 90: w, h = h, w
    return [(x - w / 2, y - h / 2), (x + w / 2, y - h / 2), (x + w / 2, y + h / 2), (x - w / 2, y + h / 2)]
silk = []
for gt in kids(pcb, "gr_text"):
    at = kid(gt, "at"); lay = kid(gt, "layer")[1]; sz = float(kid(kid(kid(gt, "effects"), "font"), "size")[1])
    th = float(kid(kid(kid(gt, "effects"), "font"), "thickness")[1])
    if sz < 0.8 - 1e-9 or th < 0.127: bad(f"silk '{gt[1]}' too small: {sz} / {th}")
    silk.append((gt[1], lay, text_box(gt[1], float(at[1]), float(at[2]), sz)))
for fp in kids(pcb, "footprint"):
    at = kid(fp, "at"); fx, fy = float(at[1]), float(at[2]); fa = float(at[3]) if len(at) > 3 else 0
    for t in kids(fp, "fp_text"):
        if kid(t, "layer")[1] != "F.SilkS": continue
        ta = kid(t, "at"); dx, dy = rot(float(ta[1]), float(ta[2]), fa)
        tang = float(ta[3]) if len(ta) > 3 else 0
        sz = float(kid(kid(kid(t, "effects"), "font"), "size")[1])
        th = float(kid(kid(kid(t, "effects"), "font"), "thickness")[1])
        if sz < 0.8 - 1e-9 or th < 0.127: bad(f"silk '{t[2]}' too small: {sz} / {th}")
        silk.append((t[2], "F.SilkS", text_box(t[2], fx + dx, fy + dy, sz, tang)))
for fp in kids(pcb, "footprint"):
    at = kid(fp, "at"); fx, fy = float(at[1]), float(at[2]); fa = float(at[3]) if len(at) > 3 else 0
    for pl in kids(fp, "fp_poly"):
        if kid(pl, "layer")[1] != "F.SilkS": continue
        pts = [rot(float(p[1]), float(p[2]), fa) for p in kid(pl, "pts")[1:]]
        poly = [(fx + x, fy + y) for x, y in pts]
        for it in items:
            if it["kind"] in ("pad", "via") and "F.Cu" in it["layers"] and dist(("poly", poly), it["geom"]) < 0.1:
                bad(f"silk mark near {it['ref']}")
for (t, lay, box) in silk:
    side = "F.Cu" if lay.startswith("F") else "B.Cu"
    if not (x0 + 0.2 < min(p[0] for p in box) and max(p[0] for p in box) < x1 - 0.2 and y0 + 0.1 < min(p[1] for p in box) and max(p[1] for p in box) < y1 - 0.1):
        bad(f"silk '{t}' runs off board")
    for it in items:
        if it["kind"] in ("pad", "via") and side in it["layers"]:
            d = dist(("poly", box), it["geom"])
            if d < 0.1: bad(f"silk '{t}' ({lay}) overlaps pad {it['ref']} ({d:.2f})")

for (t1, l1, b1), (t2, l2, b2) in itertools.combinations(silk, 2):
    if l1 == l2 and dist(("poly", b1), ("poly", b2)) < 0.05: bad(f"silk overlap '{t1}' / '{t2}'")
for (ref, c, dr) in npth:
    de = min(pt_seg(c, a, b) for a, b in edge) - dr / 2
    dc = min(dist(("circle", c, 0), it["geom"]) for it in items)
    ds = min(dist(("circle", c, 0), ("poly", box)) for (_, _, box) in silk)
    print(f"  {ref}: {dr} mm NPTH at ({c[0]-x0:.2f}, {c[1]-y0:.2f}); hole edge to board edge {de:.2f}, nearest copper {dc:.2f}, nearest silk text {ds:.2f} (from centre)")
    if de < 0.5: bad(f"{ref} too close to edge")
    if dc < 3.0: bad(f"{ref}: copper inside 3 mm keepout")
    if ds < 3.0: bad(f"{ref}: silk text inside 3 mm keepout")
if len(npth) != 4: bad(f"expected 4 mounting holes, found {len(npth)}")
tht = [r for r, it in pads.items() if "drill" in it]
print(f"through-hole pads: {tht or 'none'} (bottom side has only vias)")
if tht: bad("through-hole pads present")
print(f"silk texts checked: {len(silk)}")
pcb_nets = {r: it["net"] for r, it in pads.items()}

# ------------------------------------------------------------------ SCHEMATIC
sch = parse(open(f"{D}/{P}.kicad_sch").read())
libs = {}
for s in kid(sch, "lib_symbols")[1:]:
    pins = []
    def walk(n):
        for c in n:
            if isinstance(c, list):
                if c and c[0] == "pin":
                    at = kid(c, "at"); pins.append((kid(c, "number")[1], float(at[1]), float(at[2]), kid(c, "name")[1], c[1]))
                else: walk(c)
    walk(s)
    libs[s[1]] = dict(pins=pins, power=any(c == ["power"] for c in s if isinstance(c, list)))

def lrot(x, y, deg):  # CCW in y-up lib space
    t = math.radians(deg); return (x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t))

def key(x, y): return (round(x, 3), round(y, 3))
nodes = defaultdict(list)  # point -> list of ('pin', ref, num) ...
pin_pts = {}
sym_info = {}
for s in kids(sch, "symbol"):
    lid = kid(s, "lib_id")[1]; at = kid(s, "at"); x, y, a = float(at[1]), float(at[2]), float(at[3])
    ref = [p for p in kids(s, "property") if p[1] == "Reference"][0][2]
    val = [p for p in kids(s, "property") if p[1] == "Value"][0][2]
    fpp = [p for p in kids(s, "property") if p[1] == "Footprint"][0][2]
    sym_info[ref] = (lid, val, fpp, kid(s, "dnp")[1])
    for (num, px, py, name, ptype) in libs[lid]["pins"]:
        rx, ry = lrot(px, py, a); P_ = key(x + rx, y - ry)
        pin_pts[(ref, num)] = P_
        nodes[P_].append(("pin", ref, num, name if libs[lid]["power"] and lid != "power:PWR_FLAG" else None, ptype))
wires = []
for w in kids(sch, "wire"):
    pts = kid(w, "pts"); a = key(float(pts[1][1]), float(pts[1][2])); b = key(float(pts[2][1]), float(pts[2][2]))
    wires.append((a, b))
juncs = {key(float(kid(j, "at")[1]), float(kid(j, "at")[2])) for j in kids(sch, "junction")}
labels = [(l[1], key(float(kid(l, "at")[1]), float(kid(l, "at")[2]))) for l in kids(sch, "label")]

par = {}
def F_(x):
    par.setdefault(x, x)
    while par[x] != x: par[x] = par[par[x]]; x = par[x]
    return x
def Un(a, b): par[F_(a)] = F_(b)
def on_wire(p, a, b):
    return pt_seg(p, a, b) < 1e-6
for (a, b) in wires:
    Un(("pt", a), ("pt", b))
# endpoint-to-endpoint and endpoint/pin on wire interior
allpts = set(nodes) | {p for w in wires for p in w}
for p in allpts:
    for (a, b) in wires:
        if p in (a, b): Un(("pt", p), ("pt", a)); continue
        if on_wire(p, a, b):
            if p in juncs or p in nodes:
                Un(("pt", p), ("pt", a))
                if p not in juncs: print(f"  note: pin at {p} lands on wire interior without junction")
            else:
                bad(f"wire end {p} touches wire interior without junction")
for p, lst in nodes.items():
    for it in lst:
        Un(("pin", it[1], it[2]), ("pt", p))
        if it[3]: Un(("pin", it[1], it[2]), ("net", it[3]))
for (name, p) in labels:
    hit = [w for w in wires if on_wire(p, *w)]
    if not hit and p not in nodes: bad(f"label {name} at {p} not on a wire/pin")
    for w in hit: Un(("pt", p), ("pt", w[0]))
    Un(("pt", p), ("net", name))
# junction sanity: each junction should have >=3 connections
for j in juncs:
    n = sum(1 for (a, b) in wires if j in (a, b)) + 2 * sum(1 for (a, b) in wires if on_wire(j, a, b) and j not in (a, b)) + len(nodes.get(j, []))
    if n < 3: bad(f"junction {j} has only {n} connections")
# dangling wire ends
for (a, b) in wires:
    for p in (a, b):
        cnt = sum(1 for w in wires if p in w) - 1 + len(nodes.get(p, [])) + sum(1 for w in wires if p not in w and on_wire(p, *w)) + sum(1 for (_, lp) in labels if lp == p)
        if cnt == 0: bad(f"dangling wire end {p}")

groups = defaultdict(set)
for k in list(par):
    groups[F_(k)].add(k)
sch_nets = {}
for g, members in groups.items():
    names = sorted({m[1] for m in members if m[0] == "net"})
    pins_ = [m for m in members if m[0] == "pin"]
    if len(names) > 1: bad(f"multiple names on one net: {names}")
    nm = names[0] if names else None
    for m in pins_:
        sch_nets[(m[1], m[2])] = nm
# unconnected component pins
for (ref, num), nm in sch_nets.items():
    if ref.startswith("#"): continue
    if nm is None:
        bad(f"schematic pin {ref}.{num} has no named net")
# compare with PCB
print("\nschematic vs PCB pad nets:")
mism = 0
for (ref, num), nm in sorted(sch_nets.items()):
    if ref.startswith("#"): continue
    pn = pcb_nets.get(f"{ref}.{num}", "<no pad>")
    if pn != nm:
        mism += 1; bad(f"{ref}.{num}: sch {nm} vs pcb {pn}")
for r in pcb_nets:
    ref, num = r.split(".")
    if (ref, num) not in sch_nets and not num.startswith("MP") and num != "": bad(f"pcb pad {r} not in schematic")
print(f"  {len([k for k in sch_nets if not k[0].startswith('#')])} pins compared, {mism} mismatches")
# footprint ids match
for fp in kids(pcb, "footprint"):
    ref = [c for c in kids(fp, "fp_text") if c[1] == "reference"][0][2]
    if sym_info[ref][2] != fp[1]: bad(f"{ref} footprint sch {sym_info[ref][2]} vs pcb {fp[1]}")
    val = [c for c in kids(fp, "fp_text") if c[1] == "value"][0][2]
    if sym_info[ref][1] != val: bad(f"{ref} value sch {sym_info[ref][1]} vs pcb {val}")
    path = kid(fp, "path")[1]
    suuid = [kid(s, "uuid")[1] for s in kids(sch, "symbol") if [p for p in kids(s, "property") if p[1] == "Reference"][0][2] == ref][0]
    if path != "/" + suuid: bad(f"{ref} path mismatch")

# other files parse
for fn in (f"{P}.kicad_sym", "sym-lib-table"):
    parse(open(f"{D}/{fn}").read())
import json; json.load(open(f"{D}/{P}.kicad_pro"))
print("\nall files parse.")
print(f"\n{len(problems)} problem(s)")
