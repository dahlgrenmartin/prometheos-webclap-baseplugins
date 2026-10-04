# PrometheOS WebCLAP base plugins

A collection of permissively licensed third-party WebCLAP (WCLAP) plugins,
packaged for installation in buzz-remote. Each release has one
`.wclap.tar.gz` per upstream plugin bundle and a `SHA256SUMS`.

Install them in buzz-remote through **Machines → Plugins… → Install File…**.
You can select several archives at once.

| Archive | Plugins | Kind | License | Project |
| --- | --- | --- | --- | --- |
| `MNO.wclap.tar.gz` | MNO | Instrument (mono synth) | ISC | [charCulbert/mno](https://github.com/charCulbert/mno) |
| `Tapa.wclap.tar.gz` | Tapa | Instrument (percussion) | ISC | [charCulbert/Tapa](https://github.com/charCulbert/Tapa) |
| `Mote.wclap.tar.gz` | Mote | Note effect (arpeggiator) | ISC | [charCulbert/Mote](https://github.com/charCulbert/Mote) |
| `Slide.wclap.tar.gz` | Slide | Effect (stereo delay) | ISC | [charCulbert/Slide](https://github.com/charCulbert/Slide) |
| `ClapSawDemo.wclap.tar.gz` | Clap Saw Demo (ImGui) | Instrument | MIT | [surge-synthesizer/clap-saw-demo](https://github.com/surge-synthesizer/clap-saw-demo) |
| `SignalsmithBasics.wclap.tar.gz` | Chorus, Crunch, Frequency Shifter, Limiter, Reverb, Analyser | Effects | MIT | [Signalsmith-Audio/basics](https://github.com/Signalsmith-Audio/basics) |
| `SignalsmithClapExamples.wclap.tar.gz` | Example chorus, note plugin, virtual keyboard, synth | Effect, note effects, instrument | BSL-1.0 | [geraintluff/signalsmith-clap-cpp](https://github.com/geraintluff/signalsmith-clap-cpp) |
| `ClackGain.wclap.tar.gz` | Clack Gain | Effect | MIT OR Apache-2.0 | [prokopyl/clack](https://github.com/prokopyl/clack) |
| `ClackPolySynth.wclap.tar.gz` | Clack PolySynth | Instrument | MIT OR Apache-2.0 | [prokopyl/clack](https://github.com/prokopyl/clack) |
| `AsClapExample.wclap.tar.gz` | Gain, Synth (AssemblyScript) | Effect, instrument | BSL-1.0 | [WebCLAP/as-clap](https://github.com/WebCLAP/as-clap) |

That is 10 archives and 19 plugins. Every plugin keeps its authors' license;
this repository's own [MIT license](LICENSE) covers only its scripts and
documentation.

## Where the binaries come from

Nothing is rebuilt here. [`plugins.json`](plugins.json) pins each archive to
an upstream commit and a SHA-256:

- [charCulbert/char-wclaps](https://github.com/charCulbert/char-wclaps): MNO, Tapa, Mote, Slide, Clap Saw Demo.
- [WebCLAP/examples](https://github.com/WebCLAP/examples): Signalsmith, Clack and as-clap.

`python scripts/package.py --check` fetches each pinned file, verifies its
hash and writes `dist/`.

- **Upstream archives that already include their licenses** are published
  byte-for-byte; only the file name may differ.
- **Archives without license files, and bare `.wasm` modules**, are repacked
  deterministically with the upstream license files and a `PROVENANCE.txt`.
  Their plugin files are unchanged.

Two consecutive builds must produce identical `SHA256SUMS`; CI checks this and
publishes the release for a `v*` tag.

## Verification

Each release archive was installed and rendered with buzz-remote's
`reference.compat.test.ts` (`WEBCLAP_REFERENCE_DIR=dist`). All 19 plugins
loaded and produced finite audio, or notes for the note effects, and served
their declared editor pages. Their output matched the upstream originals.

## Not included

**Pro54** (in char-wclaps) is excluded. Its DSP is compiled from Cmajor
Software Ltd's Pro54 example patch, licensed GPLv3 or commercially, but the
archive is labelled ISC only. It can be added once its licensing is clarified.
