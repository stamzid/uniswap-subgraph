#!/usr/bin/env python3

import threading
import multiprocessing
from multiprocessing import Pipe
import uvicorn
from fastapi import FastAPI
from strawberry.fastapi import GraphQLRouter
from foundation.schema import chart_schema
from foundation.subgraph_client import SubgraphClient
from foundation.dba import db_manager,  get_latest_timestamp, delete_older_data
from foundation.tokens import supported_tokens
from foundation.utils.logging_utils import service_logger
from foundation.settings import LOOKBACK_DAYS, DATA_POLL_INTERVAL
from datetime import datetime, timedelta
from foundation.settings import PERSISTANCE_MODE

app = FastAPI()

@app.get("/status")
def status():
    return {"status": "Server is running and data is ready."}


graphql_app = GraphQLRouter(chart_schema)
app.include_router(graphql_app, prefix="/graphql")


def data_load(initial: bool = False):
    """
    Loads initial data and starts polling operations for token data updates.
    Description:
        Initializes the GraphQL client, fetches the latest timestamps for tokens, and starts
        fetching and storing token data continuously.
    """
    client = SubgraphClient(db_manager)
    _, ts_data = db_manager.execute_read_without_condition(get_latest_timestamp)

    start_time = int(datetime.timestamp(datetime.utcnow() - timedelta(days=LOOKBACK_DAYS)))
    timestamps = {d["token_id"]: d["latest_unix"] for d in ts_data}
    for token_id in supported_tokens:
        if token_id not in timestamps:
            timestamps[token_id] = start_time

    client.fetch_token(supported_tokens)
    client.fetch_token_hour_datas(timestamps, supported_tokens)
    if PERSISTANCE_MODE is None and initial is False:
        service_logger.info("Deleting data older than %s days", LOOKBACK_DAYS)
        params = {"interval_start": start_time}
        db_manager.execute_write_query(delete_older_data, params)


def schedule_data_load():
    """Schedule data_load to run every 5 minutes."""
    service_logger.info("starting polling.")
    threading.Timer(DATA_POLL_INTERVAL, schedule_data_load).start()


def data_poll(conn):
    """
    Handles the initiation of data operations based on the server's start signal.
    Args:
        conn (multiprocessing.Connection): Connection for communication between processes.
    Description:
        Waits to receive a server start signal through a pipe, then starts scheduled data loading
        tasks and logs the event. Closes the connection after scheduling the tasks.
    """
    server_started = conn.recv()
    if server_started:
        service_logger.info("Server is up, starting data operations...")
        schedule_data_load()
    conn.close()


def run_server(conn):
    """
    Loads data and starts the web server.
    Args:
        conn (multiprocessing.Connection): Connection for communication to signal data loading completion.

    Description:
        Initiates data loading, starts the FastAPI server, and signals the completion of data loading
        to the data polling process. Closes the connection after sending the signal.
    """
    service_logger.info("Populating Data")
    data_load(True)
    service_logger.info("Starting server...")
    uvicorn.run(app, host="0.0.0.0", port=8000)
    conn.send(True)
    conn.close()


if __name__ == "__main__":
    """
    Main execution block to start server and data processes and handle shutdown on KeyboardInterrupt.
    Description:
        Starts the server and data loading processes in parallel using multiprocessing. Joins the
        processes to the main thread and handles graceful shutdown and resource cleanup on interruption.
    """
    try:
        parent_conn, child_conn = Pipe()
        data_process = multiprocessing.Process(target=data_poll, args=(child_conn,))
        data_process.start()

        server_process = multiprocessing.Process(target=run_server, args=(parent_conn,))
        server_process.start()

        server_process.join()
        data_process.join()

    except KeyboardInterrupt:
        service_logger.warning("Shutting down application due to KeyboardInterrupt")
        data_process.terminate()
        server_process.terminate()

        if not parent_conn.closed:
            parent_conn.close()
        if not child_conn.closed:
            child_conn.close()
