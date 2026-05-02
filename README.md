# DB-Agent: Autonomous Database Migration Agent

An AI-driven agent designed to autonomously manage, generate, and safely test database migrations using LangGraph and Large Language Models (Google Gemini). 

**Academic Context:** This project is being developed as part of a university diploma thesis. It explores the application of Agentic AI workflows in the domain of Database Administration and automated schema evolution.

## Current Features (MVP 1.0)
Currently, the agent operates as a safe, linear pipeline (preparing for a transition to a non-deterministic Agentic ReAct architecture):
1. **Introspection:** Connects to the Production Database and extracts the current schema via SQLAlchemy.
2. **Generation:** Generates raw SQL migrations based on the user prompt and the current schema. Uses a Factory pattern to switch between a Mock provider and Gemini based on the environment.
3. **Sandbox Testing:** Clones the production schema to an isolated Sandbox DB and safely tests the generated SQL to prevent syntax or constraint errors.
4. **Deployment:** Simulates the deployment of validated SQL to the Production DB.

## Setup for Local Development

1. **Clone the repository**
   ```
   git clone https://github.com/OleksandrPro/db-agent.git
   ```
   ```
   cd db-agent
   ```

2. **Configure Environment Variables**
    Create a .env file based on the provided example:
    ```
    cp .env.example .env
    ```

    Open the .env file and configure your variables. The project uses an environment-based factory to manage API costs during development:

    ```
    # Available options: TEST, DEV, PROD
    # DEV will automatically use the MockSQLGenerator
    # TEST and PROD will use the real Gemini model
    ENVIRONMENT=DEV

    # Required only if ENVIRONMENT=PROD or ENVIRONMENT=TEST
    GOOGLE_API_KEY=your_gemini_api_key_here
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


## Next Steps (MVP 2.0 Roadmap)

**Self-Healing Loop:** Automatically return to the Generation node with error logs if the Sandbox test fails.

**Critic Agent:** Introduce a secondary LLM node to perform semantic Code Review (analyzing the prompt, initial schema, generated SQL, and resulting sandbox schema) before deployment.

**Human-in-the-Loop:** Pause the execution graph before production deployment to await human approval via CLI/API.