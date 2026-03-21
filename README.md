# BruceWayneV1

An advanced AI-powered trading and cognitive intelligence platform. BruceWayneV1 combines deep learning models, real-time market analysis, emotion detection, and autonomous agent capabilities into a unified system for strategic decision-making.

---

## Features

- **AI-Powered Trading Engine** -- Quantitative analysis with reinforcement learning, strategy evolution, and multi-model inference (DeepSeek, Phi-3, TinyLlama).
- **Cognitive Intelligence Core** -- Self-reflective AI with personality engine, archetype-based personas, and emotion-aware responses.
- **Real-Time Market Connector** -- Live data ingestion from multiple sources with WebSocket streaming.
- **Interactive Terminal UI** -- Next.js-based dashboard with a terminal-style interface, cognitive console, and episode history.
- **Memory and Learning** -- Persistent cognitive memory, feedback loops, and self-auditing mechanisms.
- **Risk Management** -- Volatility guards, bias filtering, compliance governance, and crisis simulation.
- **Voice Interface** -- Speech engine integration for voice-based interactions.
- **Video Generation** -- AI-driven content generation capabilities.
- **Web Scraping** -- Automated data collection from web sources.

---

## Architecture Overview

```
                        +-------------------+
                        |    Nginx Proxy    |
                        |   (ports 80/443)  |
                        +---------+---------+
                                  |
                    +-------------+-------------+
                    |                           |
           +--------+--------+       +---------+--------+
           |   Frontend      |       |   Backend API    |
           |   (Next.js)     |       |   (FastAPI)      |
           |   Port 3000     |       |   Port 8000      |
           +--------+--------+       +---------+--------+
                    |                           |
                    |              +------------+------------+
                    |              |            |            |
                    |     +-------+--+  +------+---+  +-----+------+
                    |     | AI Core  |  | Trading  |  | Emotion    |
                    |     | Engine   |  | Engine   |  | Engine     |
                    |     +----------+  +----------+  +------------+
                    |
           +--------+--------+--------+
           |                 |        |
    +------+---+    +-------++   +----+-----+
    | PostgreSQL|    | Redis  |   | External |
    | (Data)    |    | (Cache)|   | APIs     |
    +-----------+    +--------+   +----------+
```

---

## Tech Stack

### Backend
- **Python 3.10** -- Core language
- **FastAPI** -- REST API framework
- **Uvicorn** -- ASGI server
- **SQLAlchemy** -- ORM / database toolkit
- **PostgreSQL 16** -- Primary database
- **Redis 7** -- Caching and session storage
- **PyTorch / TensorFlow** -- Deep learning inference
- **JWT** -- Authentication

### Frontend
- **Next.js** -- React framework
- **TypeScript** -- Type-safe JavaScript
- **Tailwind CSS** -- Utility-first styling
- **WebSocket** -- Real-time communication

### Infrastructure
- **Docker / Docker Compose** -- Containerization
- **Nginx** -- Reverse proxy and TLS termination
- **GitHub Actions** -- CI/CD pipeline

---

## Quick Start

### Prerequisites

- Python 3.10+
- Node.js 20+
- Docker and Docker Compose (for containerized deployment)
- PostgreSQL 16 (for local development without Docker)
- Redis 7 (for local development without Docker)

### Local Development

```bash
# Clone the repository
git clone https://github.com/your-org/BruceWayneV1.git
cd BruceWayneV1

# Run the automated setup script
chmod +x scripts/setup.sh
./scripts/setup.sh

# Or set up manually:

# Create and activate Python virtual environment
python -m venv venv
source venv/bin/activate   # Linux/macOS
# venv\Scripts\activate    # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies
npm install

# Copy environment file and configure
cp .env.example .env
# Edit .env with your settings

# Start the backend
uvicorn main:app --reload --port 8000

# In a separate terminal, start the frontend
npm run dev
```

### Docker Deployment

```bash
# Build and start all services
docker compose -f docker-compose.prod.yml up -d --build

# View logs
docker compose -f docker-compose.prod.yml logs -f

# Stop services
docker compose -f docker-compose.prod.yml down
```

### Using the Makefile

```bash
make install       # Install all dependencies
make dev           # Start development servers
make test          # Run all tests
make lint          # Run linters
make docker-up     # Start Docker services
make docker-down   # Stop Docker services
```

---

## Environment Variables

| Variable             | Description                        | Default                  |
|----------------------|------------------------------------|--------------------------|
| `DATABASE_URL`       | PostgreSQL connection string       | `postgresql://...`       |
| `REDIS_URL`          | Redis connection string            | `redis://localhost:6379` |
| `JWT_SECRET`         | Secret key for JWT token signing   | (required)               |
| `DEEPSEEK_API_KEY`   | DeepSeek model API key             | (required)               |
| `ENVIRONMENT`        | Runtime environment                | `development`            |
| `LOG_LEVEL`          | Logging verbosity                  | `info`                   |
| `NEXT_PUBLIC_API_URL`| Backend API URL for frontend       | `http://localhost:8000`  |
| `NEXT_PUBLIC_WS_URL` | WebSocket URL for frontend         | `ws://localhost:8000/ws` |
| `POSTGRES_PASSWORD`  | PostgreSQL password (Docker)       | (required)               |
| `CORS_ORIGINS`       | Allowed CORS origins               | `*`                      |

---

## API Endpoints Overview

### Authentication
| Method | Endpoint         | Description             |
|--------|------------------|-------------------------|
| POST   | `/auth/login`    | Authenticate user       |
| POST   | `/auth/register` | Register new user       |
| POST   | `/auth/refresh`  | Refresh JWT token       |

### Core API
| Method | Endpoint           | Description              |
|--------|--------------------|--------------------------|
| GET    | `/health`          | Health check             |
| GET    | `/api/v1/status`   | System status            |
| POST   | `/api/v1/chat`     | Send chat message        |
| WS     | `/ws`              | WebSocket connection     |

### Trading
| Method | Endpoint                     | Description              |
|--------|------------------------------|--------------------------|
| GET    | `/api/v1/trading/positions`  | Current positions        |
| POST   | `/api/v1/trading/execute`    | Execute trade            |
| GET    | `/api/v1/trading/strategies` | List strategies          |

### AI and Cognitive
| Method | Endpoint                    | Description               |
|--------|-----------------------------|---------------------------|
| POST   | `/api/v1/ai/infer`          | Run AI inference          |
| GET    | `/api/v1/ai/models`         | Available models          |
| POST   | `/api/v1/cognitive/reflect`  | Trigger self-reflection  |

For complete API documentation, see [docs/api.md](docs/api.md).

---

## Project Structure

```
BruceWayneV1/
├── ai/                     # AI engine modules
│   ├── deepseek_engine/    # DeepSeek integration
│   ├── emotion_engine/     # Emotion detection and response
│   └── trading_engine/     # Trading AI strategies
├── ai_core/                # Core AI infrastructure
├── app/                    # Main application package
│   ├── api/                # API routes and middleware
│   ├── ai/                 # Advanced quantitative AI
│   ├── config/             # Configuration management
│   ├── core/               # Core business logic
│   ├── dashboard/          # Dashboard modules
│   └── models/             # Data models
├── backend/                # Backend utilities
├── components/             # React UI components
├── config/                 # Configuration files
├── contexts/               # React contexts
├── data/                   # Data storage
├── database/               # Database schemas and migrations
├── docker/                 # Docker configuration
├── docs/                   # Documentation
├── frontend/               # Frontend application code
├── hooks/                  # React hooks
├── infrastructure/         # Infrastructure configs (nginx, etc.)
├── models/                 # ML model definitions
├── modules/                # Feature modules
├── pages/                  # Next.js pages
├── public/                 # Static assets
├── routes/                 # Additional route definitions
├── scripts/                # Utility scripts
├── services/               # Service layer
├── store/                  # State management
├── styles/                 # CSS / Tailwind styles
├── tests/                  # Test suites
├── types/                  # TypeScript type definitions
├── utils/                  # Shared utilities
├── workers/                # Background workers
├── docker-compose.prod.yml # Production compose
├── main.py                 # Backend entry point
├── package.json            # Node.js dependencies
├── requirements.txt        # Python dependencies
├── Makefile                # Developer commands
└── README.md               # This file
```

---

## Contributing

1. **Fork** the repository.
2. **Create a feature branch**: `git checkout -b feature/my-feature`
3. **Make your changes** and write tests.
4. **Run the linter and tests**:
   ```bash
   make lint
   make test
   ```
5. **Commit** with a clear message: `git commit -m "Add: description of change"`
6. **Push** to your fork: `git push origin feature/my-feature`
7. **Open a Pull Request** against `develop`.

### Commit Message Convention

- `Add:` -- New features
- `Fix:` -- Bug fixes
- `Update:` -- Enhancements to existing features
- `Refactor:` -- Code restructuring
- `Docs:` -- Documentation changes
- `Test:` -- Test additions or modifications
- `Chore:` -- Maintenance tasks

### Code Style

- **Python**: Follow PEP 8. Use `black` for formatting, `isort` for imports.
- **TypeScript/JavaScript**: Use ESLint and Prettier.
- **Commits**: Keep atomic; one logical change per commit.

---

## Testing

```bash
# Run all tests
make test

# Backend tests only
pytest tests/ -v --cov=.

# Frontend tests only
npm test

# Run with specific markers
pytest tests/ -m "not slow" -v
```

---

## Monitoring

The application exposes a `/health` endpoint returning system status. In production, integrate with your monitoring stack (Prometheus, Grafana, Datadog, etc.) by scraping the health endpoint and collecting Docker container metrics.

---

## License

This project is licensed under the MIT License.

```
MIT License

Copyright (c) 2024 BruceWayneV1

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```
