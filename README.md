markdown# airflow-weather-pipeline

A batch ETL pipeline that scrapes real-time weather data for US and India cities using Apache Airflow, BeautifulSoup, and PostgreSQL — fully containerized with Docker Compose.

## Tech Stack
- **Apache Airflow 2.8.1** — DAG orchestration and scheduling
- **BeautifulSoup + Requests** — Web scraping from wttr.in
- **PostgreSQL 15** — Data storage
- **Docker Compose** — Container orchestration

## Pipeline Architecture
wttr.in → scrape_weather → transform_data → load_to_postgres
Runs on hourly schedule. Each DAG run scrapes NYC, Chicago, Hyderabad, and Bangalore.

## How to Run

### 1. Start all containers
```bash
docker-compose up airflow-init
docker-compose up -d
```

### 2. Open Airflow UI
Go to http://localhost:8080
Username: `airflow` Password: `airflow`

### 3. Trigger the DAG
Find `weather_pipeline` → toggle ON → click Run

### 4. Query the data
```bash
docker exec -it <postgres_container> psql -U airflow -d airflow -c "SELECT * FROM weather_data;"
```

## Project Structure
airflow-weather-pipeline/
├── dags/
│   └── weather_dag.py       # DAG with 3 tasks: scrape → transform → load
├── logs/                    # Airflow task logs (gitignored)
├── plugins/                 # Custom Airflow plugins (empty for now)
├── docker-compose.yml       # Airflow + Postgres services
├── requirements.txt         # Python dependencies
├── .env                     # Airflow UID config
└── .gitignore

## What I Learned
- How to write Airflow DAGs with PythonOperator
- How XCom works for passing data between tasks
- How to connect Airflow to PostgreSQL using psycopg2
- How Docker Compose networks multiple containers together
