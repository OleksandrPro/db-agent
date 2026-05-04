# DB-Agent: Autonomous Database Migration Agent

An AI-driven agent designed to autonomously manage, generate, and safely test database migrations using LangGraph and Large Language Models (Google Gemini). 

**Academic Context:** This project is being developed as part of a university diploma thesis. It explores the application of Agentic AI workflows in the domain of Database Administration and automated schema evolution.

## Current Features (MVP 2.0)
Currently, the agent operates as a safe, linear pipeline (preparing for a transition to a non-deterministic Agentic ReAct architecture):
1. **Introspection:** Connects to the Production Database and extracts the current schema via SQLAlchemy.
2. **Generation:** Produces raw SQL migrations using Gemini. It is context-aware, receiving both the schema and previous error logs if a fix is required.
3. **Sandbox Testing:** Clones the production schema to an isolated Sandbox DB and safely tests the generated SQL to prevent syntax or constraint errors.
4. **Self-Healing Loop::** If the Sandbox test fails, the agent automatically routes back to the Generation node, passing the database error log for autonomous correction.
5. **Critic Review (Semantic Guardrail):** A secondary LLM node acts as a Senior DBA. It performs a "Double-Check" on Intent (did we do what the user asked?) and Safety (will this cause data loss on real production data?).
6. **Deployment:** Only after passing both Sandbox tests and Critic approval, the agent applies the migration to the Production DB.

## Setup for Local Development

1. **Clone the repository**
   ```
   git clone https://github.com/OleksandrPro/db-agent.git
   ```
   ```
   cd db-agent
   ```

2. **Configure Environment Variables**
    Create a `.env` file (you can look at example `.env.example`):

    ```
    # --- APP CONFIG ---
    ENVIRONMENT=TEST
    MAX_ITERATIONS=3

    # --- PROD DB CREDENTIALS ---
    DB_PROD__USER=postgres
    DB_PROD__PASSWORD=mysecretpassword
    DB_PROD__NAME=prod_db
    DB_PROD__PORT=5432
    DB_PROD__HOST=localhost
    EXTERNAL_PROD_PORT=5440

    # --- TEST DB (SANDBOX) CREDENTIALS ---
    DB_TEST__USER=user
    DB_TEST__PASSWORD=pass
    DB_TEST__NAME=sandbox_db
    DB_TEST__PORT=5432
    DB_TEST__HOST=localhost
    EXTERNAL_TEST_PORT=5441

    # --- AI AGENT (GEMINI) ---
    GOOGLE_API_KEY=your_api_key_here
    MODELS__GENERATOR=gemini-2.5-flash
    MODELS__CRITIC=gemini-2.5-flash
    ```

3. **Build the Docker Containers**
    The project is fully containerized. The agent service uses uv internally to manage dependencies and virtual environments.
    ```
    docker compose build
    ```
## Running the Agent

1. **Seed the Databases**

    Before running the agent, populate the Production and Test databases with the initial tables (users, orders, etc.):

    ```
    docker compose run --rm agent python src/scripts/seed_db.py
    ```

2. **Run the Agent Pipeline**
    Start the interactive agent script:

    ```
    docker compose run --rm agent
    ```

    Note: In the current stub version, the agent will ask for your prompt in the terminal and execute the pipeline.


## Next Steps (MVP 3.0 Roadmap)

**Human-in-the-Loop:** Pause the execution graph before production deployment to await human approval via CLI/API.
