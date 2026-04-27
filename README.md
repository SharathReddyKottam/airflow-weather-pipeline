# airflow-weather-pipeline

A batch ETL pipeline that scrapes real-time weather data for 4 cities (NYC, Chicago, Hyderabad, Bangalore) on an hourly schedule — built with Apache Airflow, BeautifulSoup, PostgreSQL, and Docker Compose.

This is a learning project. If you're trying to get hands-on with Airflow for the first time, this is a good starting point — it's small enough to understand completely but uses the same patterns you'd see in a real data engineering job.

---

## What it does

Every hour, the pipeline:

1. Scrapes live weather data from [wttr.in](https://wttr.in) for each city
2. Cleans and transforms the raw response (casts types, normalizes strings)
3. Loads the results into a PostgreSQL table

You can watch all 3 steps run in the Airflow UI and query the results directly in Postgres.

---

## Tech Stack

### Apache Airflow

Airflow is a workflow orchestration tool — it lets you schedule and monitor data pipelines. Instead of running a Python script manually with a cron job, Airflow gives you a visual dashboard, task-level logging, retry logic, and run history. The core concept is a **DAG** (Directed Acyclic Graph) — a Python file that defines what tasks to run, in what order, and on what schedule. In this project the DAG has 3 tasks: scrape → transform → load, running hourly.

### BeautifulSoup + Requests

`requests` fetches the HTTP response from wttr.in (which returns JSON). `BeautifulSoup` is typically used for parsing HTML, but here we use `requests` + `.json()` directly since wttr.in supports a JSON format endpoint. If you swap this out for a real HTML scraping target, BeautifulSoup is how you'd navigate the DOM and extract values.

### PostgreSQL

A relational database where the cleaned weather data is stored. In this project Postgres plays two roles: it stores Airflow's own internal metadata (DAG runs, task states, logs) AND it stores our pipeline's output in a separate `weather_data` table. This is a common pattern — Airflow needs a backend database to function, and Postgres is the standard choice.

### Docker Compose

Airflow isn't one program — it needs a webserver, a scheduler, and a database all running at the same time. Docker Compose lets you define all of them in a single `docker-compose.yml` file and start them together with one command. Each service runs in its own container and they communicate over Docker's internal network using service names as hostnames (e.g. the Airflow containers reach Postgres at `postgres:5432`).

### XCom (Airflow concept worth knowing)

This is how tasks pass data to each other inside a DAG. Task 1 calls `xcom_push()` to store the scraped data, Task 2 calls `xcom_pull()` to retrieve it. XCom values are stored in Airflow's Postgres metadata database. For large datasets you wouldn't use XCom — you'd write to S3 or a database instead — but for small payloads like this it works fine.

### GitHub Actions

A CI workflow runs on every push to main. It validates that the DAG file has no Python syntax errors and that all imports resolve correctly. Nothing gets deployed — this is just a sanity check to catch broken code before it would cause issues in a real environment.

---

## Project Structure

```
airflow-weather-pipeline/
├── dags/
│   └── weather_dag.py        # The DAG — scrape, transform, load
├── logs/                     # Airflow task logs (gitignored)
├── plugins/                  # Custom operators (empty, for future use)
├── .github/
│   └── workflows/
│       └── ci.yml            # GitHub Actions CI
├── docker-compose.yml        # All services: Airflow + Postgres
├── requirements.txt          # Python dependencies
├── .env                      # AIRFLOW_UID (not committed)
└── .gitignore
```

---

## How to Run

**Prerequisites:** Docker Desktop installed and running.

**1. Clone the repo**

```bash
git clone https://github.com/SharathReddyKottam/airflow-weather-pipeline.git
cd airflow-weather-pipeline
```

**2. Create the `.env` file**

```bash
echo "AIRFLOW_UID=50000" > .env
```

**3. Initialize Airflow (run once)**

```bash
docker-compose up airflow-init
```

Wait until you see `exited with code 0`.

**4. Start all services**

```bash
docker-compose up -d
```

**5. Create the admin user**

```bash
docker exec -it airflow-weather-pipeline-airflow-webserver-1 airflow users create \
  --username airflow \
  --password airflow \
  --firstname Admin \
  --lastname User \
  --role Admin \
  --email admin@example.com
```

**6. Open the Airflow UI**
Go to [http://localhost:8080](http://localhost:8080)
Login: `airflow` / `airflow`

**7. Trigger the DAG**
Find `weather_pipeline` → toggle it ON → click the ▶ Run button

**8. Check the data in Postgres**

```bash
docker exec -it airflow-weather-pipeline-postgres-1 \
  psql -U airflow -d airflow -c "SELECT * FROM weather_data;"
```

---

## Sample Output

```
 id |   city    | temp_c | feels_like_c | humidity |         weather_desc         |         scraped_at
----+-----------+--------+--------------+----------+------------------------------+----------------------------
  1 | New York  |     11 |            9 |       68 | sunny                        | 2026-04-27 14:37:55
  2 | Chicago   |     13 |           11 |       75 | overcast                     | 2026-04-27 14:37:56
  3 | Hyderabad |     32 |           30 |       34 | light rain with thunderstorm | 2026-04-27 14:37:57
  4 | Bangalore |     34 |           32 |       26 | partly cloudy                | 2026-04-27 14:37:57
```

---

## To stop everything

```bash
docker-compose down
```

To also delete the Postgres data volume:

```bash
docker-compose down -v
```

---

## Things to try next

- Add more cities to the `CITIES` list in `weather_dag.py`
- Change `schedule_interval="@hourly"` to `"@daily"` or a cron expression like `"*/10 * * * *"` (every 10 mins)
- Add a 4th task that sends an alert if any city's temperature crosses a threshold
- Swap PostgreSQL for Snowflake or BigQuery as the load target
- Add data quality checks between transform and load using Airflow's `BranchPythonOperator`

