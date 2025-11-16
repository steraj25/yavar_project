# README

**This project is a FastAPI application that loads shoe data from a CSV file into Redis and provides APIs to query the data by date, brand, and color.**
**The data is indexed using Redis Hashes and Sorted Sets for fast lookup.**

## Setup Instructions
1. **Download** the CSV file from Kaggle and place it in the project directory as `7210_1.csv`.
2. **Start** the FastAPI server.
3. **Call** the `/load_data` endpoint to parse the CSV and save items into Redis.
4. **Use the remaining endpoints** to fetch recent items, brand counts, or items by color.

## Endpoints

### `/load_data`
- Loads the CSV file into Redis.
- Supports GET and POST.

### `/getRecentItem?date=YYYY-MM-DD`
- Returns the most recent item added on the given date.

### `/getBrandsCount?date=YYYY-MM-DD`
- Returns brand counts for the specified date.

### `/getItemsbyColor?color=<color>`
- Returns the latest 10 items that match the given color.

## Redis Data Storage

- **Item Hash** (primary data)
  - `item:<id>`

- **Items by Date (Sorted Set)`
  - `items:date:<date>`

- **Brand Count per Date (Sorted Set)`
  - `count:brand_date:<date>`

- **Items by Color (Sorted Set)`
  - `items:color:<color>`

## Running with Docker

The API will be available at: http://localhost:8000  
Redis will be running at: http://localhost:6379

## Running without Docker

### Install dependencies:
```
pip install -r requirements.txt
```

### Start FastAPI:
```
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## CSV Cleaning Rules

- Removes empty values  
- Skips invalid color fields  
- Removes duplicates  
- Parses timestamps for sorting  

## Files

- app/main.py — FastAPI API  
- app/load_data.py — CSV cleaning and Redis loading  
- docker-compose.yml — Redis + API container orchestration  
- Dockerfile — API container  
- requirements.txt — Project dependencies  
