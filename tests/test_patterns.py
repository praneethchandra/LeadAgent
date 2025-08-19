"""Tests for design patterns."""

import asyncio
import time
from unittest.mock import AsyncMock, Mock

import pytest

from src.lead_agent.models import CircuitBreakerConfig, RetryConfig
from src.lead_agent.patterns.circuit_breaker import CircuitBreaker, CircuitBreakerState
from src.lead_agent.patterns.retry import RetryHandler, RetryExhaustedException
from src.lead_agent.patterns.observer import Observer, Subject


class TestCircuitBreaker:
    """Test CircuitBreaker class."""
    
    def test_initial_state(self):
        """Test initial circuit breaker state."""
        config = CircuitBreakerConfig(failure_threshold=3, recovery_timeout=60)
        cb = CircuitBreaker(config)
        
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
        assert cb.success_count == 0
        assert cb.is_closed is True
        assert cb.is_open is False
        assert cb.is_half_open is False
    
    def test_can_execute_when_closed(self):
        """Test execution allowed when circuit is closed."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)
        
        assert cb.can_execute() is True
    
    def test_record_success_when_closed(self):
        """Test recording success when circuit is closed."""
        config = CircuitBreakerConfig(failure_threshold=3)
        cb = CircuitBreaker(config)
        
        # Add some failures first
        cb.failure_count = 2
        
        cb.record_success()
        
        assert cb.failure_count == 0  # Should reset on success
        assert cb.state == CircuitBreakerState.CLOSED
    
    def test_record_failure_opens_circuit(self):
        """Test that failures open the circuit."""
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = CircuitBreaker(config)
        
        # First failure
        cb.record_failure()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 1
        
        # Second failure should open circuit
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        assert cb.failure_count == 2
        assert cb.last_failure_time is not None
        assert cb.is_open is True
    
    def test_can_execute_when_open(self):
        """Test execution blocked when circuit is open."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=60)
        cb = CircuitBreaker(config)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        # Should not allow execution
        assert cb.can_execute() is False
    
    def test_transition_to_half_open(self):
        """Test transition from open to half-open state."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=1.0)
        cb = CircuitBreaker(config)
        
        # Open the circuit
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN
        
        # Wait for recovery timeout
        time.sleep(1.1)
        
        # Should transition to half-open
        assert cb.can_execute() is True
        assert cb.state == CircuitBreakerState.HALF_OPEN
        assert cb.is_half_open is True
    
    def test_half_open_success_closes_circuit(self):
        """Test that success in half-open state closes circuit."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=1.0)
        cb = CircuitBreaker(config)
        
        # Open the circuit and transition to half-open
        cb.record_failure()
        time.sleep(1.1)
        cb.can_execute()  # Transitions to half-open
        
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # Record success should close circuit
        cb.record_success()
        assert cb.state == CircuitBreakerState.CLOSED
        assert cb.failure_count == 0
        assert cb.last_failure_time is None
    
    def test_half_open_failure_opens_circuit(self):
        """Test that failure in half-open state opens circuit."""
        config = CircuitBreakerConfig(failure_threshold=1, recovery_timeout=1.0)
        cb = CircuitBreaker(config)
        
        # Open the circuit and transition to half-open
        cb.record_failure()
        time.sleep(1.1)
        cb.can_execute()  # Transitions to half-open
        
        assert cb.state == CircuitBreakerState.HALF_OPEN
        
        # Record failure should open circuit again
        cb.record_failure()
        assert cb.state == CircuitBreakerState.OPEN


class TestRetryHandler:
    """Test RetryHandler class."""
    
    def test_successful_execution_no_retry(self):
        """Test successful execution without retry."""
        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        handler = RetryHandler(config)
        
        mock_func = Mock(return_value="success")
        
        result = asyncio.run(handler.execute_with_retry(mock_func, "arg1", kwarg1="value1"))
        
        assert result == "success"
        assert mock_func.call_count == 1
        mock_func.assert_called_with("arg1", kwarg1="value1")
    
    def test_successful_async_execution_no_retry(self):
        """Test successful async execution without retry."""
        config = RetryConfig(max_attempts=3, initial_delay=0.1)
        handler = RetryHandler(config)
        
        mock_func = AsyncMock(return_value="async_success")
        
        result = asyncio.run(handler.execute_with_retry(mock_func, "arg1", kwarg1="value1"))
        
        assert result == "async_success"
        assert mock_func.call_count == 1
        mock_func.assert_called_with("arg1", kwarg1="value1")
    
    def test_retry_on_failure(self):
        """Test retry behavior on failure."""
        config = RetryConfig(max_attempts=3, initial_delay=0.1, jitter=False)
        handler = RetryHandler(config)
        
        mock_func = Mock(side_effect=[Exception("error1"), Exception("error2"), "success"])
        
        result = asyncio.run(handler.execute_with_retry(mock_func))
        
        assert result == "success"
        assert mock_func.call_count == 3
    
    def test_retry_exhausted(self):
        """Test retry exhausted scenario."""
        config = RetryConfig(max_attempts=2, initial_delay=0.1)
        handler = RetryHandler(config)
        
        mock_func = Mock(side_effect=Exception("persistent_error"))
        
        with pytest.raises(RetryExhaustedException) as exc_info:
            asyncio.run(handler.execute_with_retry(mock_func))
        
        assert "All 2 retry attempts failed" in str(exc_info.value)
        assert "persistent_error" in str(exc_info.value)
        assert mock_func.call_count == 2
    
    def test_delay_calculation_without_jitter(self):
        """Test delay calculation without jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=False
        )
        handler = RetryHandler(config)
        
        # Test exponential backoff
        assert handler._calculate_delay(0) == 1.0  # 1.0 * (2^0) = 1.0
        assert handler._calculate_delay(1) == 2.0  # 1.0 * (2^1) = 2.0
        assert handler._calculate_delay(2) == 4.0  # 1.0 * (2^2) = 4.0
        assert handler._calculate_delay(3) == 8.0  # 1.0 * (2^3) = 8.0
        assert handler._calculate_delay(4) == 10.0  # Capped at max_delay
    
    def test_delay_calculation_with_jitter(self):
        """Test delay calculation with jitter."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=2.0,
            max_delay=10.0,
            jitter=True
        )
        handler = RetryHandler(config)
        
        # With jitter, delay should be within 10% of base delay
        delay = handler._calculate_delay(1)  # Base would be 2.0
        assert 1.8 <= delay <= 2.2  # 2.0 ± 10%
    
    def test_max_delay_enforcement(self):
        """Test that delays are capped at max_delay."""
        config = RetryConfig(
            initial_delay=1.0,
            exponential_base=3.0,
            max_delay=5.0,
            jitter=False
        )
        handler = RetryHandler(config)
        
        # High attempt number should still be capped
        delay = handler._calculate_delay(10)
        assert delay == 5.0


class MockObserver(Observer):
    """Mock observer for testing."""
    
    def __init__(self):
        self.events = []
    
    async def update(self, subject: Subject, event_type: str, data: any) -> None:
        """Record events."""
        self.events.append((subject, event_type, data))


class TestObserver:
    """Test Observer pattern."""
    
    def test_attach_detach_observer(self):
        """Test attaching and detaching observers."""
        subject = Subject()
        observer = MockObserver()
        
        # Initially no observers
        assert len(subject._observers) == 0
        
        # Attach observer
        subject.attach(observer)
        assert len(subject._observers) == 1
        assert observer in subject._observers
        
        # Attach same observer again (should not duplicate)
        subject.attach(observer)
        assert len(subject._observers) == 1
        
        # Detach observer
        subject.detach(observer)
        assert len(subject._observers) == 0
        assert observer not in subject._observers
        
        # Detach non-existent observer (should not error)
        subject.detach(observer)
        assert len(subject._observers) == 0
    
    def test_notify_observers(self):
        """Test notifying observers."""
        subject = Subject()
        observer1 = MockObserver()
        observer2 = MockObserver()
        
        subject.attach(observer1)
        subject.attach(observer2)
        
        # Notify with event
        asyncio.run(subject.notify("test_event", {"data": "test"}))
        
        # Check both observers received the event
        assert len(observer1.events) == 1
        assert len(observer2.events) == 1
        
        event1 = observer1.events[0]
        event2 = observer2.events[0]
        
        assert event1[0] is subject  # subject
        assert event1[1] == "test_event"  # event_type
        assert event1[2] == {"data": "test"}  # data
        
        assert event2[0] is subject
        assert event2[1] == "test_event"
        assert event2[2] == {"data": "test"}
    
    def test_notify_with_failing_observer(self):
        """Test that notification continues even if one observer fails."""
        subject = Subject()
        
        # Create observers, one that fails
        good_observer = MockObserver()
        
        class FailingObserver(Observer):
            async def update(self, subject: Subject, event_type: str, data: any) -> None:
                raise Exception("Observer failed")
        
        failing_observer = FailingObserver()
        
        subject.attach(good_observer)
        subject.attach(failing_observer)
        
        # Notify should not raise exception
        asyncio.run(subject.notify("test_event", "test_data"))
        
        # Good observer should still receive the event
        assert len(good_observer.events) == 1
        assert good_observer.events[0][1] == "test_event"
        assert good_observer.events[0][2] == "test_data"
