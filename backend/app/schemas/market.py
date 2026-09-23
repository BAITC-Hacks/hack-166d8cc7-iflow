from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import Field

from .common import ID, Model


Coins = Annotated[int, Field(ge=0)]


class MarketReward(Model):
    id: ID
    title: str
    description: str
    price: Annotated[int, Field(gt=0)]
    category: Literal["Мерч", "Обучение", "События"]
    art: Literal["cup", "book", "bag", "ticket"]
    color: Literal["mint", "lilac", "yellow", "peach"]


class RedemptionCommand(Model):
    command_id: UUID
    reward_id: ID


class Redemption(Model):
    command_id: UUID
    employee_id: ID
    reward_id: ID
    price: Coins
    balance: Coins
    redeemed_on: date


class MarketReceipt(Model):
    request_fingerprint: str
    earned_at_redemption: Coins
    result: Redemption


class MarketState(Model):
    rewards: tuple[MarketReward, ...]
    employee_id: str | None
    balance: Coins | None
    earned: Coins | None
    spent: Coins | None
    coins_per_completion: int
    redemptions: tuple[Redemption, ...]
    revision: Annotated[int, Field(ge=0)]
    as_of_date: date
