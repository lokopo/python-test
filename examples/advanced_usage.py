"""
Advanced usage example of GUI verification tools.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from gui_verification import (
    VisualVerifier, LayoutVerifier, AccessibilityVerifier,
    InteractionVerifier, ResponsiveVerifier, PerformanceVerifier,
    BrowserManager, VerificationConfig, ReportGenerator
)


def test_e_commerce_site():
    """Example of testing an e-commerce site."""
    
    # Create custom configuration
    config = VerificationConfig(
        screenshot_threshold=0.98,
        max_load_time=2000,
        min_contrast_ratio=4.5,
        default_viewports=[
            {'name': 'mobile', 'width': 375, 'height': 667},
            {'name': 'tablet', 'width': 768, 'height': 1024},
            {'name': 'desktop', 'width': 1920, 'height': 1080}
        ]
    )
    
    # Create report generator
    report_generator = ReportGenerator(config)
    
    with BrowserManager(headless=False) as driver:
        # Navigate to e-commerce site
        driver.get("https://example-ecommerce.com")
        
        all_results = []
        
        # Test visual elements
        print("Testing visual elements...")
        visual_verifier = VisualVerifier(config)
        visual_result = visual_verifier.verify(driver, checks=['elements'], elements=[
            {'selector': 'header', 'expected_text': 'Welcome'},
            {'selector': '.product-grid', 'expected_visible': True},
            {'selector': '.shopping-cart', 'expected_visible': True}
        ])
        all_results.append(visual_result)
        
        # Test layout
        print("Testing layout...")
        layout_verifier = LayoutVerifier(config)
        layout_result = layout_verifier.verify(driver, checks=['alignment'], alignment_checks=[{
            'elements': [
                {'selector': '.product-card', 'by': 'css'},
                {'selector': '.product-card', 'by': 'css'},
                {'selector': '.product-card', 'by': 'css'}
            ],
            'type': 'grid',
            'columns': 3
        }])
        all_results.append(layout_result)
        
        # Test accessibility
        print("Testing accessibility...")
        accessibility_verifier = AccessibilityVerifier(config)
        accessibility_result = accessibility_verifier.verify(driver, checks=['aria', 'contrast'], elements=[
            {'selector': 'button', 'by': 'css'},
            {'selector': 'input', 'by': 'css'},
            {'selector': 'a', 'by': 'css'}
        ])
        all_results.append(accessibility_result)
        
        # Test interactions
        print("Testing interactions...")
        interaction_verifier = InteractionVerifier(config)
        interaction_result = interaction_verifier.verify(driver, checks=['click', 'form'], click_tests=[{
            'name': 'add_to_cart',
            'selector': '.add-to-cart-btn',
            'expected_result': {
                'expected_classes': ['added', 'in-cart'],
                'expected_new_elements': ['.cart-notification']
            }
        }])
        all_results.append(interaction_result)
        
        # Test responsive design
        print("Testing responsive design...")
        responsive_verifier = ResponsiveVerifier(config)
        responsive_result = responsive_verifier.verify(driver, checks=['viewport'], elements=[
            {'selector': 'nav', 'type': 'responsive_element'},
            {'selector': '.product-grid', 'type': 'responsive_element'},
            {'selector': '.sidebar', 'type': 'responsive_element'}
        ])
        all_results.append(responsive_result)
        
        # Test performance
        print("Testing performance...")
        performance_verifier = PerformanceVerifier(config)
        performance_result = performance_verifier.verify(driver, checks=['load_time'], url=driver.current_url)
        all_results.append(performance_result)
        
        # Generate reports
        print("Generating reports...")
        html_report = report_generator.generate_html_report(
            all_results, 
            "ecommerce_verification_report.html",
            "E-commerce Site Verification Report"
        )
        
        json_report = report_generator.generate_json_report(
            all_results,
            "ecommerce_verification_report.json"
        )
        
        console_report = report_generator.generate_console_report(all_results)
        print(console_report)
        
        print(f"Reports generated:")
        print(f"  HTML: {html_report}")
        print(f"  JSON: {json_report}")


def test_form_validation():
    """Example of testing form validation."""
    
    config = VerificationConfig()
    
    with BrowserManager(headless=False) as driver:
        driver.get("https://example-form.com")
        
        # Test form validation
        interaction_verifier = InteractionVerifier(config)
        
        # Test required field validation
        form_result = interaction_verifier.verify(driver, checks=['form'], form_tests=[{
            'name': 'contact_form_validation',
            'form_selector': 'form#contact',
            'type': 'required_validation',
            'required_fields': [
                {'selector': 'input[name="name"]', 'by': 'css'},
                {'selector': 'input[name="email"]', 'by': 'css'},
                {'selector': 'textarea[name="message"]', 'by': 'css'}
            ]
        }])
        
        print("Form validation test:")
        print(f"  Status: {form_result.status.value}")
        print(f"  Message: {form_result.message}")
        if form_result.details:
            print(f"  Details: {form_result.details}")


def test_accessibility_comprehensive():
    """Example of comprehensive accessibility testing."""
    
    config = VerificationConfig(
        min_contrast_ratio=4.5,
        large_text_ratio=3.0
    )
    
    with BrowserManager(headless=False) as driver:
        driver.get("https://example-accessibility.com")
        
        # Test accessibility comprehensively
        accessibility_verifier = AccessibilityVerifier(config)
        
        # Test ARIA attributes
        aria_result = accessibility_verifier.verify(driver, checks=['aria'], elements=[
            {'selector': 'button', 'by': 'css'},
            {'selector': 'input', 'by': 'css'},
            {'selector': 'nav', 'by': 'css'},
            {'selector': '[role="button"]', 'by': 'css'}
        ])
        
        # Test color contrast
        contrast_result = accessibility_verifier.verify(driver, checks=['contrast'], elements=[
            {'selector': 'h1', 'by': 'css'},
            {'selector': 'h2', 'by': 'css'},
            {'selector': 'p', 'by': 'css'},
            {'selector': 'a', 'by': 'css'}
        ])
        
        # Test keyboard navigation
        keyboard_result = accessibility_verifier.verify(driver, checks=['keyboard'], navigation_tests=[{
            'name': 'main_navigation',
            'type': 'tab_sequence',
            'elements': [{'selector': 'nav a, nav button', 'by': 'css'}]
        }])
        
        print("Accessibility test results:")
        for result in [aria_result, contrast_result, keyboard_result]:
            print(f"  {result.check_name}: {result.status.value}")
            print(f"    Message: {result.message}")


if __name__ == "__main__":
    print("Running advanced GUI verification examples...")
    print("=" * 50)
    
    print("\n1. E-commerce Site Testing")
    print("-" * 30)
    test_e_commerce_site()
    
    print("\n2. Form Validation Testing")
    print("-" * 30)
    test_form_validation()
    
    print("\n3. Comprehensive Accessibility Testing")
    print("-" * 30)
    test_accessibility_comprehensive()
    
    print("\nAll examples completed!")