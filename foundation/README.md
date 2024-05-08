# Overview
This document provides instructions on how to run the application using Docker, and how to query the GraphQL API to fetch chart data for cryptocurrency tokens.

## Prerequisites
* Docker
* docker-compose
* poetry (optional)
* python 3.11 (optional)

Having poetry python will allow the user to run some unittest and gql test incase they don't have the gql clients

# Setup and Running
## Starting the Application with docker
Run the application using Docker Compose:

```sh
docker-compose up -d
```

This command will start all required services in detached mode. In case the user wants to run the program from command line, then start the database first and then run the shell commands in project root. For example:
```sh
docker-compose up -d postgres
poetry shell
poetry install
alembic upgrade head
python -m foundation.app
```

## Supported Tokens

At the moment tokens are added to the `foundation/tokens.py` file in a dictionary with their `token_id` and `symbol`. If the user wants to add support more tokens, simply add the `token_id` and `symbol` to the existing dictionary and rebuild the docker image. For example:
```sh
docker build . -t foundation:latest
```
## Environment Variables

All environment variables are using defaul values at the moment. Most of them are self explanatory (i.e. DB variables). Following contains the significance of less obvious ones:

* MIN_CONN: Minimum number of connections in DB connection pool.
* MAX_CONN: Maximum number of connections in DB connection pool.
* LOOKBACK_DAYS: How many days of data to include in query, by default it's 7 days as per requirements.
* DATA_POLL_INTERVAL: How often data is being polled, at this moment it's every 5 minutes.
* PERSISTANCE_MODE: Whether to keep or delete the data older than DATA_POLL_INTERVAL. Default is "DELETE", any other value will persist the data.

## Querying the GraphQL API
You can access the GraphQL API to fetch data once the application is up. Here is how you can query chart data for the "Wrapped Bitcoin (WBTC)" token over specified time intervals.

### Example GraphQL Query
Use a GraphQL client or a tool like Postman or GraphiQL to execute the following query:

```graphql
query GetChartData {
  getChartData(tokenSymbol: "WBTC", timeUnitInHours: 2) {
    tokenMetadata {
      id
      name
      symbol
      totalSupply
      volumeUsd
      decimals
    }
    candles {
      time
      priceType
      value
    }
  }
}
```


### Example Responses

#### When Data is Available
If there is data available for the WBTC token, the response might look like this:

```json
{
  "data": {
    "getChartData": {
      "tokenMetadata": {
        "id": "0x2260fac5e5542a773aa44fbcfedf7c193bc2c599",
        "name": "Wrapped BTC",
        "symbol": "WBTC",
        "totalSupply": "18700000",
        "volumeUsd": "7200000000",
        "decimals": "8"
      },
      "candles": [
        [
          {
            "time": "2024-01-01T00:00:00",
            "priceType": "open",
            "value": 50000
          },
          {
            "time": "2024-01-01T02:00:00",
            "priceType": "close",
            "value": 50500
          },
          {
            "time": "2024-01-01T02:00:00",
            "priceType": "high",
            "value": 51000
          },
          {
            "time": "2024-01-01T00:00:00",
            "priceType": "low",
            "value": 49500
          },
          {
            "time": "2024-01-01T01:00:00",
            "priceType": "priceUSD",
            "value": 50250
          }
        ]
      ]
    }
  }
}
```

#### When No Data is Available
If no data is available for the specified interval, the response would look like this:

```json
{
    "data": {
        "getChartData": {
            "tokenMetadata": {
                "id": "",
                "name": "",
                "symbol": "",
                "totalSupply": "",
                "volumeUsd": "",
                "decimals": ""
            },
            "candles": [
                [
                    {
                        "time": "",
                        "priceType": "open",
                        "value": 0
                    },
                    {
                        "time": "",
                        "priceType": "close",
                        "value": 0
                    },
                    {
                        "time": "",
                        "priceType": "high",
                        "value": 0
                    },
                    {
                        "time": "",
                        "priceType": "low",
                        "value": 0
                    },
                    {
                        "time": "",
                        "priceType": "priceUSD",
                        "value": 0
                    }
                ]
            ]
        }
    }
}
```

This documentation ensures you have a clear understanding of how to start the application and interact with the GraphQL API, including handling scenarios where no data is available.

## Testing

Testing the application involves both unit tests for isolated components and end-to-end tests to verify the overall functionality. Unittests are focusing on function without external dependencies. Due to the nature of the program, there's only a handful of such functions.

### Prerequisites for Testing
Ensure that all dependencies are installed and that you are operating within the virtual environment managed by Poetry:

```sh
# Activate the Poetry shell
poetry shell
```

### Install dependencies
```sh
poetry install
```

### Running Unit Tests
Unit tests are designed to test isolated helper functions without requiring access to the database or external APIs:

```sh
# Run unit tests
python -m unittest tests.test_helpers
```
### Running End-to-End Tests

End-to-end tests require that the application be running within the Docker environment with docker compose. Ensure both application and db container is up and running. These tests check the full functionality from the GraphQL endpoint through to the database by leveraging pytest:

```sh
# Ensure the application is running
docker-compose ps

# Run end-to-end tests
poetry run pytest tests/test_endpoint.py
```

These tests will validate the integration between various components and ensure that the system behaves as expected.


Sure, I'll condense the design decision section into a more concise format:

## Design Decisions
### Language and Database

* Python: Foundation stack has python and it is also one of my primary languages (other being Scala)
* PostgreSQL: The data we're dealing with is structured and python has great ORM framework and library for Postgres. Also provides fast read access for complex queries

### Frameworks

* FastAPI: I chose this mainly for asynchronouse request handling and it runs perfectly with ASGI web server implementation. It's also highly performant compared to other frameworks I used such as Flask and Django.
* Strawberry GraphQL: Main reason is it is the recommeded graphQL framework for FastAPI with seamless integration and simplifies creating strongly-typed APIs in a Pythonic way. 

### Virtual Environment and Packaging
* Poetry: Handles dependency management and packaging. It simplifies the management of project dependencies and virtual environments.
* Docker: Ease of containerization and power of docker compose for local developments. The images are platform independent and one of the mainstays of CI/CD practices.

### Testing
Mainly leveraged popular python testing libraries for both unittest and integration testing.

## Reflection

### What Went Well
Overall I felt the tools I chose and the way I designed the backend API and Database manager went well for the implementation. Using Strawberry with FastAPI made it very easy to handle the server and gql client is a breeze to use with subgraphs.

### What Could Have Gone Better
I think initial time I spent on experimenting with Graphene to build the server could be avoided. I went with most number of github stars without checking FastAPI doc which clearly favours Strawberry. Although both are on the recommended libraries on graphql website. In addition, I think the polling algorithm can be improved while scaling. One way would be to have two polling interval for two different kind of data we are fetching with `token` and `tokenHourDatas`.

### Future Improvement
Depending on the scope, I would probably add an endpoint to add additional token support dynamically. At the moment, it requires a rebuilding of the image which doesn't take long time because of how I designed the docker file with caching but still with an endpoint we could avoid this step. The other thing is I would spend a little more time trying to find more edge cases / data load.


