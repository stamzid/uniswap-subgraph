#!/bin/bash

alembic upgrade head
python -m foundation.app
