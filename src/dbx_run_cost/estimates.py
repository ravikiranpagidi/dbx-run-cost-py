from __future__ import annotations

from .models import CostReport


def estimate_from_dbus(
    *,
    dbus: float,
    price_per_dbu: float,
    currency_code: str = "USD",
    **report_fields: object,
) -> CostReport:
    return CostReport.estimated(
        dbus=float(dbus),
        cost=float(dbus) * float(price_per_dbu),
        currency_code=currency_code,
        **report_fields,
    )


def estimate_from_duration(
    *,
    duration_seconds: float,
    dbus_per_hour: float,
    price_per_dbu: float,
    currency_code: str = "USD",
    **report_fields: object,
) -> CostReport:
    dbus = (float(duration_seconds) / 3600.0) * float(dbus_per_hour)
    return estimate_from_dbus(
        dbus=dbus,
        price_per_dbu=price_per_dbu,
        currency_code=currency_code,
        **report_fields,
    )
