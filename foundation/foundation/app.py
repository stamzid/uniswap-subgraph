#!/usr/bin/env python3

from foundation.subgraph_client import SubgraphClient
from foundation.dba import DatabaseManager, db_manager, get_latest_timestamp
from foundation.utils.logging_utils import service_logger
from foundation.tokens import supported_tokens
from foundation.schema import chart_schema

from datetime import datetime, timedelta
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import uvicorn
import foundation.settings as Settings


server = FastAPI()
graphql_app = GraphQLRouter(chart_schema)

server.include_router(graphql_app, prefix="/graphql")

@server.get("/")
def status():
    return {"status": "ok"}


def graph_client_runner(dba: DatabaseManager):
    client = SubgraphClient(dba)
    _, ts_data = dba.execute_read_without_condition(get_latest_timestamp)

    start_time = int(datetime.timestamp((datetime.utcnow() - timedelta(days=Settings.LOOKBACK_DAYS))))
    timestamps = {d["token_id"]: d["latest_unix"] for d in ts_data}
    for token_id in supported_tokens:
        if token_id not in timestamps:
            timestamps[token_id] = start_time

    client.fetch_token(supported_tokens)
    client.fetch_token_hour_datas(timestamps, supported_tokens)


def main():
    # Setup GraphQL

    # Setup Scheduler
    scheduler = AsyncIOScheduler()
    scheduler.add_job(lambda: graph_client_runner(db_manager), 'interval', minutes=5)
    scheduler.start()

    # Run FastAPI app
    uvicorn.run(server, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    main()
