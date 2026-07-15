# RIOS - Recursive Intelligence Operating System

A General-Purpose Evolutionary Scaffolding Framework for GPT-OSS-120B (GroqCloud)

**The model never learns. The framework evolves everything around it.**

## Overview

RIOS transforms GPT-OSS-120B on GroqCloud into a continuously evolving reasoning system through recursive scaffolding, evolutionary cognitive architectures, adaptive memory, and rigorous procedural evaluation.

Instead of:
```
User → LLM → Answer
```

RIOS implements:
```
User
 ↓
Recursive Intelligence Engine
 ↓
Planning
 ↓
Evolution
 ↓
Reasoning
 ↓
Verification
 ↓
Compression
 ↓
Memory Update
 ↓
Evaluation
 ↓
Repeat Forever (until Stop)
```

## Fundamental Principle

- **GPT-OSS-120B does NOT learn**
- **The framework evolves**: planning strategy, decomposition, verification, abstraction, compression, memory organization, reasoning order, recursive workflow, benchmark performance history, successful/failed patterns
- **Model = reasoning engine, Framework = evolving intelligence**

## Core Architecture

### Cognitive Genome

NOT a persona. Defines HOW reasoning occurs:

- Planning Depth, Verification Passes, Reasoning Order, Exploration Factor, Compression Level
- Memory Retrieval Strategy, Decomposition Style, Critique Strength, Reflection Depth
- Search Width, Confidence Threshold, Self-Correction Frequency, Abstraction Level, Information Compression Ratio

Genome is what evolves.

### Evolution

```
Gen0 default genome
 ↓
Mutate → Generate Candidate Genomes → Evaluate → Select Winner
 ↓
Repeat forever
```

Adaptive population sizing to respect GroqCloud limits:
- Easy: 1 genome
- Medium: 2 genomes
- Complex: 3 genomes
- Extreme: 5 genomes

### Recursive Scaffolding (No Artificial Limit)

```
Understand → Decompose → Generate Plan → Execute → Verify → Challenge Assumptions → Search Alternatives → Compress → Reflect → Mutate Genome → Repeat
```

### Hierarchical Memory

- **Working Memory**: Current reasoning, scaffold, plan, generation
- **Episodic Memory**: Previous generations, benchmark results, evolution history, mutation history
- **Semantic Memory**: Successful reasoning patterns, abstractions, planning templates, compression strategies, reusable insights
- **Compressed Memory**: Recursive summaries, hierarchical abstractions, information fingerprints, compressed reasoning trees

All aggressively compressed.

### Token Optimization

- Recursive summarization
- Hierarchical memory
- Semantic retrieval
- Duplicate elimination
- Prompt caching / Response caching / Checkpoint caching
- Abstraction
- Incremental context updates
- Minimum necessary info per generation

### PIES - Procedural Intelligence Evaluation System

Procedural benchmark generators generating **infinite unique tasks** (deterministic via seed, unseen before evaluation).

**20 Families Implemented:**
- Graph Algorithms, Mathematics, Formal Logic, Constraint Satisfaction, Optimization, Planning, Programming, Debugging, Compression, Scientific Reasoning, Pattern Recognition, Information Reconstruction, Scheduling, Causal Inference, Abstract Reasoning, Counterfactual Reasoning, Strategic Games, Algorithm Design, Multi-step Reasoning, Knowledge Integration

Each generator:
- Deterministic via seed
- Difficulty scalable 0..1
- Self-checking (solution + checker)
- Adversarial variants (rephrase, rename vars, add constraints, remove assumptions, reorder, inject noise, perturb numbers)

**Multi-Dimensional Metrics:**
Correctness, Logical consistency, Verification quality, Planning quality, Reasoning depth, Generalization, Robustness, Compression quality, Novelty, Self-correction, Information density, Token efficiency, Stability under paraphrasing, Resistance to adversarial modifications

**Weighted Fitness:**
- Reasoning Quality 20%
- Correctness 20%
- Verification 15%
- Planning 10%
- Generalization 10%
- Robustness 10%
- Compression 5%
- Token Efficiency 5%
- Novelty 5%
- Self-Correction 5%

### Stop / Resume

**Stop:**
- Halts recursion immediately
- Produces: Best answer, best scaffold, current genome, reasoning tree, memory, generation number, evolution history, benchmark performance, token stats, compression stats

**Resume:**
- Restores genome, scaffold, memory, checkpoint, lineage, tree, generation — continues exactly where stopped.

## Tech Stack

**Backend:**
- Python, FastAPI, AsyncIO, SQLite, WebSockets
- GroqCloud SDK (openai/gpt-oss-120b)
- Modular architecture, fully documented

**Frontend:**
- React, Next.js 14, TypeScript, TailwindCSS, Framer Motion, React Flow, Recharts
- Dark theme, glassmorphism, real-time streaming, responsive

## Project Structure

```
backend/
  app/
    config.py
    main.py
    core/
      cognitive_genome.py
      evolution_engine.py
      recursive_engine.py
      memory/ (working, episodic, semantic, compressed, manager)
      scaffolding/ (planner, decomposer, verifier, compressor, reflector)
      llm/ (groq_client, prompt_optimizer, cache)
      evaluation/
        pies/ (20 generators + benchmark_engine + difficulty + adversarial + metrics)
        fitness.py
      checkpoint/ (manager, models)
      telemetry/ (logger, stats)
    api/
      routes/ (evolution, benchmark, memory, checkpoints, stats)
      websockets/ (evolution_ws)
    db/ (database, models)

frontend/
  app/ (layout, page, globals.css)
  components/
    dashboard/
    reasoning-tree/
    genome-explorer/
    memory-inspector/
    benchmark-viewer/
    evolution-graph/
    checkpoints/
    stats/
    ui/
  lib/ (api, types)
```

## Setup

### Prerequisites

- Python 3.11+
- Node 20+
- Groq API Key (for GPT-OSS-120B) – optional, mock fallback works for dev

### Backend

```bash
cd backend
pip install -r requirements.txt
export GROQ_API_KEY=your_key
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

API docs at http://localhost:8000/docs
WebSocket at ws://localhost:8000/ws/evolution

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000

### Docker

```bash
docker-compose up --build
```

Frontend http://localhost:3000, Backend http://localhost:8000

## Usage

1. Enter a complex problem in header input
2. Click **Start** – engine begins infinite recursive evolution
   - Live WebSocket streaming of generations
   - Dashboard updates: fitness, tokens, compression, latency, cost
   - Reasoning tree visualizes scaffolding steps
   - Genome explorer shows cognitive DNA evolving
   - Memory inspector shows hierarchical memory stats
   - PIES benchmarks generate infinite tasks, adaptive difficulty
   - Evolution graph shows fitness over time
3. Click **Stop** – get best answer, scaffold, genome, full lineage, stats
4. **Resume** – continues exactly where stopped, restoring checkpoint

## Key Design Decisions

- **No wasted Groq calls**: Deterministic Python for orchestration, memory, evaluation, checkpointing, mutation, visualization – LLM only for genuine reasoning
- **Mock fallback**: If GROQ_API_KEY missing or package not installed, mock client simulates reasoning (offline dev & testing)
- **Token budgeting**: Prompt optimizer builds final prompt with allocation: Problem 20%, Genome 15%, Phase 25%, Memory 25%, History 15% + deduplication + summarization
- **Checkpoint persistence**: JSON files in ./data/checkpoints + prunes to last 50
- **Production quality**: Type hints, docstrings, modular, extensible, error handling, retry logic, logging, telemetry

## API Endpoints

- `GET /api/engine/dashboard` – aggregated dashboard
- `GET /api/evolution/state` – current state
- `POST /api/evolution/start` – start evolution (problem, resume)
- `POST /api/evolution/stop` – stop and get summary
- `POST /api/evolution/resume` – resume from checkpoint
- `GET /api/evolution/genome` – best genome
- `GET /api/benchmark/families` – list PIES families
- `POST /api/benchmark/generate` – generate procedural task
- `GET /api/memory` – memory stats
- `GET /api/checkpoints` – list checkpoints
- `GET /api/stats` – full telemetry
- `WS /ws/evolution` – real-time streaming (start, stop, get_state, resume)

## GroqCloud Model

Default model: `openai/gpt-oss-120b`
Configurable via `GROQ_MODEL` env var.
Uses OpenAI-compatible API at `https://api.groq.com/openai/v1`

Cost estimate: ~$0.15 / 1M input, $0.75 / 1M output (placeholder, check Groq pricing)

## Ultimate Goal

Create a recursive intelligence operating system that continuously evolves its reasoning architecture around GPT-OSS-120B. Not merely answering questions, but recursively refining, verifying, compressing, improving its own cognitive process over time. The evolving object is not the language model, but the external cognitive framework.

## License

MIT - Built as demonstration of evolutionary scaffolding principles.

## Future Extensibility

- Add vector DB (Chroma) for semantic retrieval
- Redis for distributed caching
- PostgreSQL for production persistence
- Multi-agent collaboration with genome speciation
- Formal verification integration (e.g., Z3 solver for checker)
- Additional PIES families
- Genome crossover tournaments, island models
- Reinforcement learning from human feedback on scaffolds
