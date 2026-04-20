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

### research_workflow.py
A multi-step research pipeline that takes a user question, breaks it into sub-questions, retrieves relevant documents from a ChromaDB vector store via Voyage AI embeddings, synthesizes findings, and generates a cited report.

**Graph flow:**
```
START → breaks → rag → synthesis → [HITL interrupt] → report → END
```

**Concepts demonstrated:** RAG inside a LangGraph graph, Voyage AI embeddings, ChromaDB Cloud integration, input/output schemas, multi-node state accumulation, human-in-the-loop interrupts, checkpointing with MemorySaver

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

Both scripts use LangGraph's `StateGraph` with typed state via `TypedDict`. Nodes return partial dicts — only updated keys — and LangGraph merges them into the shared state. Conditional routing is handled by pure Python functions that return node name strings, keeping routing logic fully transparent and testable.

Input and output schemas are enforced via `input_schema` and `output_schema` parameters on `StateGraph`, restricting what the caller passes in and what gets returned.

## Stack

- [LangGraph](https://langchain-ai.github.io/langgraph/) — stateful graph orchestration
- [Anthropic API](https://docs.anthropic.com) — document classification and extraction
- [pypdf](https://pypdf.readthedocs.io) — PDF text extraction