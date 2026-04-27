from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import requests
from bs4 import BeautifulSoup
import psycopg2
import json

# --- Config ---
CITIES = ["New York", "Chicago", "Hyderabad", "Bangalore"]

DB_CONN = {
    "host": "postgres",
    "database": "airflow",
    "user": "airflow",
    "password": "airflow",
    "port": 5432
}

# --- Default args for the DAG ---
default_args = {
    "owner": "sharath",
    "retries": 1,
    "retry_delay": timedelta(minutes=2),
}

# --- Task 1: Scrape weather ---
def scrape_weather(**context):
    results = []
    for city in CITIES:
        url = f"https://wttr.in/{city.replace(' ', '+')}?format=j1"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        current = data["current_condition"][0]
        results.append({
            "city": city,
            "temp_c": current["temp_C"],
            "feels_like_c": current["FeelsLikeC"],
            "humidity": current["humidity"],
            "weather_desc": current["weatherDesc"][0]["value"],
            "scraped_at": datetime.utcnow().isoformat()
        })
    
    # Pass data to next task via XCom (Airflow's way of sharing data between tasks)
    context["ti"].xcom_push(key="weather_data", value=results)
    print(f"Scraped {len(results)} cities successfully")

# --- Task 2: Transform data ---
def transform_data(**context):
    raw = context["ti"].xcom_pull(key="weather_data", task_ids="scrape_weather")
    
    transformed = []
    for row in raw:
        transformed.append({
            "city": row["city"],
            "temp_c": int(row["temp_c"]),
            "feels_like_c": int(row["feels_like_c"]),
            "humidity": int(row["humidity"]),
            "weather_desc": row["weather_desc"].strip().lower(),
            "scraped_at": row["scraped_at"]
        })
    
    context["ti"].xcom_push(key="transformed_data", value=transformed)
    print(f"Transformed {len(transformed)} rows")

# --- Task 3: Load to Postgres ---
def load_to_postgres(**context):
    data = context["ti"].xcom_pull(key="transformed_data", task_ids="transform_data")
    
    conn = psycopg2.connect(**DB_CONN)
    cursor = conn.cursor()
    
    # Create table if it doesn't exist
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS weather_data (
            id SERIAL PRIMARY KEY,
            city VARCHAR(100),
            temp_c INTEGER,
            feels_like_c INTEGER,
            humidity INTEGER,
            weather_desc VARCHAR(200),
            scraped_at TIMESTAMP
        )
    """)
    
    # Insert rows
    for row in data:
        cursor.execute("""
            INSERT INTO weather_data 
            (city, temp_c, feels_like_c, humidity, weather_desc, scraped_at)
            VALUES (%s, %s, %s, %s, %s, %s)
        """, (
            row["city"], row["temp_c"], row["feels_like_c"],
            row["humidity"], row["weather_desc"], row["scraped_at"]
        ))
    
    conn.commit()
    cursor.close()
    conn.close()
    print(f"Loaded {len(data)} rows into postgres")

# --- Define the DAG ---
with DAG(
    dag_id="weather_pipeline",
    default_args=default_args,
    description="Scrape weather for US + India cities and store in Postgres",
    schedule_interval="@hourly",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    tags=["weather", "etl", "portfolio"]
) as dag:

    task1 = PythonOperator(
        task_id="scrape_weather",
        python_callable=scrape_weather,
    )

    task2 = PythonOperator(
        task_id="transform_data",
        python_callable=transform_data,
    )

    task3 = PythonOperator(
        task_id="load_to_postgres",
        python_callable=load_to_postgres,
    )

    # Define order
    task1 >> task2 >> task3