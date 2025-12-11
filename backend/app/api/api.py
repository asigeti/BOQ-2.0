from fastapi import APIRouter
from app.api.endpoints import auth, plans, export, optimization, projects, boq_items, boq_hierarchy

api_router = APIRouter()
api_router.include_router(auth.router, tags=["login"])
api_router.include_router(projects.router, prefix="/projects", tags=["projects"])
api_router.include_router(boq_items.router, prefix="/projects", tags=["boq-items"])
api_router.include_router(boq_hierarchy.router, prefix="/projects", tags=["boq-hierarchy"])
api_router.include_router(plans.router, prefix="/plans", tags=["plans"])
api_router.include_router(export.router, prefix="/export", tags=["export"])
api_router.include_router(optimization.router, prefix="/optimization", tags=["optimization"])
