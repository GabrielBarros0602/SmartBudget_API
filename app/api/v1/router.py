"""Aggregates every v1 router behind a single prefix.

Domain routers (transactions, categories, budgets, ...) get included here as
they are built, so `main.py` only ever wires one v1 entry point.
"""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api/v1")
