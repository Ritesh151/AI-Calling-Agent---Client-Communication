# ⚡ AI Calling System

<table>
<tr>
<td>

### 🚀 What is this?

Production-grade AI-powered calling platform that handles:

- Incoming calls automatically  
- Android device management  
- Message recording  
- AI transcript generation  
- Real-time monitoring  
- Multi-device scaling  

</td>

<td>

<img src="https://media.giphy.com/media/v1.Y2lkPTc5MGI3NjExNjJ3NmVqNm1pNmR3YzF4emM1dHk0N3U5dDZ0eDZ6OWkwNnY4emV2YyZlcD12MV9naWZzX3NlYXJjaCZjdD1n/l3vR85PnGsBwu1PFK/giphy.gif" width="300"/>

</td>
</tr>
</table>

---

# 🌌 Platform Features

<table>

<tr>

<td width="33%" align="center">

## 🤖 AI Engine

AI call workflows  
Transcript generation  
Voice processing  

</td>

<td width="33%" align="center">

## 📱 Android Layer

ADB Management  
USB Device Detection  
Registry System  

</td>

<td width="33%" align="center">

## 🔐 Security

JWT Auth  
Rate Limiting  
Encrypted Storage  

</td>

</tr>

</table>

---

# 🧠 System Architecture

<div align="center">

```mermaid
graph TD

A[Incoming Call]

--> B[Android Device Layer]

B --> C[ADB Manager]

C --> D[FastAPI Backend]

D --> E[Call Session Engine]

E --> F[AI Processing]

F --> G[Transcript Engine]

G --> H[PostgreSQL]

D --> I[Redis Cache]

D --> J[Next.js Dashboard]

````

</div>

---

# 🛠 Tech Stack

<table>

<tr>

<td>

### Frontend

* Next.js 15
* TypeScript
* Tailwind
* Zustand
* React Query
* Axios
* Shadcn UI

</td>

<td>

### Backend

* FastAPI
* Python 3.12
* SQLAlchemy 2
* PostgreSQL
* Redis
* Alembic
* Pydantic

</td>

<td>

### DevOps

* Docker
* Docker Compose
* Ruff
* Black
* MyPy
* pytest
* Vitest

</td>

</tr>

</table>

---

# 📊 Repository Analytics

<div align="center">

<img height="180em" src="https://github-readme-stats.vercel.app/api?username=Ritesh151&show_icons=true&theme=tokyonight"/>

<img height="180em" src="https://github-readme-stats.vercel.app/api/top-langs/?username=Ritesh151&layout=compact&theme=tokyonight"/>

</div>

---

# 🔥 Contribution Activity

<div align="center">

<img width="100%" src="https://github-readme-activity-graph.vercel.app/graph?username=Ritesh151&theme=tokyo-night"/>

</div>

---

# 🐍 Contribution Snake

<div align="center">

<img src="https://raw.githubusercontent.com/Ritesh151/Ritesh151/output/github-contribution-grid-snake-dark.svg"/>

</div>

---

# 📂 Project Structure

```text
project-root/

├── frontend/
│   ├── app/
│   ├── components/
│   ├── hooks/
│   ├── services/
│   └── stores/

├── backend/
│   ├── api/
│   ├── services/
│   ├── repositories/
│   ├── schemas/
│   └── middlewares/

├── docs/

├── docker/

└── scripts/
```

---

# ⚙ Quick Start

## Clone Repository

```bash
git clone https://github.com/Ritesh151/AI-Calling-Agent---Client-Communication.git

cd AI-Calling-Agent---Client-Communication
```

---

## Docker Setup

```bash
docker compose up -d
```

---

## Backend

```bash
cd backend

python -m venv venv

pip install -r requirements.txt

alembic upgrade head

uvicorn app.main:app --reload
```

---

## Frontend

```bash
cd frontend

npm install

npm run dev
```

---

# 🔐 Security Layer

<table>

<tr>

<td>JWT Tokens</td>

<td>Password Hashing</td>

<td>Rate Limiting</td>

</tr>

<tr>

<td>CORS Security</td>

<td>Input Validation</td>

<td>ORM Protection</td>

</tr>

</table>

---

# 🌍 Deployment Flow

```text
Developer

↓

GitHub Push

↓

CI/CD Pipeline

↓

Docker Build

↓

Backend Deploy

↓

Frontend Deploy

↓

Production Monitoring
```

---

# 📜 License

MIT License

---

<div align="center">

## Developed By

# 🚀 Ritesh Gajjar

AI Systems • Automation • Production Infrastructure

<img width="100%" src="https://capsule-render.vercel.app/api?type=waving&height=140&section=footer&color=0:00F7FF,100:7C3AED"/>

</div>
```
