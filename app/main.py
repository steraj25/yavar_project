from fastapi import FastAPI, HTTPException
import redis
import json
import uvicorn
import logging
import sys

from app.load_data import save_csv_to_redis
app = FastAPI()

# logger
logging.basicConfig(
    filename="app.log",           # log file
    level=logging.INFO,           # log level
    format="%(asctime)s - %(levelname)s - %(message)s",
)

logging.info("Application started")


def init_redis():
    # Try localhost first, otherwise use 'redis' (Docker)
    for host in ["localhost", "redis"]:
        try:
            r = redis.Redis(host=host, port=6379, decode_responses=True)
            r.ping()
            print(f"Connected to Redis at {host}")
            logging.info(f"Connected to Redis at {host}")
            return r
        except:
            pass
    print("Redis not connected  - app exited")
    logging.error("Redis not connected - app exited")
    sys.exit(1)

redis_client = init_redis()


"""Download the CSV from Kaggle and place it in this project directory. This API will read the file and load its contents into Redis"""
@app.api_route("/load_data", methods=["GET", "POST"])
def load_data():
    try:
        file_name = "7210_1.csv"
        count = save_csv_to_redis(file_name, redis_client)
        return {"status": "success", "message": f"Successfully saved {count} items to Redis"}
    except Exception as e:
        logging.error(f"/load_data ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


"""Returns the most recently added item for the given date"""
@app.get("/getRecentItem")
def get_recent_item(date: str):
    try:
        date_key = f"items:date:{date}"

        if not redis_client.exists(date_key):
            raise HTTPException(status_code=404, detail="No items found")

        # Get the most recent item ID for the given date from the sorted set
        item_id = redis_client.zrevrange(date_key, 0, 0)[0]

        # Fetch the full item details
        item = redis_client.hgetall(f"item:{item_id}")

        return {
            "id": item["id"],
            "brand": item["brand"],
            "color": json.loads(item["colors"])
        }
    except Exception as e:
        logging.error(f"/getRecentItem ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


"""Returns brand counts for the given date"""
@app.get("/getBrandsCount")
def get_brands_count(date: str):
    try:
        key = f"count:brand_date:{date}"

        if not redis_client.exists(key):
            raise HTTPException(status_code=404, detail="No brands for this date")

        # Get all brands for the date, sorted by count in descending order
        brands = redis_client.zrevrange(key, 0, -1, withscores=True)

        return [
            {"brand": b, "count": int(c)} for b, c in brands
        ]
    except Exception as e:
        logging.error(f"/getBrandsCount ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))


"""Returns the latest list of items that matches the given color"""
@app.get("/getItemsbyColor")
def items_by_color(color: str):
    try:
        color_key = f"items:color:{color.lower().strip()}"

        if not redis_client.exists(color_key):
            raise HTTPException(status_code=404, detail="No items found for this color")

        # Get the top 10 most recent items matching this color
        item_ids = redis_client.zrevrange(color_key, 0, 9)

        result = []
        for item_id in item_ids:
            # Fetch the full item details for each item
            item = redis_client.hgetall(f"item:{item_id}")
            result.append({
                "id": item["id"],
                "brand": item["brand"],
                "color": json.loads(item["colors"]),
                "date": item["dateAdded"]
            })

        return result
    except Exception as e:
        logging.error(f"/getItemsbyColor ERROR: {e}")
        raise HTTPException(status_code=500, detail=str(e))



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)