"""Local-dev sink mirroring the prod Pub/Sub → BigQuery subscription.

Pulls from `swipe-events-sub` on the local Pub/Sub emulator and writes each
envelope into the local BigQuery emulator (raw.swipes_raw), matching the
column shape of the prod table. Also appends to a JSONL file so you can
inspect rows without going through BQ.
"""

import json
import logging
import os
import signal
import sys
import time
from pathlib import Path

import google.auth.credentials
from google.api_core import exceptions
from google.api_core.client_options import ClientOptions
from google.cloud import bigquery, pubsub_v1

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("pubsub-bq-sink")

PROJECT = os.environ["GOOGLE_CLOUD_PROJECT"]
TOPIC = os.environ.get("PUBSUB_TOPIC", "swipe-events")
SUBSCRIPTION = os.environ.get("PUBSUB_SUBSCRIPTION", "swipe-events-sub")
OUTPUT_PATH = Path(os.environ.get("OUTPUT_PATH", "/data/swipes_raw.jsonl"))

BQ_ENDPOINT = os.environ.get("BIGQUERY_API_ENDPOINT")
BQ_DATASET = os.environ.get("BIGQUERY_DATASET", "raw")
BQ_TABLE = os.environ.get("BIGQUERY_TABLE", "swipes_raw")


def make_bq_client() -> bigquery.Client | None:
    if not BQ_ENDPOINT:
        log.warning("BIGQUERY_API_ENDPOINT not set; BQ writes disabled")
        return None
    creds = google.auth.credentials.AnonymousCredentials()
    client = bigquery.Client(
        project=PROJECT,
        credentials=creds,
        client_options=ClientOptions(api_endpoint=BQ_ENDPOINT),
    )
    table_ref = f"{PROJECT}.{BQ_DATASET}.{BQ_TABLE}"
    log.info("BQ sink target: %s via %s", table_ref, BQ_ENDPOINT)
    return client


def ensure_subscription() -> str:
    subscriber = pubsub_v1.SubscriberClient()
    sub_path = subscriber.subscription_path(PROJECT, SUBSCRIPTION)
    topic_path = subscriber.topic_path(PROJECT, TOPIC)
    try:
        subscriber.create_subscription(name=sub_path, topic=topic_path)
        log.info("created subscription %s", sub_path)
    except exceptions.AlreadyExists:
        log.info("subscription %s already exists", sub_path)
    subscriber.close()
    return sub_path


def callback_factory(sub_path: str, bq_client: bigquery.Client | None):
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    fh = OUTPUT_PATH.open("a", buffering=1)
    table_ref = f"{PROJECT}.{BQ_DATASET}.{BQ_TABLE}" if bq_client else None

    def _cb(message: pubsub_v1.subscriber.message.Message) -> None:
        row = {
            "subscription_name": sub_path,
            "message_id": message.message_id,
            "publish_time": message.publish_time.isoformat() if message.publish_time else None,
            "data": message.data.decode("utf-8", errors="replace"),
            "attributes": json.dumps(dict(message.attributes)),
        }
        fh.write(json.dumps(row) + "\n")
        if bq_client is not None:
            try:
                errors = bq_client.insert_rows_json(table_ref, [row])
                if errors:
                    log.error("BQ insert errors id=%s errors=%s", row["message_id"], errors)
            except Exception:
                log.exception("BQ insert failed id=%s", row["message_id"])
        log.info("sink row id=%s data=%s", row["message_id"], row["data"])
        message.ack()

    return _cb


def main() -> None:
    bq_client = make_bq_client()
    sub_path = ensure_subscription()
    subscriber = pubsub_v1.SubscriberClient()
    future = subscriber.subscribe(sub_path, callback=callback_factory(sub_path, bq_client))
    log.info("listening on %s → %s + BQ", sub_path, OUTPUT_PATH)

    def _shutdown(*_):
        log.info("shutdown requested")
        future.cancel()
        future.result()
        sys.exit(0)

    signal.signal(signal.SIGTERM, _shutdown)
    signal.signal(signal.SIGINT, _shutdown)

    try:
        future.result()
    except Exception:
        log.exception("subscriber error; restarting in 3s")
        time.sleep(3)
        main()


if __name__ == "__main__":
    main()
