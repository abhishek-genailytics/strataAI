from __future__ import annotations
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP, getcontext
from typing import Dict, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from time import time
from functools import lru_cache

from app.core.supabase import get_supabase_service
from app.models.openai_chat import ChatCompletionUsage

getcontext().prec = 28  # high precision for currency math

TOKENS_PER_BILLING_UNIT = Decimal(1000)  # unit=token is priced per 1K tokens

@dataclass(frozen=True)
class PricingRow:
    pricing_type: str          # "input" | "output" | "per_request"
    price_per_unit: Decimal    # currency / unit
    unit: str                  # "token" | "request"
    currency: str              # e.g. "USD"
    region: str                # e.g. "global"

@dataclass(frozen=True)
class CostBreakdown:
    currency: str
    input_cost: Decimal
    output_cost: Decimal
    request_cost: Decimal
    total_cost: Decimal

def _select_effective(rows: List[Dict], region: Optional[str]) -> List[PricingRow]:
    """Filter by region match else 'global', prefer exact first."""
    now = datetime.now(timezone.utc).isoformat()
    region_pref = (region or "").lower()
    
    def effective(r):
        ef = r.get("effective_from")
        eu = r.get("effective_until")
        # simple string compare ok for ISO; DB should handle filtering ideally
        return (not eu or eu >= now) and (not ef or ef <= now) and (r.get("is_active", True))

    # Exact-region rows first, then global
    sel = [r for r in rows if effective(r) and str(r.get("region","")).lower() == region_pref]
    if not sel:
        sel = [r for r in rows if effective(r) and str(r.get("region","")).lower() == "global"]

    out: List[PricingRow] = []
    for r in sel:
        out.append(PricingRow(
            pricing_type=str(r["pricing_type"]),
            price_per_unit=Decimal(str(r["price_per_unit"])),
            unit=str(r["unit"]),
            currency=str(r.get("currency","USD")),
            region=str(r.get("region","global")),
        ))
    return out

def _group_by_type(rows: List[PricingRow]) -> Dict[str, PricingRow]:
    """Latest row per type wins (DB can also order by updated_at desc/ effective_from desc)"""
    d: Dict[str, PricingRow] = {}
    for r in rows:
        d[r.pricing_type] = r
    return d

# Optional in-process cache for pricing data
_CACHE_TTL_S = 300

class _TimedCache:
    def __init__(self):
        self._store = {}
    
    def get(self, key):
        v = self._store.get(key)
        if v and v[1] > time():
            return v[0]
        return None
    
    def set(self, key, value):
        self._store[key] = (value, time() + _CACHE_TTL_S)

_pricing_cache = _TimedCache()

def clear_pricing_cache():
    """Clear the pricing cache - useful for testing."""
    global _pricing_cache
    _pricing_cache._store.clear()

def load_pricing_for_model(model_id: UUID, region: Optional[str] = None) -> Dict[str, PricingRow]:
    """Fetch live pricing for a model from model_pricing."""
    key = (str(model_id), (region or "global").lower())
    cached = _pricing_cache.get(key)
    if cached:
        return cached
    
    sb = get_supabase_service()
    resp = sb.table("model_pricing")\
        .select("pricing_type, price_per_unit, unit, currency, region, effective_from, effective_until, is_active, updated_at")\
        .eq("model_id", str(model_id))\
        .order("effective_from", desc=True)\
        .limit(12)\
        .execute()
    
    rows = resp.data or []
    eff = _select_effective(rows, region)
    grouped = _group_by_type(eff)
    
    _pricing_cache.set(key, grouped)
    return grouped

def _money(x: Decimal) -> Decimal:
    """Round to 6 decimal places for sub-cent precision, banker-friendly."""
    return x.quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)

def compute_cost(
    *,
    usage: ChatCompletionUsage,
    model_id: UUID,
    region: Optional[str] = None,
) -> CostBreakdown:
    """Compute cost breakdown from usage and model pricing."""
    pricing = load_pricing_for_model(model_id, region=region)

    currency = "USD"
    input_cost = Decimal(0)
    output_cost = Decimal(0)
    request_cost = Decimal(0)

    # input tokens
    if "input" in pricing:
        pr = pricing["input"]
        currency = pr.currency or currency
        if pr.unit == "token":
            units = Decimal(usage.prompt_tokens) / TOKENS_PER_BILLING_UNIT
        elif pr.unit == "request":
            units = Decimal(1)
        else:
            units = Decimal(0)
        input_cost = pr.price_per_unit * units

    # output tokens
    if "output" in pricing:
        pr = pricing["output"]
        currency = pr.currency or currency
        if pr.unit == "token":
            units = Decimal(usage.completion_tokens) / TOKENS_PER_BILLING_UNIT
        elif pr.unit == "request":
            units = Decimal(1)
        else:
            units = Decimal(0)
        output_cost = pr.price_per_unit * units

    # per-request
    if "per_request" in pricing:
        pr = pricing["per_request"]
        currency = pr.currency or currency
        units = Decimal(1)  # one request
        request_cost = pr.price_per_unit * units

    total = input_cost + output_cost + request_cost

    return CostBreakdown(
        currency=currency,
        input_cost=_money(input_cost),
        output_cost=_money(output_cost),
        request_cost=_money(request_cost),
        total_cost=_money(total),
    )
