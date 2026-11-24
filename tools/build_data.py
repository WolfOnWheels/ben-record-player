"""Builds assets/data.js from the record PDF glyphs (glyphs.json from parse_pdf.py) and the iTunes Lookup API.

The spiral on the BEN13 record is 17 artist names (separated by a middle dot) repeated 13 times.
Each name instance becomes an SVG <g class="n aK"> so the page can highlight it, and every
letter's centre goes into a hit table so the needle can find the name under it.
"""
import json, math, re, sys, urllib.request

glyphs_path = sys.argv[1]
out_path = sys.argv[2]

G = json.load(open(glyphs_path))
CX, CY = 296.63, 415.13          # record centre (spindle) in PDF points, y down
LABEL_R = 91.42                   # yellow label radius
N_SPIRAL = 2015                   # glyphs 0..2014 are the spiral, the rest is the label
SEP = None                        # separator cluster is detected by size below

ARTISTS = ["A Tribe Called Quest", "N.W.A", "De La Soul", "OutKast", "Kendrick Lamar",
           "Tyler, The Creator", "Doechii", "Central Cee", "Feng", "Drake", "Bad Bunny",
           "Asap Rocky", "Don Toliver", "Eminem", "Dr. Dre", "Jay-Z", "NF"]
# glyphs per name, in the order the names run along the spiral (from the centre outwards)
LENS = [17, 5, 8, 7, 13, 16, 7, 10, 4, 5, 8, 9, 10, 6, 6, 5, 2]

# iTunes track ids: the best-known song per artist (clean edit where Apple has one)
TRACKS = [1806751241, 1478946359, 1657705243, 1774799818, 1781353929, 1254572572, 1800308810,
          1749412138, 1871646384, 1406109863, 1787023936, 1388566993, 1502319171, 1440903439,
          1444156738, 1440932018, 1440849363]

def rel(d):
    nums = re.findall(r'-?\d+(?:\.\d+)?', d)
    out, k = [], 0
    def sub(m):
        nonlocal k
        v = float(m.group(0)) - (CX if k % 2 == 0 else CY)
        k += 1
        s = f"{v:.1f}"
        return s[:-2] if s.endswith('.0') else s
    return re.sub(r'-?\d+(?:\.\d+)?', sub, d)

# --- assign every spiral glyph to (artist, instance) -------------------------------
period = sum(LENS) + len(LENS)
assign = []          # per glyph: (artist, instance) or None for separators
inst = 0
i = 0
while i < N_SPIRAL:
    for a, n in enumerate(LENS):
        for _ in range(n):
            if i < N_SPIRAL:
                assign.append((a, inst))
                i += 1
        inst += 1
        if i < N_SPIRAL:
            assign.append(None)  # separator dot
            i += 1
assert len(assign) == N_SPIRAL
# sanity: separators should all be tiny
for g, a in zip(G[:N_SPIRAL], assign):
    if a is None:
        assert g['w'] < 3.2 and g['h'] < 3.2, g

# --- SVG ---------------------------------------------------------------------------
inst_paths = {}
seps = []
for g, a in zip(G[:N_SPIRAL], assign):
    if a is None:
        seps.append(rel(g['d']))
    else:
        inst_paths.setdefault(a[1], [a[0], []])[1].append(rel(g['d']))

COLORS = {(0.6, 0.4, 0.3, 1.0): '#0b0d10', (0.0, 0.1, 0.75, 0.0): '#f8dd75',
          (0.75, 0.679, 0.671, 0.901): '#111', (0.0, 0.0, 0.0, 0.0): '#fff'}
# The spiral's outer edge isn't round (it swings ~266–294pt), which reads as a wobble when the
# record spins. Clip the names to the largest circle the text reaches at every angle.
env = [0.0] * 360
for g in G[:N_SPIRAL]:
    nums = [float(v) for v in re.findall(r'-?\d+(?:\.\d+)?', g['d'])]
    for x, y in zip(nums[0::2], nums[1::2]):
        dx, dy = x - CX, y - CY
        b = int((math.degrees(math.atan2(dy, dx)) + 360) % 360)
        env[b] = max(env[b], math.hypot(dx, dy))
CROP_R = round(min(env), 1)

parts = [f'<defs><clipPath id="disc"><circle r="{CROP_R}"/></clipPath></defs>'
         '<g class="spiral" clip-path="url(#disc)">']
for k in sorted(inst_paths):
    a, ds = inst_paths[k]
    parts.append(f'<path class="n a{a}" data-i="{k}" d="{"".join(ds)}"/>')
parts.append(f'<path class="sep" d="{"".join(seps)}"/></g><g class="label">')
for g in G[N_SPIRAL:]:
    # a few shapes sit off the artboard (clipped in the PDF) — skip anything outside the label
    if math.hypot(g['cx'] - CX, g['cy'] - CY) > LABEL_R:
        continue
    parts.append(f'<path fill="{COLORS[tuple(g["color"])]}" d="{rel(g["d"])}"/>')
parts.append('</g>')
svg_inner = ''.join(parts)

# --- hit table: centre of every letter that is not hidden under the label ------------
hits = []
for g, a in zip(G[:N_SPIRAL], assign):
    if a is None:
        continue
    x, y = g['cx'] - CX, g['cy'] - CY
    r = math.hypot(x, y)
    if r < LABEL_R + 2 or r > CROP_R - 1:      # under the label, or mostly cropped away
        continue
    hits += [round(x, 1), round(y, 1), a[0], a[1]]
outer = CROP_R

# --- songs ---------------------------------------------------------------------------
url = 'https://itunes.apple.com/lookup?country=US&id=' + ','.join(map(str, TRACKS))
res = {r['trackId']: r for r in json.load(urllib.request.urlopen(url))['results']}
songs = []
for a, tid in enumerate(TRACKS):
    r = res[tid]
    songs.append({'artist': ARTISTS[a], 'track': r['trackName'], 'id': tid,
                  'preview': r['previewUrl'], 'link': r['trackViewUrl'].split('?')[0],
                  'art': r['artworkUrl100'].replace('100x100', '300x300')})

data = {'artists': ARTISTS, 'songs': songs, 'labelR': LABEL_R, 'outerR': round(outer, 1),
        'instances': len(inst_paths), 'hits': hits, 'svg': svg_inner}
with open(out_path, 'w') as f:
    f.write('window.RECORD_DATA = ' + json.dumps(data, separators=(',', ':')) + ';\n')
print('instances', len(inst_paths), 'hit letters', len(hits) // 4, 'outerR', round(outer, 1),
      'svg KB', len(svg_inner) // 1024)
for s in songs:
    print(f"  {s['artist']:22} {s['track']}")
