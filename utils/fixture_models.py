from dataclasses import dataclass


@dataclass(frozen=True)
class DeliveryQuoteInfo:
    id: str | None = None
    fee: int | float | None = None
    currency: str | None = None
    expires_at: str | None = None


@dataclass(frozen=True)
class DeliveryContact:
    name: str | None = None
    phone: str | None = None
    address: str | None = None


@dataclass(frozen=True)
class DeliveryPackage:
    description: str | None = None
    weight_kg: int | float | None = None


@dataclass(frozen=True)
class DeliveryHistoryEntry:
    at: str
    status: str


@dataclass(frozen=True)
class DeliveryInfo:
    id: str | None = None
    business_id: str | None = None
    status: str | None = None
    fee: int | float | None = None
    currency: str | None = None
    pickup: DeliveryContact | None = None
    drop_off: DeliveryContact | None = None
    package: DeliveryPackage | None = None
    courier_id: str | None = None
    history: tuple[DeliveryHistoryEntry, ...] = ()


@dataclass(frozen=True)
class WalletInfo:
    balance: int | float | None = None
    held: int | float | None = None