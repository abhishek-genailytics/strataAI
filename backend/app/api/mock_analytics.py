from fastapi import APIRouter
from datetime import date, datetime, timedelta
import random

router = APIRouter()

@router.get("/usage-summary")
async def get_mock_usage_summary():
    """Mock usage summary data for dashboard testing"""
    return {
        "total_requests": 1247,
        "total_cost": 23.45,
        "success_rate": 98.2,
        "avg_latency": 245,
        "start_date": (date.today() - timedelta(days=30)).isoformat(),
        "end_date": date.today().isoformat(),
        "days_count": 30
    }

@router.get("/usage-trends")
async def get_mock_usage_trends():
    """Mock usage trends data for dashboard testing"""
    trends = []
    for i in range(7):
        day = date.today() - timedelta(days=6-i)
        trends.append({
            "date": day.isoformat(),
            "requests": random.randint(50, 200),
            "cost": round(random.uniform(1.0, 5.0), 2),
            "errors": random.randint(0, 10),
            "avg_latency": random.randint(200, 400)
        })
    
    return trends

@router.get("/cost-analysis")
async def get_mock_cost_analysis():
    """Mock cost analysis data for dashboard testing"""
    return {
        "total_cost": 23.45,
        "cost_by_provider": [
            {"provider": "openai", "cost": 15.30, "requests": 850, "percentage": 65.2},
            {"provider": "anthropic", "cost": 8.15, "requests": 397, "percentage": 34.8}
        ],
        "cost_by_model": [
            {"model": "gpt-4", "cost": 12.50, "requests": 425},
            {"model": "gpt-3.5-turbo", "cost": 2.80, "requests": 425},
            {"model": "claude-3-sonnet", "cost": 8.15, "requests": 397}
        ],
        "daily_costs": [
            {"date": (date.today() - timedelta(days=6)).isoformat(), "cost": 2.1},
            {"date": (date.today() - timedelta(days=5)).isoformat(), "cost": 3.4},
            {"date": (date.today() - timedelta(days=4)).isoformat(), "cost": 4.2},
            {"date": (date.today() - timedelta(days=3)).isoformat(), "cost": 3.8},
            {"date": (date.today() - timedelta(days=2)).isoformat(), "cost": 4.5},
            {"date": (date.today() - timedelta(days=1)).isoformat(), "cost": 2.9},
            {"date": date.today().isoformat(), "cost": 2.55}
        ]
    }
