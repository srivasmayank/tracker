from decimal import Decimal
from typing import Dict, List
from fastapi import APIRouter, Query, status
from pydantic import BaseModel, Field

from app.services.fx_service import default_fx_service

router = APIRouter(prefix="/fx", tags=["Foreign Exchange (FX) & Currencies"])


class CurrencyConversionResponse(BaseModel):
    original_amount: Decimal
    from_currency: str
    to_currency: str
    exchange_rate: Decimal
    converted_amount: Decimal


class SupportedCurrenciesResponse(BaseModel):
    currencies: List[str]


@router.get("/currencies", response_model=SupportedCurrenciesResponse)
def get_supported_currencies():
    """Returns the list of supported ISO 4217 currency symbols."""
    return SupportedCurrenciesResponse(
        currencies=default_fx_service.get_supported_currencies()
    )


@router.get("/rates", response_model=Dict[str, Decimal])
def get_exchange_rates(
    base: str = Query("USD", min_length=3, max_length=3, description="Base currency to fetch rates against")
):
    """
    Returns real-time or cached benchmark exchange rates relative to the requested base currency.
    Employs triangulation across reference currencies.
    """
    return default_fx_service.get_all_rates(base_currency=base)


@router.get("/convert", response_model=CurrencyConversionResponse)
def convert_currency(
    amount: Decimal = Query(..., gt=0, description="Amount in source currency"),
    from_currency: str = Query(..., min_length=3, max_length=3, description="Source currency code (e.g. EUR)"),
    to_currency: str = Query(..., min_length=3, max_length=3, description="Target currency code (e.g. USD)"),
):
    """
    Converts a monetary amount between any two supported currencies with Decimal precision.
    """
    converted_amount, rate = default_fx_service.convert(
        amount=amount,
        from_curr=from_currency,
        to_curr=to_currency
    )
    return CurrencyConversionResponse(
        original_amount=amount,
        from_currency=from_currency.upper().strip(),
        to_currency=to_currency.upper().strip(),
        exchange_rate=rate,
        converted_amount=converted_amount
    )
