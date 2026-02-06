from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import TYPE_CHECKING
import hashlib
import secrets

if TYPE_CHECKING:
    pass


class SubscriptionTier(Enum):
    """Subscription tiers for the trading bot."""
    FREE = "free"
    BASIC = "basic"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class PaymentStatus(Enum):
    """Payment status for subscriptions."""
    ACTIVE = "active"
    PENDING = "pending"
    EXPIRED = "expired"
    CANCELLED = "cancelled"
    SUSPENDED = "suspended"


@dataclass
class SubscriptionPlan:
    """Defines a subscription plan."""
    tier: SubscriptionTier
    name: str
    price_monthly: float
    price_yearly: float
    max_strategies: int
    max_positions: int
    paper_trading: bool
    live_trading: bool
    ai_advisory: bool
    priority_support: bool
    features: list[str]


@dataclass
class UserSubscription:
    """User's subscription details."""
    user_id: str
    plan: SubscriptionPlan
    status: PaymentStatus
    start_date: datetime
    end_date: datetime
    last_payment_date: datetime | None
    payment_method: str | None
    auto_renew: bool


class SubscriptionManager:
    """
    Manages subscription plans and payment status.
    Controls access to trading features based on subscription tier.
    """

    PLANS: dict[SubscriptionTier, SubscriptionPlan] = {
        SubscriptionTier.FREE: SubscriptionPlan(
            tier=SubscriptionTier.FREE,
            name="Free",
            price_monthly=0.0,
            price_yearly=0.0,
            max_strategies=1,
            max_positions=1,
            paper_trading=True,
            live_trading=False,
            ai_advisory=False,
            priority_support=False,
            features=["1 strategy", "Paper trading only", "Basic indicators"],
        ),
        SubscriptionTier.BASIC: SubscriptionPlan(
            tier=SubscriptionTier.BASIC,
            name="Basic",
            price_monthly=29.99,
            price_yearly=299.99,
            max_strategies=3,
            max_positions=2,
            paper_trading=True,
            live_trading=True,
            ai_advisory=False,
            priority_support=False,
            features=["3 strategies", "Live trading", "Risk management", "Email alerts"],
        ),
        SubscriptionTier.PRO: SubscriptionPlan(
            tier=SubscriptionTier.PRO,
            name="Pro",
            price_monthly=79.99,
            price_yearly=799.99,
            max_strategies=10,
            max_positions=5,
            paper_trading=True,
            live_trading=True,
            ai_advisory=True,
            priority_support=True,
            features=[
                "10 strategies", "Live trading", "AI advisory layer",
                "Advanced risk controls", "Priority support", "API access"
            ],
        ),
        SubscriptionTier.ENTERPRISE: SubscriptionPlan(
            tier=SubscriptionTier.ENTERPRISE,
            name="Enterprise",
            price_monthly=299.99,
            price_yearly=2999.99,
            max_strategies=999,
            max_positions=20,
            paper_trading=True,
            live_trading=True,
            ai_advisory=True,
            priority_support=True,
            features=[
                "Unlimited strategies", "Live trading", "AI advisory layer",
                "Custom risk rules", "24/7 support", "White-label option",
                "Dedicated server"
            ],
        ),
    }

    def __init__(self):
        self._subscriptions: dict[str, UserSubscription] = {}
        self._api_keys: dict[str, str] = {}  # user_id -> api_key mapping

    def create_subscription(
        self,
        user_id: str,
        tier: SubscriptionTier,
        payment_method: str,
        yearly: bool = False,
    ) -> UserSubscription:
        """Create a new subscription for a user."""
        plan = self.PLANS[tier]
        
        now = datetime.utcnow()
        if yearly:
            end_date = now + timedelta(days=365)
        else:
            end_date = now + timedelta(days=30)
        
        subscription = UserSubscription(
            user_id=user_id,
            plan=plan,
            status=PaymentStatus.ACTIVE,
            start_date=now,
            end_date=end_date,
            last_payment_date=now,
            payment_method=payment_method,
            auto_renew=True,
        )
        
        self._subscriptions[user_id] = subscription
        self._generate_api_key(user_id)
        
        return subscription

    def get_subscription(self, user_id: str) -> UserSubscription | None:
        """Get user's subscription details."""
        return self._subscriptions.get(user_id)

    def check_feature_access(self, user_id: str, feature: str) -> bool:
        """Check if user has access to a specific feature."""
        sub = self._subscriptions.get(user_id)
        if not sub:
            return False
        
        # Check if subscription is active
        if sub.status != PaymentStatus.ACTIVE:
            return False
        
        # Check if subscription expired
        if datetime.utcnow() > sub.end_date:
            sub.status = PaymentStatus.EXPIRED
            return False
        
        # Feature checks
        if feature == "live_trading":
            return sub.plan.live_trading
        elif feature == "ai_advisory":
            return sub.plan.ai_advisory
        elif feature == "paper_trading":
            return sub.plan.paper_trading
        elif feature == "priority_support":
            return sub.plan.priority_support
        
        return feature in sub.plan.features

    def can_add_strategy(self, user_id: str, current_strategies: int) -> bool:
        """Check if user can add another strategy."""
        sub = self._subscriptions.get(user_id)
        if not sub or sub.status != PaymentStatus.ACTIVE:
            return False
        
        if datetime.utcnow() > sub.end_date:
            sub.status = PaymentStatus.EXPIRED
            return False
        
        return current_strategies < sub.plan.max_strategies

    def can_open_position(self, user_id: str, current_positions: int) -> bool:
        """Check if user can open another position."""
        sub = self._subscriptions.get(user_id)
        if not sub or sub.status != PaymentStatus.ACTIVE:
            return False
        
        if datetime.utcnow() > sub.end_date:
            sub.status = PaymentStatus.EXPIRED
            return False
        
        return current_positions < sub.plan.max_positions

    def renew_subscription(self, user_id: str) -> bool:
        """Renew user's subscription."""
        sub = self._subscriptions.get(user_id)
        if not sub:
            return False
        
        if not sub.auto_renew:
            return False
        
        # Simulate payment processing
        now = datetime.utcnow()
        
        # Calculate new end date
        if sub.end_date > now:
            # Still active, extend from end date
            new_end = sub.end_date + timedelta(days=30)
        else:
            # Expired, start from now
            new_end = now + timedelta(days=30)
        
        sub.end_date = new_end
        sub.last_payment_date = now
        sub.status = PaymentStatus.ACTIVE
        
        return True

    def cancel_subscription(self, user_id: str) -> bool:
        """Cancel user's subscription."""
        sub = self._subscriptions.get(user_id)
        if not sub:
            return False
        
        sub.status = PaymentStatus.CANCELLED
        sub.auto_renew = False
        return True

    def suspend_subscription(self, user_id: str, reason: str) -> bool:
        """Suspend subscription (e.g., for payment failure)."""
        sub = self._subscriptions.get(user_id)
        if not sub:
            return False
        
        sub.status = PaymentStatus.SUSPENDED
        return True

    def get_all_plans(self) -> list[SubscriptionPlan]:
        """Get all available subscription plans."""
        return list(self.PLANS.values())

    def _generate_api_key(self, user_id: str) -> str:
        """Generate unique API key for user."""
        # Create a unique API key
        random_component = secrets.token_urlsafe(32)
        user_hash = hashlib.sha256(user_id.encode()).hexdigest()[:16]
        api_key = f"trd_{user_hash}_{random_component}"
        self._api_keys[user_id] = api_key
        return api_key

    def get_api_key(self, user_id: str) -> str | None:
        """Get user's API key."""
        return self._api_keys.get(user_id)

    def validate_api_key(self, api_key: str) -> str | None:
        """Validate API key and return user_id if valid."""
        for user_id, key in self._api_keys.items():
            if key == api_key:
                # Check subscription is still valid
                sub = self._subscriptions.get(user_id)
                if sub and sub.status == PaymentStatus.ACTIVE:
                    if datetime.utcnow() <= sub.end_date:
                        return user_id
        return None

    def revoke_api_key(self, user_id: str) -> bool:
        """Revoke user's API key."""
        if user_id in self._api_keys:
            del self._api_keys[user_id]
            return True
        return False

    def get_expiring_subscriptions(self, days: int = 7) -> list[UserSubscription]:
        """Get subscriptions expiring within specified days."""
        expiring = []
        threshold = datetime.utcnow() + timedelta(days=days)
        
        for sub in self._subscriptions.values():
            if sub.status == PaymentStatus.ACTIVE:
                if sub.end_date <= threshold:
                    expiring.append(sub)
        
        return expiring

    def process_payment_failure(self, user_id: str) -> None:
        """Handle payment failure - suspend or downgrade."""
        sub = self._subscriptions.get(user_id)
        if not sub:
            return
        
        # Grace period of 3 days
        grace_end = sub.end_date + timedelta(days=3)
        
        if datetime.utcnow() > grace_end:
            # Downgrade to free tier
            sub.status = PaymentStatus.EXPIRED
            # Create new free subscription
            self.create_subscription(user_id, SubscriptionTier.FREE, "none")
