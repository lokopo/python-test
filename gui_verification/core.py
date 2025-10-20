"""
Core verification framework and base classes.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List, Optional, Union
import time
from datetime import datetime


class VerificationStatus(Enum):
    """Status of a verification check."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


@dataclass
class VerificationResult:
    """Result of a verification check."""
    check_name: str
    status: VerificationStatus
    message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    duration_ms: Optional[float] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class VerificationError(Exception):
    """Exception raised during verification."""
    pass


class BaseVerifier(ABC):
    """Base class for all GUI verifiers."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.results: List[VerificationResult] = []
    
    @abstractmethod
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Perform the verification check."""
        pass
    
    def run_verification(self, target: Any, **kwargs) -> VerificationResult:
        """Run verification with timing and error handling."""
        start_time = time.time()
        
        try:
            result = self.verify(target, **kwargs)
            result.duration_ms = (time.time() - start_time) * 1000
            self.results.append(result)
            return result
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            error_result = VerificationResult(
                check_name=self.__class__.__name__,
                status=VerificationStatus.FAIL,
                message=f"Verification failed with error: {str(e)}",
                duration_ms=duration_ms
            )
            self.results.append(error_result)
            return error_result
    
    def get_results(self) -> List[VerificationResult]:
        """Get all verification results."""
        return self.results.copy()
    
    def clear_results(self):
        """Clear all verification results."""
        self.results.clear()
    
    def get_summary(self) -> Dict[str, int]:
        """Get summary of verification results."""
        summary = {status.value: 0 for status in VerificationStatus}
        for result in self.results:
            summary[result.status.value] += 1
        return summary


class VerificationSuite:
    """A suite of verifiers that can be run together."""
    
    def __init__(self, name: str = "Verification Suite"):
        self.name = name
        self.verifiers: List[BaseVerifier] = []
        self.results: List[VerificationResult] = []
    
    def add_verifier(self, verifier: BaseVerifier):
        """Add a verifier to the suite."""
        self.verifiers.append(verifier)
    
    def run_all(self, target: Any, **kwargs) -> List[VerificationResult]:
        """Run all verifiers in the suite."""
        self.results.clear()
        
        for verifier in self.verifiers:
            result = verifier.run_verification(target, **kwargs)
            self.results.append(result)
        
        return self.results.copy()
    
    def get_suite_summary(self) -> Dict[str, Any]:
        """Get summary of the entire suite."""
        summary = {
            "suite_name": self.name,
            "total_checks": len(self.results),
            "status_counts": {status.value: 0 for status in VerificationStatus},
            "total_duration_ms": 0,
            "verifiers": []
        }
        
        for result in self.results:
            summary["status_counts"][result.status.value] += 1
            if result.duration_ms:
                summary["total_duration_ms"] += result.duration_ms
        
        for verifier in self.verifiers:
            verifier_summary = verifier.get_summary()
            summary["verifiers"].append({
                "name": verifier.__class__.__name__,
                "results": verifier_summary
            })
        
        return summary