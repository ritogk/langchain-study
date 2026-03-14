"""
LangGraph 分岐パターン学習 API
4つの分岐パターンを実装し、LangSmith でトレーシング・品質評価を行う
"""
import os
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__), "..", ".env"))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from controllers import health_router, patterns_router, eval_router

app = FastAPI(title="LangGraph Branching Patterns", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router, prefix="/api")
app.include_router(patterns_router, prefix="/api")
app.include_router(eval_router, prefix="/api")
