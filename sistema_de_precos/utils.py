from fuel_station import FuelStation
from fuel_type_enum import FuelType


def parseToStation(fuelTypeStr, latStr, lonStr, priceStr):
    return FuelStation(FuelType(int(fuelTypeStr)), float(latStr), float(lonStr), int(priceStr))
