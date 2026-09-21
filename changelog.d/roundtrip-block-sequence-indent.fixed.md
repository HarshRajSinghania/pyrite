- **A no-op load and save keeps each document's block-sequence indentation
  (#148).** A `links:` block written with its items indented under the key
  (`sequence=4, offset=2`) came back flush with the key, because the single
  shared `YAML()` in `pyrite/utils/yaml.py` never set an indent and ruamel's
  default is `sequence=2, offset=0` -- so a load-and-save with no edit rewrote
  the file. The dumper now reads the numbers out of the parsed tree's own
  line/column records, per document, so nothing is reformatted that was not
  already written that way: hand-written files keep their style, files pyrite
  wrote keep theirs, and new content is emitted exactly as before. A document
  that mixes both styles in one file cannot be reproduced -- the emitter takes
  one setting per document -- and a test says so rather than leaving it
  unsaid.
