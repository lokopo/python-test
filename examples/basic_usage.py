"""
Basic usage example of GUI verification tools.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui_verification import (
    VerificationSuite, VisualVerifier, LayoutVerifier, 
    AccessibilityVerifier, InteractionVerifier, ResponsiveVerifier,
    PerformanceVerifier, BrowserManager, VerificationConfig
)


def main():
    """Example of basic GUI verification usage."""
    
    # Create configuration
    config = VerificationConfig(
        screenshot_threshold=0.95,
        max_load_time=3000,
        min_contrast_ratio=4.5
    )
    
    # Create verification suite
    suite = VerificationSuite("Basic GUI Verification")
    
    # Add verifiers
    suite.add_verifier(VisualVerifier(config))
    suite.add_verifier(LayoutVerifier(config))
    suite.add_verifier(AccessibilityVerifier(config))
    suite.add_verifier(InteractionVerifier(config))
    suite.add_verifier(ResponsiveVerifier(config))
    suite.add_verifier(PerformanceVerifier(config))
    
    # Use browser manager
    with BrowserManager(headless=False) as driver:
        # Navigate to a test page
        driver.get("https://example.com")
        
        # Run all verifications
        results = suite.run_all(driver)
        
        # Print results
        for result in results:
            print(f"{result.check_name}: {result.status.value}")
            print(f"  Message: {result.message}")
            if result.details:
                print(f"  Details: {result.details}")
            print()


if __name__ == "__main__":
    main()