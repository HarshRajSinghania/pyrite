# Getting Started with Pyrite

Pyrite is a Knowledge-as-Code platform. You keep structured knowledge in markdown files with YAML frontmatter, validated against schemas, versioned in git, and searchable by any AI through MCP. This tutorial walks you from zero to a working knowledge base in about five minutes.

## Install Pyrite

```bash
# Install (no PyPI wheel yet -- from source). Needs Python 3.11+.
git clone https://github.com/pyrite-wiki/pyrite.git && cd pyrite
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[all]"
```

# Initialize a knowledge base outside the clone
pyrite init --template research --path ~/my-kb

# Create some entries
pyrite create -k my-kb --type person --title "Sarah Chen" \
  --body "Engineering lead. Considering move to consulting." --tags "team,engineering"

pyrite create -k my-kb --type note --title "Switch to async standups" \
  --body "Decided 2026-03-01. Reduces meeting load by 3hrs/week." --tags "process"

# Search (keyword, semantic, or hybrid)
pyrite search "consulting" -k my-kb
pyrite search "career transition" -k my-kb --mode=semantic  # keyword mode finds exact words only
# The first semantic search downloads the embedding model (~90 MB, one time).
# Writes never wait on that download: an entry is keyword-searchable the
# moment it is written, and gets its embedding on the next `pyrite index`
```

See the full [getting-started guide](docs/getting-started.md) for more.

## Use Templates for Domain-Specific KBs

The templates `pyrite init` accepts are the six listed above. Each works with nothing extra installed:

```bash
cd ..
pyrite init --template software --path my-project
```

The **software** template adds ADRs, components, backlog items, standards, and runbooks — everything you need to manage a software project's knowledge. Its `pyrite sw` commands (`sw adrs`, `sw backlog`, ...) come from the software-kb extension, which is a separate install: `pip install -e extensions/software-kb`. See the [software-kb README](../extensions/software-kb/README.md) for the backlog lifecycle, dependencies (`blocked_by` / `blocks`), and command reference. Extensions are never installed by a template; the [README](../README.md#install) lists them.

The `zettelkasten` template gives note-maturity types; the extension behind it is an example plugin, showing how a Pyrite plugin adds entry types, CLI commands, MCP tools and a preset, not a supported product.

## Launch the Web UI

Pyrite ships an optional web interface for browsing, editing, and visualizing your knowledge base. It is built from the `web/` directory of your clone, so from the repository root, once:

```bash
cd web && npm install && npm run build
```

Then, with the `server` extra (included in `[all]`):

```bash
pyrite serve
```

Open http://localhost:8000.

## Next steps

- [Concepts](concepts.md)
- [CLI reference](cli.md)
- [MCP](mcp.md)
- [Awesome Plugins](plugins.md) — community extensions
- [Upgrading](upgrading.md) — what changes between releases and what to run (links [pinning entry ids](pinning-entry-ids.md))
- [Gemini MCP Integration](gemini-mcp-integration.md) — connect Pyrite to Gemini
- [OpenAI MCP Integration](openai-mcp-integration.md) — connect Pyrite to OpenAI-compatible clients
- [Docker Deployment](../README.md#deploy) — deploy for teams with Railway, Render, Fly.io, or self-hosted
