# 🔗 Supply Chain Graph — Order to Cash

> A **graph-powered supply chain analytics system** with **natural language querying using LLMs**.
> Explore interconnected business entities visually and extract insights through conversational queries.

---

## 🚀 Tech Stack

<p align="center">

<img src="https://skillicons.dev/icons?i=python,fastapi,sqlite,html,css,js" />

<img src="https://img.shields.io/badge/LLM-Groq%20%7C%20LLaMA3-F55036?style=for-the-badge" />
<img src="https://img.shields.io/badge/Graph-Vis.js-4a6cf7?style=for-the-badge" />
<img src="https://img.shields.io/badge/Deploy-Render-46E3B7?style=for-the-badge" />

</p>

---

## ⭐ Key Highlights

* 🔗 Graph-based visualization of relational supply chain data
* 💬 Natural language → SQL → insights pipeline
* 🛡️ Multi-layer guardrails for safe LLM usage
* ⚡ Zero-infrastructure deployment using SQLite
* 🧠 Two-step LLM reasoning for higher accuracy

---
🚀 Live Demo
🔗 View Live App → https://supply-chain-ciom.onrender.com
---


## 🏗️ Architecture Overview

```
                        ┌────────────────────────────┐
                        │        Frontend UI         │
                        │  Graph (Vis.js) + Chat     │
                        └────────────┬───────────────┘
                                     │ HTTP
                        ┌────────────▼───────────────┐
                        │      FastAPI Backend       │
                        │                            │
                        │  ┌──────────────┐          │
                        │  │ /api/graph   │          │
                        │  └──────┬───────┘          │
                        │         │                  │
                        │  ┌──────▼───────┐          │
                        │  │ SQLite DB    │          │
                        │  │ (data.db)    │          │
                        │  └──────────────┘          │
                        │                            │
                        │  ┌──────────────┐          │
                        │  │ /api/chat    │          │
                        │  └──────┬───────┘          │
                        │         │                  │
                        │  ┌──────▼────────┐         │
                        │  │ Groq LLM      │         │
                        │  │ (LLaMA 3.3)   │         │
                        │  └───────────────┘         │
                        └────────────────────────────┘
```

---

## 🔄 Query Flow (End-to-End)

```
User Question
     │
     ▼
Guardrail Layer 1 (Keyword Filter)
     │
     ▼
LLM Step 1 → Generate SQL
     │
     ▼
Guardrail Layer 2 (SQL Validation)
     │
     ▼
SQLite Execution
     │
     ▼
LLM Step 2 → Generate Answer
     │
     ▼
Final Natural Language Response
```

---

## 🗄️ Database Choice — SQLite

### Why SQLite over Neo4j or PostgreSQL?

| Factor         | SQLite ✅                        | Neo4j                               | PostgreSQL                        |
| -------------- | ------------------------------- | ----------------------------------- | --------------------------------- |
| Setup          | Zero configuration, single file | Requires setup / cloud instance     | Requires server setup             |
| Deployment     | Ships with app                  | External dependency                 | External dependency               |
| Query Language | SQL (LLM-friendly)              | Cypher (specialized)                | SQL                               |
| Cost           | Free                            | Limited free tier                   | Limited free tier                 |
| Performance    | Ideal for small–medium datasets | Optimized for graph-heavy workloads | Optimized for large-scale systems |
| Learning Curve | Easy                            | Steep                               | Moderate                          |

---

### ✅ Why SQLite was chosen

* Dataset (~3,000 rows, 19 tables) fits well within SQLite limits
* No infrastructure or server management required
* Portable (`data.db` file travels with app)
* Faster development and debugging
* **Highly compatible with LLM-generated SQL**

---

### 🧠 Design Insight

Although SQLite is relational, the system **implements a graph abstraction layer**:

```
Nodes  → Orders, Customers, Products, Payments
Edges  → Foreign key relationships
Graph  → Rendered using Vis.js
```

👉 Result:
Graph-like exploration **without needing a graph database**

---

## 🧠 LLM Prompting Strategy

### Model Used

* **LLaMA 3.3 70B via Groq**
* Chosen for **fast inference + free tier**

---

### 🔁 Two-Step LLM Pipeline

#### Step 1 — SQL Generation

* Input: User question
* Context provided:

  * Full database schema
  * Table relationships
  * Query patterns

Rules enforced:

* Only SELECT queries
* No explanations
* OUT_OF_SCOPE for irrelevant queries

---

#### Step 2 — Answer Generation

* Input: SQL results
* Output:

  * Clean natural language summary
  * Bullet points when needed
  * No technical jargon

---

### ✅ Why Two-Step Approach?

* Separation of concerns
* Better accuracy
* Easier debugging
* Reduced hallucination risk

---

## 🛡️ Guardrails & Safety

### Layer 1 — Keyword Filtering

Blocks clearly unrelated queries before hitting LLM

```python
["poem", "weather", "movie", "joke", "sports"]
```

---

### Layer 2 — LLM Scope Control

LLM is instructed:

```
If query is not related → return OUT_OF_SCOPE
```

---

### Layer 3 — SQL Safety Check

```python
["DROP", "DELETE", "INSERT", "UPDATE", "ALTER"]
```

👉 Prevents destructive queries from execution

---

## 📊 Data Model Overview

### 6 Core Entities

* Customers
* Sales Orders
* Products
* Deliveries
* Invoices
* Payments

### Relationships

```
Customer → Order → Delivery → Invoice → Payment
                 ↓
              Product
```

---

## 💬 Example Queries

| Query                   | Output                             |
| ----------------------- | ---------------------------------- |
| Top billed products     | Aggregation over billing documents |
| Trace order lifecycle   | Full entity chain                  |
| Orders without invoices | Missing flow detection             |
| Unbilled deliveries     | Operational gaps                   |
| Customer totals         | Revenue insights                   |

---

## ⚙️ Run Locally

```bash
git clone https://github.com/TechxKashish/supply-chain.git
cd supply-chain

pip install -r requirements.txt

echo "GROQ_API_KEY=your_key_here" > .env

python ingest.py

python -m uvicorn main:app --reload
```

---

## 📁 Project Structure

```
supply-chain/
├── main.py
├── ingest.py
├── data.db
├── index.html
├── vis-network.min.js
├── requirements.txt
├── Procfile
├── .env
├── dataset/
```

---

## 🔮 Future Improvements

* Streaming LLM responses
* Graph highlighting from chat
* Conversation memory
* CSV export
* Neo4j integration (advanced scaling)

---

## 👨‍💻 Built With AI Assistance

Developed using AI tools for:

* Backend development
* Prompt engineering
* Data modeling
* Debugging & optimization

---

<div align="center">

### 💡 Designed for real-world supply chain intelligence

**Radhika Jindal · 2026**

</div>
