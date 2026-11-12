from abc import ABC, abstractmethod
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Dict, List, Optional, Tuple


class ExchangeRateProvider(ABC):
    """
    Abstract Adapter Interface for foreign exchange rate providers.
    Adheres to:
    - Open/Closed Principle (OCP): New bank/commercial providers (e.g., ECB, OpenExchangeRates,
      Wise) can be introduced without modifying core application code.
    - Liskov Substitution Principle (LSP): Any provider implementation can be substituted transparently.
    """

    @abstractmethod
    def get_rates(self, base_currency: str = "USD") -> Dict[str, Decimal]:
        """Fetch all exchange rates relative to the requested base currency."""
        pass

    @abstractmethod
    def get_rate(self, from_curr: str, to_curr: str) -> Decimal:
        """Fetch or triangulate the exchange rate between two currencies."""
        pass


class FallbackStaticFXAdapter(ExchangeRateProvider):
    """
    Highly reliable, zero-network-dependency benchmark FX provider.
    Provides benchmark exchange rates pegged against USD with full triangulation support.
    """

    # Realistic benchmark rates relative to 1.0 USD
    DEFAULT_RATES_USD: Dict[str, Decimal] = {
        "USD": Decimal("1.000000"),
        "EUR": Decimal("0.920000"),
        "GBP": Decimal("0.790000"),
        "INR": Decimal("84.500000"),
        "CAD": Decimal("1.380000"),
        "AUD": Decimal("1.520000"),
        "JPY": Decimal("152.000000"),
        "CHF": Decimal("0.880000"),
        "SGD": Decimal("1.320000"),
        "AED": Decimal("3.672500"),
    }

    def __init__(self, custom_rates: Optional[Dict[str, Decimal]] = None):
        self.rates = custom_rates or self.DEFAULT_RATES_USD.copy()

    def get_rates(self, base_currency: str = "USD") -> Dict[str, Decimal]:
        base = base_currency.upper().strip()
        if base not in self.rates:
            raise ValueError(f"Unsupported base currency '{base}'. Supported: {list(self.rates.keys())}")

        base_in_usd = self.rates[base]
        converted_rates: Dict[str, Decimal] = {}
        for curr, rate_in_usd in self.rates.items():
            # Triangulation: rate(Base -> Curr) = rate(USD -> Curr) / rate(USD -> Base)
            rate = (rate_in_usd / base_in_usd).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
            converted_rates[curr] = rate

        return converted_rates

    def get_rate(self, from_curr: str, to_curr: str) -> Decimal:
        f_curr = from_curr.upper().strip()
        t_curr = to_curr.upper().strip()

        if f_curr == t_curr:
            return Decimal("1.000000")

        if f_curr not in self.rates:
            raise ValueError(f"Currency '{f_curr}' is not supported.")
        if t_curr not in self.rates:
            raise ValueError(f"Currency '{t_curr}' is not supported.")

        # Triangulation formula: Rate(From -> To) = Rate(USD -> To) / Rate(USD -> From)
        rate = (self.rates[t_curr] / self.rates[f_curr]).quantize(Decimal("0.000001"), rounding=ROUND_HALF_UP)
        return rate


class CachedFXProvider(ExchangeRateProvider):
    """
    Decorator pattern caching exchange rates in memory to reduce downstream network/computation overhead.
    """

    def __init__(self, provider: ExchangeRateProvider, ttl_seconds: int = 3600):
        self.provider = provider
        self.ttl_seconds = ttl_seconds
        self._cache: Dict[str, Tuple[datetime, Dict[str, Decimal]]] = {}

    def get_rates(self, base_currency: str = "USD") -> Dict[str, Decimal]:
        base = base_currency.upper().strip()
        now = datetime.now(timezone.utc)

        if base in self._cache:
            timestamp, cached_rates = self._cache[base]
            if (now - timestamp).total_seconds() < self.ttl_seconds:
                return cached_rates

        fresh_rates = self.provider.get_rates(base)
        self._cache[base] = (now, fresh_rates)
        return fresh_rates

    def get_rate(self, from_curr: str, to_curr: str) -> Decimal:
        f_curr = from_curr.upper().strip()
        t_curr = to_curr.upper().strip()
        if f_curr == t_curr:
            return Decimal("1.000000")

        rates = self.get_rates(f_curr)
        return rates[t_curr]


class FXService:
    """
    High-level domain service providing currency conversion and foreign exchange utilities.
    Guarantees exact Decimal arithmetic to eliminate floating-point truncation.
    """

    def __init__(self, provider: Optional[ExchangeRateProvider] = None):
        self.provider = provider or CachedFXProvider(FallbackStaticFXAdapter())

    def get_supported_currencies(self) -> List[str]:
        """Returns list of supported ISO 4217 currency symbols."""
        return list(FallbackStaticFXAdapter.DEFAULT_RATES_USD.keys())

    def get_exchange_rate(self, from_curr: str, to_curr: str) -> Decimal:
        """Fetch current exchange rate between two currencies."""
        return self.provider.get_rate(from_curr, to_curr)

    def convert(
        self, amount: Decimal, from_curr: str, to_curr: str
    ) -> Tuple[Decimal, Decimal]:
        """
        Converts monetary amount from source currency to target currency.
        Returns:
            (converted_amount, exchange_rate)
        """
        f_curr = from_curr.upper().strip()
        t_curr = to_curr.upper().strip()

        if f_curr == t_curr:
            return amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP), Decimal("1.000000")

        rate = self.get_exchange_rate(f_curr, t_curr)
        converted = (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        return converted, rate

    def get_all_rates(self, base_currency: str = "USD") -> Dict[str, Decimal]:
        """Fetch all rates relative to base_currency."""
        return self.provider.get_rates(base_currency)


# Global singleton instance for injection
default_fx_service = FXService()
