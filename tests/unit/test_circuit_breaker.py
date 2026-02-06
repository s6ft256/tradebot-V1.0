from paid_trading_bot.risk.circuit_breaker import CircuitBreaker, CircuitBreakerConfig, SystemState


def test_circuit_breaker_trips_on_drawdown():
    cb = CircuitBreaker(CircuitBreakerConfig(emergency_drawdown_percent=10.0))
    state = SystemState(
        drawdown_percent=10.0,
        sentinel_status="HEALTHY",
        sentinel_reason=None,
        api_consecutive_failures=0,
        balance_discrepancy_percent=0.0,
    )
    assert cb.check_and_trip(state) is True
    assert cb.is_tripped is True


def test_circuit_breaker_manual_reset_requires_token():
    cb = CircuitBreaker(CircuitBreakerConfig())
    cb._trip("TEST")
    assert cb.manual_reset(admin_token="") is False
    assert cb.manual_reset(admin_token="token") is True
