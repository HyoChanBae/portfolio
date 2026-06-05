# 🛒 LLM-Driven E-Commerce Analytics Platform

> **An End-to-End Data Platform Leveraging the Olist Brazilian E-Commerce Dataset, Featuring a LangGraph-Based SQL Agent and an Automated ELT Pipeline Orchestrated by dbt & Apache Airflow.**

This project delivers a scalable, modern data platform designed to ingest and model large-scale e-commerce data while democratizing data access. By combining a **LangGraph-driven Multi-Agent SQL Engine** with a **Modern Data Stack (dbt + Airflow)**, it enables non-technical stakeholders to extract precise business insights through natural language queries.

---

## 🏗️ System Architecture

The infrastructure is strategically decoupled across **multi-instance AWS environments running Docker** to ensure high availability, fault isolation, and resource optimization.

- **AWS Instance 1 (Application & Storage Layer):**
  - **MySQL 8.0.46 (Docker):** Functions as the primary data store holding the raw e-commerce tables and processed analytical datasets.
  - **LangGraph & LangChain Platform:** Implements a multi-agent workflow. It intelligently routes user inputs (categorizing them into `general questions` or `sql questions`) and dynamically injects database table schemas into the LLM context to generate and execute precise, syntax-valid SQL queries.
- **AWS Instance 2 (Data Transformation & Orchestration Layer):**
  - **dbt (Data Build Tool):** Transforms raw relational data into production-ready analytical assets (Star Schema / Data Marts) while enforcing data quality checks.
  - **Apache Airflow 3.2.1 (Docker):** Orchestrates the dbt DAGs and the overall ELT workflow, ensuring resilient job scheduling and real-time monitoring.
  - **Runtime Environment:** Standardized on Python 3.12 within a Ubuntu OS container to ensure cross-instance environment consistency.

---

## 📊 Dataset Profile

- **Brazilian E-Commerce Public Dataset by Olist**
  - Real, anonymized e-commerce data comprising ~100k orders from 2016 to 2018 across Brazilian marketplaces.
  - **Core Entities:** Customers, Orders, Order Items, Payments, Reviews, Products, Sellers, and Geolocation.
  - **Technical Challenge:** Highly normalized and interconnected schema. It requires complex multi-table joins, making it an ideal production-grade benchmark to validate both dbt data modeling and the LLM's structural schema awareness.

---

## 🚀 Key Features & Technical Implementations

### 1. Intent-Routing SQL Agent via LangGraph
- **Smart Intent Routing:** Automatically classifies user prompts. Casual or high-level inquiries go to `general question`, while data-retrieval prompts trigger the `sql question` workflow.
- **Schema-Aware Context Injection:** To overcome LLM hallucinations in complex relational structures, the system dynamically feeds exact DDL/table schemas into the prompt context, guaranteeing the generation of syntactically accurate ANSI-SQL.
- **CI/CD Alignment:** LangChain/LangGraph application code developed locally is seamlessly managed via Git and deployed to AWS, ensuring a continuous and robust development workflow.

### 2. Analytical Data Modeling via dbt & Airflow
- **Layered Data Architecture:** Implemented a robust multi-layered dbt architecture (**Staging ➡️ Intermediate ➡️ Marts**) to convert raw data into highly optimized Star Schemas for business intelligence.
- **Data Quality & Governance:** Built-in dbt tests enforce data integrity (uniqueness, non-null assertions, and relationship constraints) preventing data pollution.
- **Containerized Orchestration:** Wrapped the entire transformation workflow into Airflow DAGs running on Docker, securing isolated execution, failure alerting, and automated retries.

---

## 🛠️ Tech Stack

| Category | Technologies |
| :--- | :--- |
| **Languages** | Python 3.12, SQL |
| **LLM Frameworks** | LangGraph, LangChain, OpenAI API |
| **Databases** | MySQL 8.0.46 (Docker) |
| **Data Transformation** | dbt (Data Build Tool) |
| **Orchestration** | Apache Airflow 3.2.1 (Docker) |
| **Infrastructure & DevOps** | AWS EC2, Ubuntu OS, Docker, Git |

---

## 📈 Business Impact & Key Takeaways

- **Empowering Non-Technical Teams (Data Democratization):** Eliminated the SQL bottleneck for business teams (e.g., product managers, marketers). Stakeholders can query complex trends—such as *"Which product category had the highest revenue in São Paulo last month?"*—in plain English and receive instant data outputs.
- **Production-Grade Data Reliability:** Integrating dbt tests into Airflow pipelines shifted data quality checks left, ensuring that schema breakages or data anomalies are caught and isolated before they impact downstream analytics.
