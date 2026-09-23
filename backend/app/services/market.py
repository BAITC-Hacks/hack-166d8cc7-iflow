"""Demo rewards ledger, committed in the same overlay as employee progress."""

from datetime import date
import hashlib
import json
from typing import TYPE_CHECKING

from app.core.auth import Principal
from app.core.errors import DomainError
from app.repositories.dataset import DatasetSnapshot
from app.schemas.market import (
    MarketReceipt,
    MarketReward,
    MarketState,
    Redemption,
    RedemptionCommand,
)
from app.schemas.state import MutableState

if TYPE_CHECKING:
    from app.services.dataset import DatasetService


COINS_PER_COMPLETION = 80
REWARDS = (
    MarketReward(
        id="cup", title="Термокружка Halyk", price=160, category="Мерч",
        description="Для любимого кофе и новых идей. Демонстрационная награда.",
        art="cup", color="mint",
    ),
    MarketReward(
        id="book", title="Книга для следующего шага", price=80, category="Обучение",
        description="Выбери книгу о технологиях или развитии. Демонстрационная награда.",
        art="book", color="lilac",
    ),
    MarketReward(
        id="bag", title="Шоппер Halyk", price=240, category="Мерч",
        description="Забери полезный мерч за свой прогресс. Демонстрационная награда.",
        art="bag", color="yellow",
    ),
    MarketReward(
        id="ticket", title="Билет на конференцию", price=400, category="События",
        description="Новые знакомства и знания за пределами команды. Демонстрационная награда.",
        art="ticket", color="peach",
    ),
)
REWARDS_BY_ID = {reward.id: reward for reward in REWARDS}


def earned_coins(snapshot: DatasetSnapshot, employee_id: str, as_of_date: date) -> int:
    # Historical/imported completed rows do not mint coins. A runtime transition
    # from an in-progress assignment counts only when its event is voluntary.
    return COINS_PER_COMPLETION * sum(
        1 for completion in snapshot.runtime_completions
        if completion.employee_id == employee_id
        and completion.completed_on <= as_of_date
        and not snapshot.events.get(completion.event_id).mandatory
    )


def command_fingerprint(employee_id: str, command: RedemptionCommand) -> str:
    payload = {"employee_id": employee_id, "command": command.model_dump(mode="json")}
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def validate_market_state(snapshot: DatasetSnapshot, state: MutableState) -> None:
    """Reject an inconsistent ledger before startup or any state publication."""
    spent: dict[str, int] = {}
    previous_earnings: dict[str, int] = {}
    previous_dates: dict[str, date] = {}
    redeemed: set[tuple[str, str]] = set()
    for key, receipt in state.market_receipts.items():
        result = receipt.result
        employee_id = result.employee_id
        reward = REWARDS_BY_ID.get(result.reward_id)
        command = RedemptionCommand(command_id=result.command_id, reward_id=result.reward_id)
        if key != str(result.command_id) or receipt.request_fingerprint != command_fingerprint(employee_id, command):
            raise ValueError("Invalid market command receipt")
        if snapshot.employees.get(employee_id) is None or reward is None or result.price != reward.price:
            raise ValueError("Unknown market employee/reward or changed reward price")
        if (employee_id, reward.id) in redeemed:
            raise ValueError("Reward already redeemed by employee")
        redeemed.add((employee_id, reward.id))
        if result.redeemed_on < previous_dates.get(employee_id, snapshot.meta.as_of_date):
            raise ValueError("Market receipts must follow application date order")
        previous_dates[employee_id] = result.redeemed_on
        earned = receipt.earned_at_redemption
        if (
            earned % COINS_PER_COMPLETION != 0
            or earned < previous_earnings.get(employee_id, 0)
            or earned > earned_coins(snapshot, employee_id, result.redeemed_on)
        ):
            raise ValueError("Market receipt exceeds earned coins")
        previous_earnings[employee_id] = earned
        spent[employee_id] = spent.get(employee_id, 0) + result.price
        if result.balance != earned - spent[employee_id]:
            raise ValueError("Market receipt balance is inconsistent")


class MarketService:
    def __init__(self, dataset: "DatasetService"):
        self.dataset = dataset

    def read(self, principal: Principal, as_of_date: date) -> MarketState:
        with self.dataset.lock:
            snapshot = self.dataset.capture()
            if principal.role == "hr":
                return MarketState(
                    rewards=REWARDS, employee_id=None, balance=None, earned=None, spent=None,
                    coins_per_completion=COINS_PER_COMPLETION, redemptions=(),
                    revision=snapshot.revision, as_of_date=as_of_date,
                )
            employee_id = principal.employee_id
            if employee_id is None or snapshot.employees.get(employee_id) is None:
                raise DomainError("unauthorized", "Employee identity no longer exists")
            redemptions = tuple(
                receipt.result for receipt in self.dataset.state.market_receipts.values()
                if receipt.result.employee_id == employee_id
            )
            earned = earned_coins(snapshot, employee_id, as_of_date)
            spent = sum(redemption.price for redemption in redemptions)
            if any(redemption.redeemed_on > as_of_date for redemption in redemptions) or spent > earned:
                raise DomainError("conflict", "Application date precedes saved market activity")
            return MarketState(
                rewards=REWARDS, employee_id=employee_id, balance=earned - spent,
                earned=earned, spent=spent, coins_per_completion=COINS_PER_COMPLETION,
                redemptions=redemptions, revision=snapshot.revision, as_of_date=as_of_date,
            )

    def redeem(self, principal: Principal, command: RedemptionCommand, as_of_date: date) -> Redemption:
        if principal.role != "employee" or principal.employee_id is None:
            raise DomainError("forbidden", "Only employees may redeem their rewards")
        employee_id = principal.employee_id
        with self.dataset.lock:
            fingerprint = command_fingerprint(employee_id, command)
            key = str(command.command_id)
            prior = self.dataset.state.market_receipts.get(key)
            if prior is not None:
                if prior.request_fingerprint != fingerprint:
                    raise DomainError("conflict", "Command ID already used")
                return prior.result
            snapshot = self.dataset.capture()
            if snapshot.employees.get(employee_id) is None:
                raise DomainError("unauthorized", "Employee identity no longer exists")
            reward = REWARDS_BY_ID.get(command.reward_id)
            if reward is None:
                raise DomainError("not_found", "Reward not found")
            redemptions = [
                receipt.result for receipt in self.dataset.state.market_receipts.values()
                if receipt.result.employee_id == employee_id
            ]
            if any(result.reward_id == reward.id for result in redemptions):
                raise DomainError("conflict", "Reward already redeemed")
            if any(result.redeemed_on > as_of_date for result in redemptions):
                raise DomainError("conflict", "Application date precedes saved market activity")
            earned = earned_coins(snapshot, employee_id, as_of_date)
            balance = earned - sum(result.price for result in redemptions)
            if balance < reward.price:
                raise DomainError("conflict", "Insufficient coins")
            result = Redemption(
                command_id=command.command_id, employee_id=employee_id, reward_id=reward.id,
                price=reward.price, balance=balance - reward.price, redeemed_on=as_of_date,
            )
            receipt = MarketReceipt(request_fingerprint=fingerprint, earned_at_redemption=earned, result=result)
            next_state = self.dataset.state.model_copy(update={
                "revision": self.dataset.state.revision + 1,
                "market_receipts": {**self.dataset.state.market_receipts, key: receipt},
            })
            try:
                self.dataset.commit(next_state)
            except OSError as error:
                raise DomainError("unavailable", "Could not persist redemption; retry with the same command ID") from error
            return result
