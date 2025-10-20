"""
GUI Verification Tools Suite

A comprehensive suite of tools for programmatically verifying GUI appearance and behavior.
"""

from .core import VerificationResult, VerificationError, BaseVerifier
from .visual import VisualVerifier, ScreenshotComparator, ElementDetector
from .layout import LayoutVerifier, PositionChecker, SizeChecker, AlignmentChecker
from .accessibility import AccessibilityVerifier, ARIAChecker, ContrastChecker, KeyboardNavigationChecker
from .interaction import InteractionVerifier, ClickTester, FormValidator, HoverTester
from .responsive import ResponsiveVerifier, ViewportTester, BreakpointChecker
from .performance import PerformanceVerifier, LoadTimeChecker, AnimationChecker
from .config import VerificationConfig, ReportGenerator
from .utils import BrowserManager, ElementFinder, ColorUtils

__version__ = "1.0.0"
__all__ = [
    "VerificationResult",
    "VerificationError", 
    "BaseVerifier",
    "VisualVerifier",
    "ScreenshotComparator",
    "ElementDetector",
    "LayoutVerifier",
    "PositionChecker",
    "SizeChecker",
    "AlignmentChecker",
    "AccessibilityVerifier",
    "ARIAChecker",
    "ContrastChecker",
    "KeyboardNavigationChecker",
    "InteractionVerifier",
    "ClickTester",
    "FormValidator",
    "HoverTester",
    "ResponsiveVerifier",
    "ViewportTester",
    "BreakpointChecker",
    "PerformanceVerifier",
    "LoadTimeChecker",
    "AnimationChecker",
    "VerificationConfig",
    "ReportGenerator",
    "BrowserManager",
    "ElementFinder",
    "ColorUtils",
]