<div align="center">

![Forktober GIF](https://raw.githubusercontent.com/ACM-VIT/.github/master/profile/acm_gif_banner.gif)

<!-- Project Title -->
<h2>Scrag</h2>

<p>Adaptive, multi‑strategy web scraper that extracts clean text and metadata for RAG pipelines and local LLM workflows.</p>

<p>
  <a href="https://acmvit.in/" target="_blank">
    <img alt="made-by-acm" src="https://img.shields.io/badge/MADE%20BY-ACM%20VIT-orange?style=flat-square&logo=acm&link=acmvit.in" />
  </a>
  <img alt="license" src="https://img.shields.io/badge/License-MIT-green.svg?style=flat-square" />
</p>

</div>

---

## Table of Contents
- [About](#about)
- [Features](#features)
- [Project Structure](#project-structure)
- [Roadmap](#roadmap)
- [Quick Start](#quick-start)
- [Usage](#usage)
- [Contributing](#contributing)
- [Hacktoberfest](#hacktoberfest)
- [Submitting a Pull Request](#submitting-a-pull-request)
- [Guidelines for Pull Request](#guidelines-for-pull-request)
- [Authors](#authors)

---

## About
This project proposes a robust web scraper designed for maximum adaptability. It automatically adjusts to various website structures by employing a multi‑strategy extraction approach. The scraper attempts to extract clean, structured text and metadata (including title, author, and date) using methods such as newspaper3k, readability‑lxml, and BeautifulSoup heuristics. In cases where these methods are insufficient, it can optionally fall back to headless browser rendering to capture content from more complex, dynamically loaded websites. The output is specifically formatted for integration into Retrieval‑Augmented Generation (RAG) pipelines or for use with local Large Language Models (LLMs).

An ambitious, optional extension to this project is the Universal RAG Builder. This layer would automatically identify and scrape top‑ranked websites relevant to a user's query, subsequently building a RAG index from the collected data. This feature addresses a key limitation of local LLMs, their inability to browse the internet by providing automated knowledge aggregation and up‑to‑date information retrieval without requiring manual data collection. The project's user interface will initially be a Command Line Interface (CLI), with plans for a web‑based version to cater to users who prefer a more visually appealing display.

---

## Features
- **Multi‑strategy extraction**: newspaper3k, readability‑lxml, and BeautifulSoup‑based heuristics  
- **JavaScript support**: Optional Selenium and Playwright extractors for dynamic content ⚡  
- **Metadata capture**: title, author, and date when available  
- **RAG pipeline integration**: Complete embedding, indexing, and retrieval system 🧠  
- **Flexible configuration**: YAML-based configuration with environment support  
- **CLI first**: Simple commands to extract, process, and query content  
- **Graceful fallbacks**: Automatic fallback between extraction strategies  
- **Performance optimized**: Async extraction and configurable timeouts  

### Web Rendering Capabilities

For JavaScript-heavy pages that require browser automation:

```bash
# Install with web rendering support
pip install 'scrag[web-render]'

# Extract from single-page applications
scrag extract https://spa-example.com --selenium --browser chrome

# Use Playwright for modern web apps
scrag extract https://dynamic-site.com --playwright --browser chromium

# List available extractors
scrag extractors
```

**Supported browsers:**
- **Selenium**: Chrome, Firefox  
- **Playwright**: Chromium, Firefox, WebKit  

> ⚠️ **Note**: Web rendering extractors have a heavy footprint and are not recommended for CI environments. See [Web Rendering Guide](docs/guides/web-rendering-extractors.md) for details.  

---

## Project Structure

```
scrag/
├── src/scrag/                 # Main source code
│   ├── extractors/           # Content extraction strategies
│   ├── processors/           # Text processing and cleaning
│   ├── storage/              # Storage backends and adapters
│   ├── rag/                  # RAG pipeline components
│   ├── cli/                  # Command-line interface
│   ├── web/                  # Web interface
│   └── utils/                # Utility functions
├── tests/                    # Comprehensive test suite
│   ├── unit/                 # Unit tests
│   ├── integration/          # Integration tests
│   ├── performance/          # Performance benchmarks
│   └── fixtures/             # Test data and mocks
├── docs/                     # Documentation
│   ├── api/                  # API reference
│   ├── guides/               # User guides
│   └── tutorials/            # Step-by-step tutorials
├── research/                 # Research & architectural decisions
│   ├── spikes/               # Discovery and research spikes
│   ├── decisions/            # Architecture Decision Records (ADRs)
│   └── epics/                # Epic planning and documentation
├── config/                   # Configuration files
│   ├── extractors/           # Extractor configurations
│   └── rag/                  # RAG pipeline configurations
├── deployment/               # Deployment configurations
│   ├── docker/               # Docker configurations
│   ├── kubernetes/           # Kubernetes manifests
│   └── aws/                  # AWS deployment files
├── scripts/                  # Development and build scripts
└── ARCHITECTURE.md           # Detailed architecture documentation
```

For detailed architecture information, see [ARCHITECTURE.md](ARCHITECTURE.md).

---

## Roadmap
- Universal RAG Builder: auto‑discover top results for a query, scrape them, and build a ready‑to‑use RAG index.  
- Web UI: a lightweight interface for users who prefer a visual workflow.  
- Export adapters: convenient formats for popular vector DBs and RAG frameworks.  

### Current Release (v1.0)
-  Multi-strategy extraction: newspaper3k, readability-lxml, and BeautifulSoup-based heuristics
-  Metadata capture: title, author, and date when available
-  CLI interface with configuration management
-  Extensible pipeline architecture

### Universal RAG Builder (v2.0) - In Planning
Split into two focused EPICs for better implementation:

**EPIC 1: Web Crawling & Discovery System**
- Discovery Query: Convert user intent to search strategies
- Search Integration: Web search APIs, RSS feeds, sitemap discovery
- Intelligent Fetching: Rate limiting, retry logic, content deduplication
- CrawlManager: Robust error handling and job orchestration

**EPIC 2: RAG Index Construction**
- Multi-model Embeddings: Support for various embedding models
- Flexible Storage: Abstract IndexStore interface for different backends
- Optimized Retrieval: Fast semantic search and query capabilities
- Content Chunking: RAG-optimized text segmentation


### Documentation & Research
-  `/research/` directory: Maintains architectural decisions, spikes, and institutional knowledge
-  Spike-driven development: Thorough research before implementation
-  Comprehensive issue templates: Clear Definition of Done for all tasks  

---

## Quick Start

```bash
# 1) Fork and clone
# Click Fork on GitHub, then:
 git clone https://github.com/ACM-VIT/scrag.git
 cd scrag

# 2) Create a branch
 git checkout -b feat/your-feature

# 3) Install dependencies
 uv sync
 uv pip install -e src/scrag

> **Note:** This project uses `uv` as the canonical dependency manager. Dependencies are defined in `src/scrag/pyproject.toml` and managed via `uv.lock`. Do not use `pip install -r requirements.txt` as the root `requirements.txt` has been removed to avoid conflicts.

# 4) Verify the CLI
 uv run scrag info
```

---

## Usage
Run the Typer-powered CLI after syncing dependencies (as shown in Quick Start).

```sh
# Extract a single page using the default strategy cascade
uv run scrag extract https://example.com/article

# Choose a custom output location and persist as plain text
uv run scrag extract https://example.com/article --output data/custom --format txt

# Relax the minimum content length requirement for sparse pages
uv run scrag extract https://example.com/article --min-length 50
```

---

## Contributing
We welcome contributions of all kinds! Please read our [Contributing Guidelines](contributing.md) to get started quickly and make your PRs count.

---

## Hacktoberfest

<p>
   <a href="https://hacktoberfest.com/" target="_blank">
      <img alt="Hacktoberfest" src="https://img.shields.io/badge/Hacktoberfest-2025-indigo?style=flat-square" />
   </a>
</p>

Join us for Hacktoberfest! Quality > quantity.
- Aim for meaningful, well‑scoped PR/MRs that solve real issues.
- Non‑code contributions (docs, design, tutorials) are welcome via PR.
- Full participation details: https://hacktoberfest.com/participation

---

## Submitting a Pull Request

1. Fork the repository (top‑right on GitHub)
2. Clone your fork locally:
   ```bash
   git clone <HTTPS-ADDRESS>
   cd <NAME-OF-REPO>
   ```
3. Create a new branch:
   ```bash
   git checkout -b <your-branch-name>
   ```
4. Make your changes and stage them:
   ```bash
   git add .
   ```
5. Commit your changes:
   ```bash
   git commit -m "feat: your message"
   ```
6. Push to your fork:
   ```bash
   git push origin <your-branch-name>
   ```
7. Open a Pull Request and clearly describe what you changed and why. Link related issues (e.g., “Fixes #123”).

<!-- <img src="https://img.shields.io/github/:variant/:user/:repo?style=flat-square&labelColor=orange" alt="Open a Pull Request" /> -->

---

## Guidelines for Pull Request
- Avoid PRs that are automated/scripted or plagiarized from someone else’s work.
- Don’t spam; keep each PR focused and meaningful.
- The project maintainer’s decision on PR validity is final.
- For more, see our [Contributing Guidelines](contributing.md) and the Hacktoberfest [participation rules](https://hacktoberfest.com/participation).

---

## Authors

**Authors:** <!-- [author1's name](link), [author2's name](link) -->  
**Contributors:** <!-- Generate contributors list using https://contributors-img.web.app/preview -->

---

## Community & Conduct
By participating in this project, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

---

<div align="center">
  
Made with ❤️ by <a href="https://acmvit.in/" target="_blank">ACM‑VIT</a>

![Footer GIF](https://raw.githubusercontent.com/ACM-VIT/.github/master/profile/domains.gif)

</div>
