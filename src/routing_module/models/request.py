"""Request models produced by the LLM parser."""

from enum import Enum

from pydantic import BaseModel, Field


class FuelType(str, Enum):
    """Supported fuel types for vehicle range calculations."""

    GASOLINE = "gasoline"
    DIESEL = "diesel"
    ELECTRIC = "electric"


class StopType(str, Enum):
    """Categories of stops the user may request along the route."""

    GAS_STATION = "gas_station"
    REST_STOP = "rest_stop"
    FOOD = "food"
    HOTEL = "hotel"
    SHOPPING = "shopping"
    CUSTOM = "custom"


class VehicleInfo(BaseModel):
    """Vehicle constraints used for fuel stop planning."""

    fuel_tank_liters: float | None = Field(
        default=None,
        description="Tank capacity in liters. None means no fuel planning.",
        gt=0,
    )
    fuel_consumption_l_per_100km: float = Field(
        default=8.0,
        description="Average fuel use. Default 8 L/100km when user does not specify.",
        gt=0,
    )
    fuel_type: FuelType = FuelType.GASOLINE


class StopPreference(BaseModel):
    """User preference for a type of stop along the route."""

    type: StopType
    brands: list[str] = Field(default_factory=list)
    amenities: list[str] = Field(default_factory=list)
    categories: list[str] = Field(default_factory=list)
    notes: str | None = None


class OvernightStay(BaseModel):
    """Requested overnight stop in a country along the route."""

    country: str
    nights: int = Field(default=1, ge=1)
    notes: str | None = None


class RouteRequest(BaseModel):
    """Structured trip plan extracted from natural language input."""

    origin: str
    destination: str
    vehicle: VehicleInfo = Field(default_factory=VehicleInfo)
    stop_preferences: list[StopPreference] = Field(default_factory=list)
    overnight_stays: list[OvernightStay] = Field(default_factory=list)
    explicit_waypoints: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(
        default_factory=list,
        description="Parser notes about corrections or assumptions.",
    )

    @property
    def needs_fuel_planning(self) -> bool:
        """True when tank size is known and fuel stops should be planned."""
        return self.vehicle.fuel_tank_liters is not None

    @property
    def max_range_km(self) -> float | None:
        """Maximum driving range on a full tank, in kilometers."""
        if self.vehicle.fuel_tank_liters is None:
            return None
        return (self.vehicle.fuel_tank_liters / self.vehicle.fuel_consumption_l_per_100km) * 100
