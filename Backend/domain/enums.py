from enum import Enum


class OrderStatus(str, Enum):
    BEING_PICKED = "wordt verzameld"
    SHIPPED = "verstuurd"
    BACKORDER = "backorder"
    DELIVERED = "afgeleverd"


class DayPart(str, Enum):
    MORNING = "ochtend"
    AFTERNOON = "middag"
