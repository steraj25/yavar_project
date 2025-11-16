import logging

import pandas as pd
import json
from datetime import datetime


def clear_existing_data(redis_client):
    redis_client.flushdb()
    logging.info("Redis database fully cleared")


def parse_colors(color_string):
    try:
        return json.loads(color_string)
    except:
        return [color.strip() for color in color_string.split(',') if color.strip()]

import os
def load_and_clean_csv(csv_path: str):
    df = pd.read_csv(csv_path, dtype=str, usecols=["id", "brand", "colors", "dateAdded"])

    # Remove empty values
    df.replace("", None, inplace=True)
    df.dropna(inplace=True)

    # Remove rows where colors is only ","
    df = df[df["colors"].str.strip() != ","]

    # Remove duplicates
    df.drop_duplicates(inplace=True)

    # save cleaned data if required
    # df.to_excel("cleaned_data.xlsx")
    return df


def save_csv_to_redis(csv_path: str, redis_client):
    logging.info("Loading CSV...")
    df = load_and_clean_csv(csv_path)
    total = len(df)
    logging.info(f"Total valid rows: {total}")

    logging.info("Flushing Redis...")
    clear_existing_data(redis_client)

    count = 0
    # Pipeline with batch processing for high-performance bulk operations
    batch_size = 1000
    pipeline = redis_client.pipeline()

    for _, row in df.iterrows():

        item_id = row["id"]
        brand = row["brand"]
        # parse if multiple colours are present
        colors = parse_colors(row["colors"])
        date_added = row["dateAdded"]

        # Parse timestamp
        date_obj = datetime.fromisoformat(date_added.replace('Z', '+00:00'))
        date_only = date_obj.date().isoformat()
        timestamp = date_obj.timestamp()


        item_key = f"item:{item_id}"
        item_data = {
            'id': item_id,
            'brand': brand,
            'colors': json.dumps(colors),
            'dateAdded': date_added,
        }

        # Save each field of the item into the Redis Hash (primary data)
        for field, value in item_data.items():
            pipeline.hset(item_key, field, value)

        # Add item to a date-based Sorted Set (score = timestamp)
        pipeline.zadd(f"items:date:{date_only}", {item_id: timestamp})

        # Increment brand count in a brand-per-date Sorted Set (score = count)
        pipeline.zincrby(f"count:brand_date:{date_only}", 1, brand)

        # For each color, add the item to a color-based Sorted Set (score = timestamp)
        for color in colors:
            color_clean = color.lower().strip()
            if color_clean:
                pipeline.zadd(f"items:color:{color_clean}", {item_id: timestamp})

        count += 1

        # Execute batch
        if count % batch_size == 0 or count == total:
            pipeline.execute()
            logging.info(f"Inserted {count}/{total}...")
            pipeline = redis_client.pipeline()

    logging.info(f"Successfully inserted {count} items into Redis.")
    return count



