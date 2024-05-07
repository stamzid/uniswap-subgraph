#!/usr/bin/env python3

import json
import time
import datetime

from gql import gql, Client
from gql.transport.aiohttp import AIOHTTPTransport
from foundation.settings import TRANSPORT_URL
from foundation.utils.logging_utils import service_logger
from foundation.dba import DatabaseManager, insert_token_hour_sql, insert_token_sql


class SubgraphClient:
    def __init__(self, dba: DatabaseManager):
        transport = AIOHTTPTransport(url=TRANSPORT_URL)
        self.client = Client(transport=transport, fetch_schema_from_transport=True)
        self.dba = dba

    def add_symbol(self, data: list[dict], tokens: dict[str]):
        for entry in data:
            entry_token_id = entry["id"].split("-")[0]
            entry["id"] = entry_token_id
            entry["symbol"] = tokens[entry_token_id]
            entry["timestamp"] = datetime.datetime.utcfromtimestamp(entry["periodStartUnix"]).strftime("%Y-%m-%dT%H:%M:%S")

    def fetch_token_hour_datas(self, timestamps: dict[int], tokens: dict[str]):
        for token_id in timestamps:
            current_timestamp = timestamps[token_id]
            while True:
                query = gql(f"""
                    {{
                        tokenHourDatas(first: 100, where: {{token: "{token_id}", periodStartUnix_gt: {current_timestamp}}}) {{
                            id
                            periodStartUnix
                            open
                            close
                            high
                            low
                            priceUSD
                        }}
                    }}
                """)

                try:
                    response = self.client.execute(query)
                    data = response.get('tokenHourDatas', [])
                    if not data:
                        break

                    new_timestamp = max(data, key=lambda x: x['periodStartUnix'])['periodStartUnix']

                    # Ensure to update the timestamp only if new data was fetched
                    if new_timestamp > current_timestamp:
                        timestamps[token_id] = new_timestamp
                        current_timestamp = new_timestamp

                    self.add_symbol(data, tokens)
                    self.dba.execute_batch_insert(insert_token_hour_sql, data)
                except KeyError as e:
                    service_logger.error("Error processing gql response %s", e)
                except Exception as e:
                    service_logger.error(e)

        return timestamps

    def fetch_token(self, tokens: dict):
        token_ids = list(tokens.keys())
        token_ids_json = json.dumps(token_ids)

        # Construct the GraphQL query
        query = gql(f"""
            {{
                tokens(where: {{id_in: {token_ids_json}}}) {{
                    id,
                    name,
                    symbol,
                    totalSupply,
                    volumeUSD,
                    decimals
                }}
            }}
        """)

        try:
            response = self.client.execute(query)
            data = response.get('tokens', [])
            self.dba.execute_batch_insert(insert_token_sql, data)
        except Exception as e:
            service_logger.error(e)
