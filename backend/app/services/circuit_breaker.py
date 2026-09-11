import time
import logging
from enum import Enum

logger = logging.getLogger("nexagrid.circuit_breaker")

class CircuitState(Enum):
    CLOSED = "CLOSED"      # Normal operational state
    OPEN = "OPEN"          # Outage state (fast-failing calls)
    HALF_OPEN = "HALF_OPEN" # Testing recovery state

class CircuitBreaker:
    """
    Circuit Breaker Pattern implementation for resilient external AI service integration.
    """
    def __init__(self, failure_threshold: int = 3, recovery_time_seconds: int = 30):
        self.failure_threshold = failure_threshold
        self.recovery_time_seconds = recovery_time_seconds
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_state_change = time.time()

    def allow_request(self) -> bool:
        now = time.time()
        if self.state == CircuitState.OPEN:
            if now - self.last_state_change > self.recovery_time_seconds:
                self.state = CircuitState.HALF_OPEN
                self.last_state_change = now
                logger.info("Circuit Breaker transitioned to HALF_OPEN state.")
                return True
            return False
        return True

    def record_success(self):
        self.failure_count = 0
        if self.state != CircuitState.CLOSED:
            self.state = CircuitState.CLOSED
            self.last_state_change = time.time()
            logger.info("Circuit Breaker transitioned to CLOSED state.")

    def record_failure(self):
        self.failure_count += 1
        if self.state == CircuitState.HALF_OPEN or self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            self.last_state_change = time.time()
            logger.warning(f"Circuit Breaker tripped to OPEN state. (count: {self.failure_count})")

ai_circuit_breaker = CircuitBreaker(failure_threshold=3, recovery_time_seconds=20)
