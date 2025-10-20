"""
Configuration and reporting utilities for GUI verification.
"""

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, asdict

from .core import VerificationResult, VerificationStatus


@dataclass
class VerificationConfig:
    """Configuration for GUI verification."""
    
    # Visual verification settings
    screenshot_threshold: float = 0.95
    screenshot_tolerance: int = 5
    
    # Layout verification settings
    position_tolerance: int = 5
    size_tolerance: int = 5
    alignment_tolerance: int = 5
    
    # Accessibility settings
    min_contrast_ratio: float = 4.5
    large_text_ratio: float = 3.0
    required_aria_attributes: List[str] = None
    
    # Performance settings
    max_load_time: int = 3000  # milliseconds
    max_dom_ready_time: int = 2000
    max_first_paint_time: int = 1000
    max_animation_duration: int = 500
    min_fps: int = 30
    
    # Responsive settings
    default_viewports: List[Dict[str, int]] = None
    viewport_tolerance: int = 10
    
    # General settings
    timeout: int = 10
    wait_time: int = 1
    hover_delay: float = 0.5
    
    def __post_init__(self):
        if self.required_aria_attributes is None:
            self.required_aria_attributes = [
                'aria-label', 'aria-labelledby', 'aria-describedby'
            ]
        
        if self.default_viewports is None:
            self.default_viewports = [
                {'name': 'mobile', 'width': 375, 'height': 667},
                {'name': 'tablet', 'width': 768, 'height': 1024},
                {'name': 'desktop', 'width': 1920, 'height': 1080}
            ]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, config_dict: Dict[str, Any]) -> 'VerificationConfig':
        """Create config from dictionary."""
        return cls(**config_dict)
    
    @classmethod
    def from_file(cls, file_path: str) -> 'VerificationConfig':
        """Load config from JSON file."""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return cls.from_dict(config_dict)
    
    def save_to_file(self, file_path: str):
        """Save config to JSON file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2)


class ReportGenerator:
    """Generate verification reports in various formats."""
    
    def __init__(self, config: Optional[VerificationConfig] = None):
        self.config = config or VerificationConfig()
    
    def generate_html_report(self, results: List[VerificationResult], 
                           output_path: str, title: str = "GUI Verification Report") -> str:
        """Generate HTML report."""
        html_content = self._create_html_template(title)
        
        # Add summary
        summary = self._generate_summary(results)
        html_content = html_content.replace('{{SUMMARY}}', self._format_summary_html(summary))
        
        # Add detailed results
        details_html = self._format_results_html(results)
        html_content = html_content.replace('{{DETAILS}}', details_html)
        
        # Add timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        html_content = html_content.replace('{{TIMESTAMP}}', timestamp)
        
        # Save to file
        with open(output_path, 'w') as f:
            f.write(html_content)
        
        return output_path
    
    def generate_json_report(self, results: List[VerificationResult], 
                           output_path: str) -> str:
        """Generate JSON report."""
        report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': self._generate_summary(results),
            'results': [self._result_to_dict(result) for result in results],
            'config': self.config.to_dict()
        }
        
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        return output_path
    
    def generate_console_report(self, results: List[VerificationResult]) -> str:
        """Generate console-friendly report."""
        summary = self._generate_summary(results)
        
        report = []
        report.append("=" * 60)
        report.append("GUI VERIFICATION REPORT")
        report.append("=" * 60)
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")
        
        # Summary
        report.append("SUMMARY:")
        report.append(f"  Total checks: {summary['total_checks']}")
        report.append(f"  Passed: {summary['passed']}")
        report.append(f"  Failed: {summary['failed']}")
        report.append(f"  Warnings: {summary['warnings']}")
        report.append(f"  Skipped: {summary['skipped']}")
        report.append(f"  Success rate: {summary['success_rate']:.1f}%")
        report.append("")
        
        # Detailed results
        report.append("DETAILED RESULTS:")
        report.append("-" * 60)
        
        for result in results:
            status_symbol = {
                VerificationStatus.PASS: "✓",
                VerificationStatus.FAIL: "✗",
                VerificationStatus.WARNING: "⚠",
                VerificationStatus.SKIP: "-"
            }[result.status]
            
            report.append(f"{status_symbol} {result.check_name}")
            report.append(f"  Status: {result.status.value.upper()}")
            report.append(f"  Message: {result.message}")
            
            if result.duration_ms:
                report.append(f"  Duration: {result.duration_ms:.1f}ms")
            
            if result.details:
                report.append(f"  Details: {json.dumps(result.details, indent=4)}")
            
            report.append("")
        
        return "\n".join(report)
    
    def _generate_summary(self, results: List[VerificationResult]) -> Dict[str, Any]:
        """Generate summary statistics."""
        total_checks = len(results)
        passed = sum(1 for r in results if r.status == VerificationStatus.PASS)
        failed = sum(1 for r in results if r.status == VerificationStatus.FAIL)
        warnings = sum(1 for r in results if r.status == VerificationStatus.WARNING)
        skipped = sum(1 for r in results if r.status == VerificationStatus.SKIP)
        
        success_rate = (passed / total_checks * 100) if total_checks > 0 else 0
        
        return {
            'total_checks': total_checks,
            'passed': passed,
            'failed': failed,
            'warnings': warnings,
            'skipped': skipped,
            'success_rate': success_rate
        }
    
    def _format_summary_html(self, summary: Dict[str, Any]) -> str:
        """Format summary as HTML."""
        return f"""
        <div class="summary">
            <h2>Summary</h2>
            <div class="summary-stats">
                <div class="stat">
                    <span class="stat-label">Total Checks:</span>
                    <span class="stat-value">{summary['total_checks']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Passed:</span>
                    <span class="stat-value passed">{summary['passed']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Failed:</span>
                    <span class="stat-value failed">{summary['failed']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Warnings:</span>
                    <span class="stat-value warning">{summary['warnings']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Skipped:</span>
                    <span class="stat-value skipped">{summary['skipped']}</span>
                </div>
                <div class="stat">
                    <span class="stat-label">Success Rate:</span>
                    <span class="stat-value">{summary['success_rate']:.1f}%</span>
                </div>
            </div>
        </div>
        """
    
    def _format_results_html(self, results: List[VerificationResult]) -> str:
        """Format results as HTML."""
        html_parts = []
        
        for result in results:
            status_class = result.status.value
            status_symbol = {
                VerificationStatus.PASS: "✓",
                VerificationStatus.FAIL: "✗",
                VerificationStatus.WARNING: "⚠",
                VerificationStatus.SKIP: "-"
            }[result.status]
            
            html_parts.append(f"""
            <div class="result {status_class}">
                <div class="result-header">
                    <span class="status-symbol">{status_symbol}</span>
                    <span class="check-name">{result.check_name}</span>
                    <span class="status-badge">{result.status.value.upper()}</span>
                </div>
                <div class="result-message">{result.message}</div>
                {f'<div class="result-duration">Duration: {result.duration_ms:.1f}ms</div>' if result.duration_ms else ''}
                {f'<div class="result-details"><pre>{json.dumps(result.details, indent=2)}</pre></div>' if result.details else ''}
            </div>
            """)
        
        return "".join(html_parts)
    
    def _result_to_dict(self, result: VerificationResult) -> Dict[str, Any]:
        """Convert VerificationResult to dictionary."""
        return {
            'check_name': result.check_name,
            'status': result.status.value,
            'message': result.message,
            'details': result.details,
            'timestamp': result.timestamp.isoformat() if result.timestamp else None,
            'duration_ms': result.duration_ms
        }
    
    def _create_html_template(self, title: str) -> str:
        """Create HTML template."""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            overflow: hidden;
        }}
        .header {{
            background: #2c3e50;
            color: white;
            padding: 20px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2em;
        }}
        .content {{
            padding: 20px;
        }}
        .summary {{
            margin-bottom: 30px;
        }}
        .summary h2 {{
            color: #2c3e50;
            border-bottom: 2px solid #3498db;
            padding-bottom: 10px;
        }}
        .summary-stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 20px;
        }}
        .stat {{
            background: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            text-align: center;
        }}
        .stat-label {{
            display: block;
            font-weight: bold;
            color: #666;
            margin-bottom: 5px;
        }}
        .stat-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .stat-value.passed {{ color: #27ae60; }}
        .stat-value.failed {{ color: #e74c3c; }}
        .stat-value.warning {{ color: #f39c12; }}
        .stat-value.skipped {{ color: #95a5a6; }}
        .result {{
            border: 1px solid #ddd;
            border-radius: 5px;
            margin-bottom: 15px;
            overflow: hidden;
        }}
        .result.pass {{
            border-left: 4px solid #27ae60;
        }}
        .result.fail {{
            border-left: 4px solid #e74c3c;
        }}
        .result.warning {{
            border-left: 4px solid #f39c12;
        }}
        .result.skip {{
            border-left: 4px solid #95a5a6;
        }}
        .result-header {{
            background: #f8f9fa;
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .status-symbol {{
            font-size: 1.2em;
            font-weight: bold;
        }}
        .check-name {{
            font-weight: bold;
            flex: 1;
        }}
        .status-badge {{
            background: #3498db;
            color: white;
            padding: 4px 8px;
            border-radius: 3px;
            font-size: 0.8em;
            font-weight: bold;
        }}
        .result-message {{
            padding: 15px;
        }}
        .result-duration {{
            padding: 0 15px 15px;
            color: #666;
            font-size: 0.9em;
        }}
        .result-details {{
            padding: 0 15px 15px;
        }}
        .result-details pre {{
            background: #f8f9fa;
            padding: 10px;
            border-radius: 3px;
            overflow-x: auto;
            font-size: 0.9em;
        }}
        .footer {{
            text-align: center;
            padding: 20px;
            color: #666;
            border-top: 1px solid #eee;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>{title}</h1>
            <p>Generated on {{TIMESTAMP}}</p>
        </div>
        <div class="content">
            {{SUMMARY}}
            <h2>Detailed Results</h2>
            {{DETAILS}}
        </div>
        <div class="footer">
            <p>Generated by GUI Verification Tools</p>
        </div>
    </div>
</body>
</html>
        """