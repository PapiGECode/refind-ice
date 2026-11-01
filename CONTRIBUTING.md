# Contributing

Issues and pull requests are welcome. For visual problems, include your rEFInd version, firmware resolution, number/order of visible OS entries and tools, and a screenshot with personal details removed. Never upload EFI keys, BCD stores, recovery keys or private disk images.

The renderer is `source/render.py`; presets are in `presets/`. Use a new output directory and compare all selection states. The brightness masks depend on exact layout geometry; a change to entry counts or resolution needs regenerated artwork. Do not claim physical compatibility based solely on a preview.

Keep source, documentation and font attribution together. Distribution checksums cover exact bytes; refresh them when preparing a new release. Use an issue to discuss substantial layout changes before implementation.
