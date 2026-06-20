# 🕋 Auto Makah

**AI Agent Platform — Saudi Arabia's OpenClaw Twin (>95%)**

Auto Makah is a cloud-native AI agent operating platform. Create, deploy, and manage specialized AI agents for any domain — legal, accounting, marketing, engineering, and more.

## Features

- 🧠 **Agent Runtime** — Create specialized AI agents with domain knowledge
- 🏭 **Agent Factory** — 5 templates, one-click agent creation
- 🧬 **Self-Replication** — Clone agents for any domain
- 🐝 **Expert Swarm** — 8 domain experts, parallel execution
- 📚 **Knowledge Base** — 17 entries across 4 domains (IFRS, SOCPA, Saudi Law, GSTIC)
- 🎨 **Dashboard** — RTL Arabic professional dashboard
- 📱 **Telegram Bot** — @AutoMakahBot
- 📖 **Learning Loop** — Continuous improvement from interactions
- 🛠️ **Tool Registry** — Extensible tool system (8 categories)

## Tech Stack

- **Backend**: FastAPI + Python 3.12
- **Models**: ZenMux (GLM-5.2-free), GPT-4o-mini, Nemotron 120B
- **Database**: PostgreSQL / SQLite
- **Deploy**: Fly.io (2 machines, ams region)
- **Messaging**: Telegram Webhook

## Quick Start

```bash
pip install -r requirements.txt
python main.py
```

## API

- `GET /api/health` — Health check
- `GET /api/factory/templates` — Agent templates
- `POST /api/factory/create` — Create from template
- `POST /api/factory/clone` — Self-replication
- `GET /api/factory/learning` — Learning stats

## Telegram Commands

- `/start` — Welcome + templates
- `/agents` — Active agents
- `/create` — Create agent
- `/new_legal_expert` — Create legal expert
- `/clone medical المستشار الطبي` — Clone agent

## Live

- **Platform**: https://auto-makah.fly.dev
- **Bot**: @AutoMakahBot
- **Cost**: $0/month

🕋 Built from scratch — 23 commits — 52 files
