#!/usr/bin/env python3

import os


TRANSPORT_URL = os.getenv("TRANSPORT_URL", "https://api.thegraph.com/subgraphs/name/uniswap/uniswap-v3")

DB_HOST = os.getenv("DB_HOST", "foundation_postgres")
DB_PORT = os.getenv("DB_PORT", 5432)
DB_USER = os.getenv("DB_USER", "foundation")
DB_PASS = os.getenv("DB_PASS", "foundation")
DB_NAME = os.getenv("DB_NAME", "foundation")
DB_SCHEMA = os.getenv("DB_SCHEMA", "foundation")

MIN_CONN = int(os.getenv("MINIMUM_DB_CONNECTIONS", 16))
MAX_CONN = int(os.getenv("MAXIMUM_DB_CONNECTIONS", 1024))

LOOKBACK_DAYS = os.getenv("LOOBACK_DAYS", 7)
DATA_POLL_INTERVAL = os.getenv("DATA_POLL_INTERVAL", 300)
PERSISTANCE_MODE = os.getenv("PERSISTANCE_MODE")
