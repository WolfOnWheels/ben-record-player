# B.E.N. Record Player

A playable turntable built from the "B.E.N. – 13 Years of Life" T-shirt design. The record's
grooves are made of artist names. Drop the tonearm on a name to hear a 30-second Apple Music
preview by that artist.

- Drag the tonearm onto the record; every copy of the playing artist's name lights up.
- Grab the record to scratch (it plays backwards too).
- Start • Stop switches the motor; the music slows down and speeds up with the platter.

## Files

| Path | What it is |
|---|---|
| `index.html` | The whole player (HTML, CSS and JavaScript) |
| `assets/deck.png`, `assets/arm.png` | Top-view turntable and tonearm artwork |
| `assets/data.js` | Generated: record artwork as SVG, letter positions for hit-testing, song list |
| `tools/` | Scripts that generated `data.js` from the Illustrator PDF |

## Changing a song

Edit the iTunes track id in `tools/build_data.py` (`TRACKS`, same order as `ARTISTS`) and rebuild:

```bash
python3 tools/parse_pdf.py          # reads the PDF's decompressed page content (content.txt) → glyphs.json
python3 tools/build_data.py glyphs.json assets/data.js
```

`build_data.py` also refreshes the preview URLs from the iTunes Lookup API.

Previews and cover art stream from Apple; the page needs HTTPS to play audio.
