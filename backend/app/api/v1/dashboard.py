from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException
from typing import Dict, Any
from app.services.cache import get_revenue_summary
from app.core.auth import authenticate_request as get_current_user

# Amounts are NUMERIC(10, 3) in the database, so a total can carry a third decimal. Rounding to cents happens here, once, with an explicit rounding mode - never implicitly via binary float.
CENTS = Decimal("0.01")

router = APIRouter()

@router.get("/dashboard/summary")
async def get_dashboard_summary(
    property_id: str,
    current_user: dict = Depends(get_current_user)
) -> Dict[str, Any]:
    
    tenant_id = getattr(current_user, "tenant_id", "default_tenant") or "default_tenant"
    
    revenue_data = await get_revenue_summary(property_id, tenant_id)

    # Money stays a Decimal, and is serialised as a string. Converting to float here would put the amount into binary floating point, which cannot represent most decimal fractions exactly.
    total_revenue = Decimal(revenue_data['total'])
    total_rounded = total_revenue.quantize(CENTS, rounding=ROUND_HALF_UP)

    return {
        "property_id": revenue_data['property_id'],
        # Exact value, to full stored precision, for any further arithmetic.
        "total_revenue": str(total_revenue),
        # Pre-rounded for display, so the client never does money maths.
        "total_revenue_display": str(total_rounded),
        # True when rounding to cents discarded a sub-cent remainder.
        "rounding_applied": total_rounded != total_revenue,
        "currency": revenue_data['currency'],
        "reservations_count": revenue_data['count']
    }
