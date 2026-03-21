# Architecture Documentation

## System Overview

BruceWayneV1 is a modular AI-powered platform composed of distinct layers that communicate through well-defined interfaces. The system follows a service-oriented design with clear separation between the frontend presentation layer, the backend API layer, the AI inference layer, and the data persistence layer.

```
┌─────────────────────────────────────────────────────────────────┐
│                        CLIENT LAYER                             │
│                                                                 │
│   ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐     │
│   │  Terminal UI │  │  Dashboard   │  │  Cognitive       │     │
│   │  (Next.js)  │  │  Panels      │  │  Console         │     │
│   └──────┬──────┘  └──────┬───────┘  └────────┬─────────┘     │
│          │                │                    │                │
│          └────────────────┼────────────────────┘                │
│                           │  HTTP / WebSocket                   │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    GATEWAY LAYER                                 │
│                           │                                     │
│              ┌────────────┴────────────┐                        │
│              │    Nginx Reverse Proxy   │                        │
│              │    TLS / Rate Limiting   │                        │
│              └────────────┬────────────┘                        │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                      API LAYER                                   │
│                           │                                     │
│   ┌───────────────────────┴───────────────────────┐             │
│   │              FastAPI Application               │             │
│   │                                                │             │
│   │  ┌──────────┐  ┌───────────┐  ┌────────────┐ │             │
│   │  │  Auth     │  │  REST     │  │  WebSocket │ │             │
│   │  │  (JWT)    │  │  Routes   │  │  Handler   │ │             │
│   │  └──────────┘  └───────────┘  └────────────┘ │             │
│   │                                                │             │
│   │  ┌──────────┐  ┌───────────┐  ┌────────────┐ │             │
│   │  │ Middleware│  │ Throttling│  │  CORS      │ │             │
│   │  └──────────┘  └───────────┘  └────────────┘ │             │
│   └───────────────────────┬───────────────────────┘             │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                   INTELLIGENCE LAYER                             │
│                           │                                     │
│   ┌───────────┬───────────┼───────────┬──────────────┐         │
│   │           │           │           │              │         │
│   │  ┌───────┴──┐  ┌─────┴────┐  ┌───┴────┐  ┌─────┴──────┐ │
│   │  │ DeepSeek │  │ Trading  │  │Emotion │  │ Personality│ │
│   │  │ Engine   │  │ Engine   │  │Engine  │  │ Engine     │ │
│   │  └──────────┘  └──────────┘  └────────┘  └────────────┘ │
│   │                                                          │
│   │  ┌──────────┐  ┌──────────┐  ┌────────────────────────┐ │
│   │  │ Phi-3    │  │TinyLlama │  │ Model Router /         │ │
│   │  │ Kernel   │  │ Kernel   │  │ Kernel Selector        │ │
│   │  └──────────┘  └──────────┘  └────────────────────────┘ │
│   └──────────────────────────────────────────────────────────┘ │
│                           │                                     │
└───────────────────────────┼─────────────────────────────────────┘
                            │
┌───────────────────────────┼─────────────────────────────────────┐
│                    DATA LAYER                                    │
│                           │                                     │
│   ┌───────────┬───────────┼───────────┬───────────┐            │
│   │           │           │           │           │            │
│   │  ┌───────┴──┐  ┌─────┴────┐  ┌───┴────┐  ┌──┴────────┐  │
│   │  │PostgreSQL│  │  Redis   │  │Cognitive│  │ External  │  │
│   │  │  (RDBMS) │  │  (Cache) │  │ Memory  │  │ APIs      │  │
│   │  └──────────┘  └──────────┘  └─────────┘  └───────────┘  │
│   └───────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## Component Descriptions

### Client Layer

**Terminal UI (Next.js)** -- The primary interface is a terminal-style web application built with Next.js and TypeScript. It provides a command-line-like experience for interacting with the AI system, viewing real-time trading data, and monitoring cognitive state.

**Dashboard Panels** -- Specialized panels for risk analytics, trading views, and performance monitoring. These components render real-time charts and metrics using data streamed over WebSocket connections.

**Cognitive Console** -- A dedicated interface for interacting with the AI's cognitive features, including self-reflection, memory inspection, and personality configuration.

### Gateway Layer

**Nginx Reverse Proxy** -- Handles TLS termination, request routing, rate limiting, and static asset serving. Routes traffic to the appropriate backend service based on URL path.

### API Layer

**FastAPI Application** -- The core backend server provides REST endpoints, WebSocket connections, JWT-based authentication, request throttling, and CORS management. Routes are organized by domain (trading, AI, health, simulation).

**Authentication** -- JWT-based token flow with role-based access control. Tokens are issued on login and refreshed via a dedicated endpoint.

**WebSocket Handler** -- Maintains persistent connections for real-time streaming of market data, AI responses, and system events.

### Intelligence Layer

**DeepSeek Engine** -- Primary language model integration for cognitive reasoning, including prompt management, memory bridging, and cognitive loop processing.

**Trading Engine** -- Quantitative analysis module with strategy evolution, simulation, and reinforcement learning-based trading.

**Emotion Engine** -- Detects emotional context in user interactions and adapts responses accordingly. Maintains an emotion state model and emotion memory.

**Personality Engine** -- Manages AI persona through configurable archetypes, personality traits, and narrative style.

**Model Router** -- Dynamically selects the appropriate inference model (DeepSeek, Phi-3, TinyLlama) based on the task, available resources, and configuration.

### Data Layer

**PostgreSQL** -- Primary relational database for user data, trading history, configuration, and persistent state.

**Redis** -- In-memory cache for session data, real-time state, rate limiting counters, and pub/sub messaging.

**Cognitive Memory** -- Specialized storage for the AI's memory system, supporting episodic memory, knowledge graphs, and contextual recall.

**External APIs** -- Integrations with market data providers, news feeds, and third-party AI services.

---

## Data Flow

### Request Flow (REST)

1. Client sends HTTP request to Nginx.
2. Nginx terminates TLS, applies rate limiting, and forwards to FastAPI.
3. FastAPI middleware validates JWT, applies throttling.
4. Route handler processes the request, invoking services as needed.
5. Services interact with AI engines, database, or cache.
6. Response travels back through the same path.

### Real-Time Flow (WebSocket)

1. Client establishes WebSocket connection through Nginx.
2. FastAPI upgrades connection and authenticates via token.
3. Backend pushes events (market data, AI responses, system alerts) in real-time.
4. Client sends commands and queries over the same connection.

### AI Inference Flow

1. Request arrives at the API layer with a prompt or task.
2. Model Router evaluates the task and selects an appropriate model.
3. Selected engine processes the input through its cognitive loop.
4. Emotion Engine and Personality Engine modulate the response.
5. Cognitive Memory is consulted and updated.
6. Final response is returned to the caller.

---

## Technology Choices

| Component       | Technology       | Rationale                                                |
|-----------------|------------------|----------------------------------------------------------|
| Backend         | FastAPI          | High performance async Python framework with auto-docs   |
| Frontend        | Next.js          | SSR, file-based routing, strong TypeScript support       |
| Database        | PostgreSQL 16    | Robust relational DB with JSON support and reliability   |
| Cache           | Redis 7          | Sub-millisecond latency, pub/sub, and data structures    |
| AI Models       | DeepSeek/Phi-3   | Balance of capability, speed, and resource requirements  |
| Auth            | JWT              | Stateless, scalable token-based authentication           |
| Proxy           | Nginx            | Battle-tested reverse proxy with TLS and load balancing  |
| Containers      | Docker           | Reproducible environments and simplified deployment      |
| CI/CD           | GitHub Actions   | Native GitHub integration, matrix builds, caching        |
