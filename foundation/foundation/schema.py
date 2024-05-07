#!/usr/bin/env python3

import strawberry
from datetime import datetime
from psycopg2 import sql
from typing import List
from foundation.dba import db_manager
from foundation.tokens import supported_tokens


symbol_map = {v: k for k, v in supported_tokens.items()}

def fetch_chart_data(token_symbol: str, time_unit_in_hours: int):
    interval = time_unit_in_hours * 3600
    token_id = symbol_map.get(token_symbol)
    if not token_id:
        return 0, []

    query = sql.SQL("""
        SELECT
            MIN(timestamp) AS interval_start,
            array_agg(open ORDER BY timestamp) AS opens,
            array_agg(close ORDER BY timestamp DESC) AS closes,
            MAX(high) AS max_high,
            MIN(low) AS min_low,
            AVG(price_usd) AS avg_price_usd
        FROM
            foundation.token_hours_data
        WHERE
            token_id = %(token_id)s
        GROUP BY
            FLOOR(EXTRACT(EPOCH FROM timestamp) / %(interval)s)
        ORDER BY
            interval_start
    """)

    params = {"interval": interval, "token_id": token_id}
    return db_manager.execute_read_query(query, params)


def format_chart_data(data: List[dict]):
    opens = []
    closes = []
    highs = []
    lows = []
    priceUSDs = []

    for record in data:
        time_str = record['interval_start'].strftime('%Y-%m-%dT%H:%M:%S')
        opens.append([time_str, "open", record['opens'][0] if record['opens'] else 0])
        closes.append([time_str, "close", record['closes'][0] if record['closes'] else 0])
        highs.append([time_str, "high", record.get('max_high', 0)])
        lows.append([time_str, "low", record.get('min_low', 0)])
        priceUSDs.append([time_str, "priceUSD", record.get('avg_price_usd', 0)])

    formatted_data = [opens, closes, highs, lows, priceUSDs]
    return formatted_data


@strawberry.type
class PricePoint:
    time: str
    price_type: str
    value: float


@strawberry.type
class Query:
    @strawberry.field
    def get_chart_data(self, token_symbol: str, time_unit_in_hours: int) -> List[List[PricePoint]]:
        _, data = fetch_chart_data(token_symbol, time_unit_in_hours)
        formatted_data = format_chart_data(data)
        return [
            [PricePoint(time=point[0], price_type=point[1], value=point[2]) for point in group]
            for group in formatted_data
        ]


chart_schema = strawberry.Schema(query=Query)
