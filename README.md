# ParaDogma -- Hierarchical AI

Multi-agent platform built on the DOGMA stack (Compressor, Transport, Skill Library).

## Architecture

```
                  +------------+
                  | Controller |
                  +-----+------+
                        |
                  +-----v------+
                  |   Planner  |     decomposes tasks, assigns to workers
                  +--+---+---+-+
                     |   |   |
              +------+   |   +------+
              |          |          |
         +----v---+ +----v----+ +--v----+
         | Coder  | | Reviewer| | Tester|
         +--------+ +---------+ +-------+
```

Every agent inherits from `HierarchicalAgent` which integrates:

* **DogmaCompressor** -- semantic compression of inter-agent messages
* **DogmaNode** -- transport layer for packet routing
* **SkillLibrary** -- persistent skill/experience store

## Quick start

```bash
# Run the demo
python -m hierarchical.demo

# Run tests
python -m pytest tests/ -v
```

## Project layout

```
hierarchical/
  __init__.py      package exports
  node.py          HierarchicalAgent base class + DOGMA components
  planner.py       Planner agent (decompose / assign / aggregate)
  worker.py        Coder, Reviewer, Tester agents
  controller.py    Controller (queue, routing, logging)
  demo.py          end-to-end demo script
tests/
  test_hierarchical.py   unit + integration tests
```

## License

MIT
