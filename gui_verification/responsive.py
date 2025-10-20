"""
Responsive design verification tools for GUI testing.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .core import BaseVerifier, VerificationResult, VerificationStatus


class ResponsiveVerifier(BaseVerifier):
    """Main responsive design verification class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.viewport_tester = ViewportTester(config)
        self.breakpoint_checker = BreakpointChecker(config)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Run responsive design verification checks."""
        checks = kwargs.get('checks', ['viewport', 'breakpoints'])
        results = []
        
        for check in checks:
            if check == 'viewport':
                result = self.viewport_tester.verify(target, **kwargs)
                results.append(result)
            elif check == 'breakpoints':
                result = self.breakpoint_checker.verify(target, **kwargs)
                results.append(result)
        
        # Determine overall status
        if all(r.status == VerificationStatus.PASS for r in results):
            status = VerificationStatus.PASS
            message = "All responsive design checks passed"
        elif any(r.status == VerificationStatus.FAIL for r in results):
            status = VerificationStatus.FAIL
            message = "Some responsive design checks failed"
        else:
            status = VerificationStatus.WARNING
            message = "Some responsive design checks have warnings"
        
        return VerificationResult(
            check_name="ResponsiveVerifier",
            status=status,
            message=message,
            details={"individual_results": [r.__dict__ for r in results]}
        )


class ViewportTester(BaseVerifier):
    """Test responsive behavior at different viewport sizes."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.default_viewports = config.get('default_viewports', [
            {'name': 'mobile', 'width': 375, 'height': 667},
            {'name': 'tablet', 'width': 768, 'height': 1024},
            {'name': 'desktop', 'width': 1920, 'height': 1080}
        ])
        self.tolerance = config.get('viewport_tolerance', 10)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Test responsive behavior at different viewport sizes."""
        driver = target
        viewports = kwargs.get('viewports', self.default_viewports)
        elements_to_check = kwargs.get('elements', [])
        
        if not elements_to_check:
            # Find common responsive elements
            elements_to_check = self._find_responsive_elements(driver)
        
        results = []
        all_passed = True
        
        for viewport in viewports:
            try:
                result = self._test_viewport(driver, viewport, elements_to_check)
                results.append(result)
                if not result['passed']:
                    all_passed = False
            except Exception as e:
                results.append({
                    'viewport': viewport['name'],
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"Viewport tests: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="ViewportTester",
            status=status,
            message=message,
            details={"viewport_results": results}
        )
    
    def _find_responsive_elements(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """Find elements that commonly need responsive testing."""
        responsive_selectors = [
            'nav', 'header', 'main', 'aside', 'footer',
            '.container', '.row', '.col-', '.grid-',
            '[class*="responsive"]', '[class*="mobile"]', '[class*="desktop"]'
        ]
        
        elements = []
        for selector in responsive_selectors:
            try:
                found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for i, element in enumerate(found_elements):
                    if element.is_displayed():
                        elements.append({
                            'selector': f"{selector}:nth-of-type({i+1})",
                            'by': By.CSS_SELECTOR,
                            'type': 'responsive_element'
                        })
            except:
                continue
        
        return elements
    
    def _test_viewport(self, driver: webdriver.Chrome, viewport: Dict[str, Any], 
                      elements_to_check: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Test a specific viewport size."""
        viewport_name = viewport['name']
        width = viewport['width']
        height = viewport['height']
        
        result = {
            'viewport': viewport_name,
            'width': width,
            'height': height,
            'passed': True,
            'checks': []
        }
        
        try:
            # Set viewport size
            driver.set_window_size(width, height)
            time.sleep(1)  # Wait for layout to adjust
            
            # Check each element
            for element_spec in elements_to_check:
                element_result = self._check_element_responsive(driver, element_spec, viewport)
                result['checks'].extend(element_result['checks'])
                if not element_result['passed']:
                    result['passed'] = False
            
            # Check for horizontal scroll
            scroll_result = self._check_horizontal_scroll(driver, viewport)
            result['checks'].append(scroll_result)
            if not scroll_result['passed']:
                result['passed'] = False
            
            # Check for overlapping elements
            overlap_result = self._check_element_overlaps(driver, elements_to_check)
            result['checks'].append(overlap_result)
            if not overlap_result['passed']:
                result['passed'] = False
        
        except Exception as e:
            result['checks'].append({
                'type': 'viewport_test',
                'passed': False,
                'message': f'Viewport test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _check_element_responsive(self, driver: webdriver.Chrome, element_spec: Dict[str, Any], 
                                 viewport: Dict[str, Any]) -> Dict[str, Any]:
        """Check if an element behaves responsively."""
        selector = element_spec['selector']
        by_type = element_spec.get('by', By.CSS_SELECTOR)
        
        result = {
            'element': selector,
            'passed': True,
            'checks': []
        }
        
        try:
            element = driver.find_element(by_type, selector)
            bounds = self._get_element_bounds(element)
            viewport_width = viewport['width']
            
            # Check if element fits within viewport
            if bounds['x'] + bounds['width'] > viewport_width:
                result['checks'].append({
                    'type': 'viewport_fit',
                    'passed': False,
                    'message': f'Element extends beyond viewport width ({bounds["x"] + bounds["width"]} > {viewport_width})'
                })
                result['passed'] = False
            else:
                result['checks'].append({
                    'type': 'viewport_fit',
                    'passed': True,
                    'message': f'Element fits within viewport width'
                })
            
            # Check if element is visible
            if not element.is_displayed():
                result['checks'].append({
                    'type': 'visibility',
                    'passed': False,
                    'message': 'Element not visible at this viewport size'
                })
                result['passed'] = False
            else:
                result['checks'].append({
                    'type': 'visibility',
                    'passed': True,
                    'message': 'Element visible at this viewport size'
                })
            
            # Check element size appropriateness
            size_result = self._check_element_size_appropriateness(bounds, viewport)
            result['checks'].append(size_result)
            if not size_result['passed']:
                result['passed'] = False
        
        except Exception as e:
            result['checks'].append({
                'type': 'element_check',
                'passed': False,
                'message': f'Error checking element: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _check_element_size_appropriateness(self, bounds: Dict[str, int], viewport: Dict[str, Any]) -> Dict[str, Any]:
        """Check if element size is appropriate for viewport."""
        viewport_width = viewport['width']
        element_width = bounds['width']
        
        # Check if element is too small to be usable on mobile
        if viewport['name'] == 'mobile' and element_width < 44:  # Minimum touch target size
            return {
                'type': 'size_appropriateness',
                'passed': False,
                'message': f'Element too small for mobile touch target ({element_width}px < 44px)'
            }
        
        # Check if element takes up too much space
        width_percentage = (element_width / viewport_width) * 100
        if width_percentage > 90:
            return {
                'type': 'size_appropriateness',
                'passed': False,
                'message': f'Element takes up too much viewport width ({width_percentage:.1f}%)'
            }
        
        return {
            'type': 'size_appropriateness',
            'passed': True,
            'message': f'Element size appropriate for viewport ({width_percentage:.1f}% width)'
        }
    
    def _check_horizontal_scroll(self, driver: webdriver.Chrome, viewport: Dict[str, Any]) -> Dict[str, Any]:
        """Check for unwanted horizontal scroll."""
        viewport_width = viewport['width']
        
        # Get page width
        page_width = driver.execute_script("return document.documentElement.scrollWidth")
        
        if page_width > viewport_width:
            return {
                'type': 'horizontal_scroll',
                'passed': False,
                'message': f'Page has horizontal scroll (page width: {page_width}px > viewport: {viewport_width}px)'
            }
        else:
            return {
                'type': 'horizontal_scroll',
                'passed': True,
                'message': f'No horizontal scroll (page width: {page_width}px <= viewport: {viewport_width}px)'
            }
    
    def _check_element_overlaps(self, driver: webdriver.Chrome, elements_to_check: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Check for overlapping elements."""
        element_bounds = []
        
        for element_spec in elements_to_check:
            try:
                selector = element_spec['selector']
                by_type = element_spec.get('by', By.CSS_SELECTOR)
                element = driver.find_element(by_type, selector)
                bounds = self._get_element_bounds(element)
                bounds['selector'] = selector
                element_bounds.append(bounds)
            except:
                continue
        
        overlaps = []
        for i, bounds1 in enumerate(element_bounds):
            for j, bounds2 in enumerate(element_bounds[i+1:], i+1):
                if self._elements_overlap(bounds1, bounds2):
                    overlaps.append({
                        'element1': bounds1['selector'],
                        'element2': bounds2['selector']
                    })
        
        if overlaps:
            return {
                'type': 'element_overlaps',
                'passed': False,
                'message': f'Found {len(overlaps)} overlapping element pairs',
                'overlaps': overlaps
            }
        else:
            return {
                'type': 'element_overlaps',
                'passed': True,
                'message': 'No overlapping elements found'
            }
    
    def _elements_overlap(self, bounds1: Dict[str, int], bounds2: Dict[str, int]) -> bool:
        """Check if two elements overlap."""
        return not (bounds1['x'] + bounds1['width'] <= bounds2['x'] or
                   bounds2['x'] + bounds2['width'] <= bounds1['x'] or
                   bounds1['y'] + bounds1['height'] <= bounds2['y'] or
                   bounds2['y'] + bounds2['height'] <= bounds1['y'])
    
    def _get_element_bounds(self, element: WebElement) -> Dict[str, int]:
        """Get element bounds."""
        location = element.location
        size = element.size
        return {
            'x': location['x'],
            'y': location['y'],
            'width': size['width'],
            'height': size['height']
        }


class BreakpointChecker(BaseVerifier):
    """Check CSS breakpoint behavior."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.breakpoints = config.get('breakpoints', [
            {'name': 'mobile', 'min_width': 0, 'max_width': 767},
            {'name': 'tablet', 'min_width': 768, 'max_width': 1023},
            {'name': 'desktop', 'min_width': 1024, 'max_width': 9999}
        ])
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Check breakpoint behavior."""
        driver = target
        breakpoint_tests = kwargs.get('breakpoint_tests', [])
        
        if not breakpoint_tests:
            # Create default breakpoint tests
            breakpoint_tests = self._create_default_breakpoint_tests()
        
        results = []
        all_passed = True
        
        for test in breakpoint_tests:
            try:
                result = self._run_breakpoint_test(driver, test)
                results.append(result)
                if not result['passed']:
                    all_passed = False
            except Exception as e:
                results.append({
                    'test': test.get('name', 'unknown'),
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"Breakpoint tests: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="BreakpointChecker",
            status=status,
            message=message,
            details={"breakpoint_results": results}
        )
    
    def _create_default_breakpoint_tests(self) -> List[Dict[str, Any]]:
        """Create default breakpoint tests."""
        tests = []
        
        for breakpoint in self.breakpoints:
            tests.append({
                'name': f'breakpoint_{breakpoint["name"]}',
                'breakpoint': breakpoint,
                'type': 'visibility_check'
            })
        
        return tests
    
    def _run_breakpoint_test(self, driver: webdriver.Chrome, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single breakpoint test."""
        test_name = test['name']
        breakpoint = test['breakpoint']
        test_type = test['type']
        
        result = {
            'test': test_name,
            'breakpoint': breakpoint['name'],
            'passed': True,
            'checks': []
        }
        
        try:
            # Set viewport to breakpoint size
            test_width = (breakpoint['min_width'] + breakpoint['max_width']) // 2
            test_height = 800  # Standard height
            driver.set_window_size(test_width, test_height)
            time.sleep(1)
            
            if test_type == 'visibility_check':
                result = self._test_breakpoint_visibility(driver, test, result)
            elif test_type == 'layout_check':
                result = self._test_breakpoint_layout(driver, test, result)
        
        except Exception as e:
            result['checks'].append({
                'type': 'breakpoint_test',
                'passed': False,
                'message': f'Breakpoint test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _test_breakpoint_visibility(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test element visibility at breakpoint."""
        breakpoint = test['breakpoint']
        elements_to_check = test.get('elements', [])
        
        if not elements_to_check:
            # Check common responsive elements
            elements_to_check = [
                {'selector': 'nav', 'expected_visible': True},
                {'selector': '.mobile-menu', 'expected_visible': breakpoint['name'] == 'mobile'},
                {'selector': '.desktop-menu', 'expected_visible': breakpoint['name'] != 'mobile'}
            ]
        
        for element_spec in elements_to_check:
            selector = element_spec['selector']
            expected_visible = element_spec.get('expected_visible', True)
            
            try:
                element = driver.find_element(By.CSS_SELECTOR, selector)
                actual_visible = element.is_displayed()
                
                if actual_visible == expected_visible:
                    result['checks'].append({
                        'type': 'visibility_check',
                        'passed': True,
                        'message': f'Element {selector} visibility correct: {actual_visible}'
                    })
                else:
                    result['checks'].append({
                        'type': 'visibility_check',
                        'passed': False,
                        'message': f'Element {selector} visibility incorrect: expected {expected_visible}, got {actual_visible}'
                    })
                    result['passed'] = False
            
            except:
                if expected_visible:
                    result['checks'].append({
                        'type': 'visibility_check',
                        'passed': False,
                        'message': f'Element {selector} not found but expected to be visible'
                    })
                    result['passed'] = False
                else:
                    result['checks'].append({
                        'type': 'visibility_check',
                        'passed': True,
                        'message': f'Element {selector} not found as expected (not visible)'
                    })
        
        return result
    
    def _test_breakpoint_layout(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test layout behavior at breakpoint."""
        # This is a placeholder for layout-specific breakpoint tests
        result['checks'].append({
            'type': 'layout_check',
            'passed': True,
            'message': 'Layout check (placeholder)'
        })
        
        return result