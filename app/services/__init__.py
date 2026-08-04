"""Service layer: the only place business rules are allowed to live.

Services receive repositories through FastAPI's `Depends`, never by
instantiating them directly, so the persistence implementation can change
without touching business logic.
"""
