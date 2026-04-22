# stateful-ai-workflows

Stateful multi-step AI pipelines built with LangGraph. Each script demonstrates a different pattern of graph-based workflow: conditional routing, looping graphs, and LLM-driven branching.

## Projects

### calculator.py

A string arithmetic calculator implemented as a LangGraph graph. Parses a natural language string of numbers and operators, then routes through multiply/divide and plus/minus nodes respecting standard operator precedence. Loops back through the graph until all operations are resolved.

**Graph flow:**

```
START → read → route → multiplydivide ↘
                     ↘ plusminus      → route (loop until resolved) → answer → END
                     ↘ answer → END
```

**Concepts demonstrated:** looping conditional edges, input/output schemas, stateful operator precedence without a stack

---

### document_analyzer.py

A PDF document analyzer that classifies documents using Claude and extracts structured information based on document type.

**Graph flow:**

```
START → extract → classify → researchpaper → summary → END
                           ↘ news          → summary → END
```

**Concepts demonstrated:** LLM-driven conditional routing, PDF text extraction, structured JSON outputs via assistant prefill, input/output schemas

---

### ingest.py

A document ingestion pipeline that reads local `.pdf`, `.txt`, or `.md` files, chunks content by sentence-aware word windows, generates Voyage AI embeddings, and stores vectors in a ChromaDB Cloud collection.

**Graph flow:**

```
START → extract → chunk → embed_and_store → END
```

**Concepts demonstrated:** ingestion workflow design, PDF/text extraction, chunking with overlap, batched embeddings with retry on rate limits, ChromaDB Cloud persistence, input/output schemas

---

### research.py

A dual-mode RAG workflow for either deep research or fast query answering. In `research` mode, it decomposes questions, retrieves evidence for each sub-question, synthesizes findings, and generates a cited report. In `query` mode, it retrieves top matching documents and answers directly with citations.

**Graph flow:**

```
research mode: START → breaks → rag → synthesis → [HITL interrupt] → report → END
query mode:    START → retrieve → [HITL interrupt] → answer → END
```

**Concepts demonstrated:** multi-graph architecture, RAG with Voyage AI + ChromaDB Cloud, cited answer/report generation, schema-validated state, human-in-the-loop interrupts, checkpointing with MemorySaver

## Setup

```bash
git clone https://github.com/Anon0107/stateful-ai-workflows
cd stateful-ai-workflows
py -3.11 -m pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your Anthropic API key:

```bash
cp .env.example .env
```

## Usage

```bash
py -3.11 script_name.py
```

## Requirements

```
langgraph
anthropic
pypdf
python-dotenv
voyageai
chromadb
```

## Architecture

The workflows use LangGraph's `StateGraph` with typed state via `TypedDict`. Nodes return partial dicts - only updated keys - and LangGraph merges them into shared state. This keeps each step focused while preserving end-to-end context across the pipeline.

Input and output schemas are enforced via `input_schema` and `output_schema` parameters on `StateGraph`, restricting what the caller passes in and what gets returned.

## Stack

- [LangGraph](https://langchain-ai.github.io/langgraph/) — stateful graph orchestration
- [Anthropic API](https://docs.anthropic.com) — document classification and extraction
- [pypdf](https://pypdf.readthedocs.io) — PDF text extraction

