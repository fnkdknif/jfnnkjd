# Local Knowledge Base

> A local, explainable RAG system for knowledge workers

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Vision

For knowledge workers, researchers, and creators who need a **private, explainable, and auditable** system for analyzing documents, Local Knowledge Base provides **local RAG (Retrieval-Augmented Generation)** with full citation traceability and offline operation.

Unlike cloud-based solutions, our system runs entirely on your machine, giving you complete control over your data and ensuring privacy.

## ✨ Key Features (Phase 0 - Infrastructure)

- ✅ **Multi-format Document Parsing**
  - PDF (PyMuPDF)
  - Markdown
  - DOCX, HTML, TXT (planned)
  - EPUB, MOBI, AZW3 (M2)

- ✅ **Hierarchical Chunking**
  - Structure-preserving text segmentation
  - TOC-aware chunking with overlap
  - Citation-ready metadata

- ✅ **Database & Models**
  - SQLite/PostgreSQL support
  - Document, chunk, event, audit, artifact tracking
  - Migration system

- ✅ **CLI Interface**
  - Document ingestion
  - Status monitoring
  - Rich terminal UI

- ✅ **Configuration Management**
  - YAML-based config
  - Environment variable support
  - Path management

- ✅ **Logging & Audit**
  - Structured JSON logging
  - Event tracking
  - Audit trail for security

## 🚀 Quick Start

### Installation

```bash
# Clone repository
git clone https://github.com/yourname/LocalKnowledgeBase.git
cd LocalKnowledgeBase

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Initialize database
python -m app.cli init
```

### Basic Usage

```bash
# Ingest a document
python -m app.cli ingest path/to/document.pdf

# Ingest a directory
python -m app.cli ingest -r path/to/documents/

# List documents
python -m app.cli list

# Show document info
python -m app.cli info 1

# Check system status
python -m app.cli status
```

## 📋 Project Status

**Current Phase:** Phase 0 - Infrastructure ✅

### Completed
- [x] Project structure and configuration
- [x] Database schema and models
- [x] PDF and Markdown parsers
- [x] Hierarchical chunking
- [x] CLI framework
- [x] Logging and audit system
- [x] Unit tests

### Next (Phase 1)
- [ ] BM25 indexing (Whoosh)
- [ ] Vector indexing (Chroma)
- [ ] Hybrid search
- [ ] Ollama integration
- [ ] Basic RAG pipeline
- [ ] Citation alignment

### Roadmap
- **M1:** Core retrieval + RAG with citations
- **M2:** Export (PDF/Markdown), Study Guide, MindMap
- **M3:** GraphRAG, Whisper ASR, Reranker

## 🏗️ Architecture

```
app/
├── cli.py              # Command-line interface
├── core/
│   ├── config.py       # Configuration management
│   ├── utils.py        # Utility functions
│   ├── logging.py      # Logging and audit
│   ├── chunker.py      # Hierarchical chunking
│   ├── parser/         # Document parsers
│   │   ├── base.py
│   │   ├── pdf_parser.py
│   │   └── markdown_parser.py
│   └── indexer/        # Indexing (Phase 1)
├── models/             # SQLModel ORM models
│   ├── documents.py
│   ├── chunks.py
│   ├── events.py
│   ├── artifacts.py
│   └── audits.py
└── db/
    ├── session.py      # Database session
    └── migrate.py      # Migration system
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test
pytest tests/test_parser.py
```

## ⚙️ Configuration

Edit `config.yaml` to customize:

- File paths
- Chunking parameters
- Model settings (Ollama)
- Search configuration
- Export options

See `config.yaml` for all options.

## 🔒 Privacy & Security

- **Offline by default**: All processing runs locally
- **No external calls**: Unless explicitly enabled in config
- **Audit logging**: All external API calls are logged
- **Data ownership**: Your documents never leave your machine

## 📖 Documentation

- [Architecture](docs/architecture.md) - System design
- [API Reference](docs/api_reference.md) - API docs (Phase 1)
- [Development](docs/development.md) - Contributing guide

## 🤝 Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Built with:
- [FastAPI](https://fastapi.tiangolo.com/)
- [SQLModel](https://sqlmodel.tiangolo.com/)
- [PyMuPDF](https://pymupdf.readthedocs.io/)
- [Rich](https://rich.readthedocs.io/)
- [Click](https://click.palletsprojects.com/)

## 📞 Contact

- Issues: [GitHub Issues](https://github.com/yourname/LocalKnowledgeBase/issues)
- Discussions: [GitHub Discussions](https://github.com/yourname/LocalKnowledgeBase/discussions)

---

**Status:** Phase 0 Complete ✅ | Next: Search & RAG Implementation
