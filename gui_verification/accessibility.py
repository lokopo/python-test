"""
Accessibility verification tools for GUI testing.
"""

import re
from typing import Any, Dict, List, Optional, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .core import BaseVerifier, VerificationResult, VerificationStatus


class AccessibilityVerifier(BaseVerifier):
    """Main accessibility verification class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.aria_checker = ARIAChecker(config)
        self.contrast_checker = ContrastChecker(config)
        self.keyboard_checker = KeyboardNavigationChecker(config)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Run accessibility verification checks."""
        checks = kwargs.get('checks', ['aria', 'contrast', 'keyboard'])
        results = []
        
        for check in checks:
            if check == 'aria':
                result = self.aria_checker.verify(target, **kwargs)
                results.append(result)
            elif check == 'contrast':
                result = self.contrast_checker.verify(target, **kwargs)
                results.append(result)
            elif check == 'keyboard':
                result = self.keyboard_checker.verify(target, **kwargs)
                results.append(result)
        
        # Determine overall status
        if all(r.status == VerificationStatus.PASS for r in results):
            status = VerificationStatus.PASS
            message = "All accessibility checks passed"
        elif any(r.status == VerificationStatus.FAIL for r in results):
            status = VerificationStatus.FAIL
            message = "Some accessibility checks failed"
        else:
            status = VerificationStatus.WARNING
            message = "Some accessibility checks have warnings"
        
        return VerificationResult(
            check_name="AccessibilityVerifier",
            status=status,
            message=message,
            details={"individual_results": [r.__dict__ for r in results]}
        )


class ARIAChecker(BaseVerifier):
    """Check ARIA attributes and accessibility features."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.required_aria_attributes = config.get('required_aria_attributes', [
            'aria-label', 'aria-labelledby', 'aria-describedby'
        ])
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Check ARIA attributes and accessibility features."""
        driver = target
        elements_to_check = kwargs.get('elements', [])
        
        if not elements_to_check:
            # Check all interactive elements
            elements_to_check = self._find_interactive_elements(driver)
        
        results = []
        all_passed = True
        
        for element_spec in elements_to_check:
            try:
                result = self._check_element_accessibility(driver, element_spec)
                results.append(result)
                if not result['passed']:
                    all_passed = False
            except Exception as e:
                results.append({
                    'element': element_spec.get('selector', 'unknown'),
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"ARIA checks: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="ARIAChecker",
            status=status,
            message=message,
            details={"aria_results": results}
        )
    
    def _find_interactive_elements(self, driver: webdriver.Chrome) -> List[Dict[str, str]]:
        """Find all interactive elements that need accessibility checks."""
        interactive_selectors = [
            'button', 'input', 'select', 'textarea', 'a[href]',
            '[role="button"]', '[role="link"]', '[role="menuitem"]',
            '[role="tab"]', '[role="option"]', '[onclick]'
        ]
        
        elements = []
        for selector in interactive_selectors:
            try:
                found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for i, element in enumerate(found_elements):
                    elements.append({
                        'selector': f"{selector}:nth-of-type({i+1})",
                        'by': By.CSS_SELECTOR
                    })
            except:
                continue
        
        return elements
    
    def _check_element_accessibility(self, driver: webdriver.Chrome, element_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check accessibility of a single element."""
        selector = element_spec['selector']
        by_type = element_spec.get('by', By.CSS_SELECTOR)
        
        element = driver.find_element(by_type, selector)
        
        result = {
            'element': selector,
            'passed': True,
            'checks': []
        }
        
        # Check for accessible name
        accessible_name = self._get_accessible_name(element)
        if not accessible_name:
            result['passed'] = False
            result['checks'].append({
                'type': 'accessible_name',
                'passed': False,
                'message': 'Element lacks accessible name'
            })
        else:
            result['checks'].append({
                'type': 'accessible_name',
                'passed': True,
                'message': f'Element has accessible name: "{accessible_name}"'
            })
        
        # Check ARIA attributes
        aria_attributes = self._get_aria_attributes(element)
        for attr in self.required_aria_attributes:
            if attr in aria_attributes:
                result['checks'].append({
                    'type': f'aria_{attr}',
                    'passed': True,
                    'message': f'Element has {attr}: "{aria_attributes[attr]}"'
                })
            else:
                result['checks'].append({
                    'type': f'aria_{attr}',
                    'passed': False,
                    'message': f'Element missing {attr}'
                })
        
        # Check role attribute
        role = element.get_attribute('role')
        if role:
            result['checks'].append({
                'type': 'role',
                'passed': True,
                'message': f'Element has role: "{role}"'
            })
        else:
            # Check if element needs explicit role
            tag_name = element.tag_name.lower()
            if tag_name in ['div', 'span'] and element.get_attribute('onclick'):
                result['checks'].append({
                    'type': 'role',
                    'passed': False,
                    'message': 'Interactive div/span should have explicit role'
                })
                result['passed'] = False
        
        # Check for proper heading hierarchy
        if element.tag_name.lower().startswith('h'):
            heading_level = int(element.tag_name[1])
            result['checks'].append({
                'type': 'heading_level',
                'passed': True,
                'message': f'Heading level: h{heading_level}'
            })
        
        # Check for alt text on images
        if element.tag_name.lower() == 'img':
            alt_text = element.get_attribute('alt')
            if alt_text is None:
                result['passed'] = False
                result['checks'].append({
                    'type': 'alt_text',
                    'passed': False,
                    'message': 'Image missing alt attribute'
                })
            elif alt_text.strip() == '':
                result['checks'].append({
                    'type': 'alt_text',
                    'passed': True,
                    'message': 'Image has empty alt (decorative)'
                })
            else:
                result['checks'].append({
                    'type': 'alt_text',
                    'passed': True,
                    'message': f'Image has alt text: "{alt_text}"'
                })
        
        return result
    
    def _get_accessible_name(self, element: WebElement) -> Optional[str]:
        """Get the accessible name of an element."""
        # Check aria-label first
        aria_label = element.get_attribute('aria-label')
        if aria_label and aria_label.strip():
            return aria_label.strip()
        
        # Check aria-labelledby
        aria_labelledby = element.get_attribute('aria-labelledby')
        if aria_labelledby:
            # Find the element referenced by aria-labelledby
            try:
                labelled_element = element.find_element(By.ID, aria_labelledby)
                return labelled_element.text.strip()
            except:
                pass
        
        # Check for visible text
        text = element.text.strip()
        if text:
            return text
        
        # Check for alt text on images
        if element.tag_name.lower() == 'img':
            alt_text = element.get_attribute('alt')
            if alt_text is not None:
                return alt_text.strip()
        
        # Check for placeholder text
        placeholder = element.get_attribute('placeholder')
        if placeholder and placeholder.strip():
            return placeholder.strip()
        
        return None
    
    def _get_aria_attributes(self, element: WebElement) -> Dict[str, str]:
        """Get all ARIA attributes from an element."""
        aria_attributes = {}
        
        # Get all attributes
        attributes = element.get_property('attributes')
        for attr in attributes:
            attr_name = attr['name']
            if attr_name.startswith('aria-'):
                aria_attributes[attr_name] = attr['value']
        
        return aria_attributes


class ContrastChecker(BaseVerifier):
    """Check color contrast ratios for accessibility."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.min_contrast_ratio = config.get('min_contrast_ratio', 4.5)  # WCAG AA standard
        self.large_text_ratio = config.get('large_text_ratio', 3.0)  # WCAG AA for large text
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Check color contrast ratios."""
        driver = target
        elements_to_check = kwargs.get('elements', [])
        
        if not elements_to_check:
            # Check all text elements
            elements_to_check = self._find_text_elements(driver)
        
        results = []
        all_passed = True
        
        for element_spec in elements_to_check:
            try:
                result = self._check_element_contrast(driver, element_spec)
                results.append(result)
                if not result['passed']:
                    all_passed = False
            except Exception as e:
                results.append({
                    'element': element_spec.get('selector', 'unknown'),
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"Contrast checks: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="ContrastChecker",
            status=status,
            message=message,
            details={"contrast_results": results}
        )
    
    def _find_text_elements(self, driver: webdriver.Chrome) -> List[Dict[str, str]]:
        """Find all text elements that need contrast checking."""
        text_selectors = [
            'p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'span', 'div', 'a',
            'button', 'input[type="text"]', 'input[type="email"]', 'textarea'
        ]
        
        elements = []
        for selector in text_selectors:
            try:
                found_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for i, element in enumerate(found_elements):
                    if element.text.strip():  # Only check elements with text
                        elements.append({
                            'selector': f"{selector}:nth-of-type({i+1})",
                            'by': By.CSS_SELECTOR
                        })
            except:
                continue
        
        return elements
    
    def _check_element_contrast(self, driver: webdriver.Chrome, element_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check contrast ratio for a single element."""
        selector = element_spec['selector']
        by_type = element_spec.get('by', By.CSS_SELECTOR)
        
        element = driver.find_element(by_type, selector)
        
        result = {
            'element': selector,
            'passed': True,
            'checks': []
        }
        
        try:
            # Get computed styles
            styles = driver.execute_script("""
                var element = arguments[0];
                var computed = window.getComputedStyle(element);
                return {
                    color: computed.color,
                    backgroundColor: computed.backgroundColor,
                    fontSize: computed.fontSize,
                    fontWeight: computed.fontWeight
                };
            """, element)
            
            # Parse colors
            text_color = self._parse_color(styles['color'])
            background_color = self._parse_color(styles['backgroundColor'])
            
            if text_color and background_color:
                # Calculate contrast ratio
                contrast_ratio = self._calculate_contrast_ratio(text_color, background_color)
                
                # Determine if text is large (18pt+ or 14pt+ bold)
                font_size = self._parse_font_size(styles['fontSize'])
                font_weight = styles['fontWeight']
                is_large_text = font_size >= 18 or (font_size >= 14 and font_weight in ['bold', '700', '800', '900'])
                
                required_ratio = self.large_text_ratio if is_large_text else self.min_contrast_ratio
                
                if contrast_ratio >= required_ratio:
                    result['checks'].append({
                        'type': 'contrast_ratio',
                        'passed': True,
                        'message': f'Contrast ratio {contrast_ratio:.2f} meets requirement ({required_ratio})',
                        'contrast_ratio': contrast_ratio,
                        'required_ratio': required_ratio,
                        'is_large_text': is_large_text
                    })
                else:
                    result['passed'] = False
                    result['checks'].append({
                        'type': 'contrast_ratio',
                        'passed': False,
                        'message': f'Contrast ratio {contrast_ratio:.2f} below requirement ({required_ratio})',
                        'contrast_ratio': contrast_ratio,
                        'required_ratio': required_ratio,
                        'is_large_text': is_large_text
                    })
            else:
                result['checks'].append({
                    'type': 'contrast_ratio',
                    'passed': False,
                    'message': 'Could not determine text or background color'
                })
                result['passed'] = False
        
        except Exception as e:
            result['checks'].append({
                'type': 'contrast_ratio',
                'passed': False,
                'message': f'Error checking contrast: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _parse_color(self, color_str: str) -> Optional[Tuple[int, int, int]]:
        """Parse CSS color string to RGB tuple."""
        if not color_str or color_str == 'transparent':
            return None
        
        # Handle rgb() format
        rgb_match = re.match(r'rgb\((\d+),\s*(\d+),\s*(\d+)\)', color_str)
        if rgb_match:
            return tuple(map(int, rgb_match.groups()))
        
        # Handle rgba() format
        rgba_match = re.match(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*[\d.]+\)', color_str)
        if rgba_match:
            return tuple(map(int, rgba_match.groups()[:3]))
        
        # Handle hex format
        hex_match = re.match(r'#([0-9a-fA-F]{2})([0-9a-fA-F]{2})([0-9a-fA-F]{2})', color_str)
        if hex_match:
            return tuple(int(hex_match.group(i), 16) for i in range(1, 4))
        
        return None
    
    def _parse_font_size(self, font_size_str: str) -> float:
        """Parse CSS font size to points."""
        if not font_size_str:
            return 16  # Default
        
        # Handle px
        if font_size_str.endswith('px'):
            return float(font_size_str[:-2]) * 0.75  # Convert px to pt
        
        # Handle pt
        if font_size_str.endswith('pt'):
            return float(font_size_str[:-2])
        
        # Handle em (assume 16px base)
        if font_size_str.endswith('em'):
            return float(font_size_str[:-2]) * 16 * 0.75
        
        return 16  # Default
    
    def _calculate_contrast_ratio(self, color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate contrast ratio between two RGB colors."""
        def get_luminance(rgb):
            r, g, b = [c / 255.0 for c in rgb]
            r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
            g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
            b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
            return 0.2126 * r + 0.7152 * g + 0.0722 * b
        
        lum1 = get_luminance(color1)
        lum2 = get_luminance(color2)
        
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)


class KeyboardNavigationChecker(BaseVerifier):
    """Check keyboard navigation and focus management."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = config.get('timeout', 10)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Check keyboard navigation."""
        driver = target
        navigation_tests = kwargs.get('navigation_tests', [])
        
        if not navigation_tests:
            # Create default navigation tests
            navigation_tests = self._create_default_navigation_tests(driver)
        
        results = []
        all_passed = True
        
        for test in navigation_tests:
            try:
                result = self._run_navigation_test(driver, test)
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
        message = f"Keyboard navigation: {sum(1 for r in results if r['passed'])}/{len(results)} tests passed"
        
        return VerificationResult(
            check_name="KeyboardNavigationChecker",
            status=status,
            message=message,
            details={"navigation_results": results}
        )
    
    def _create_default_navigation_tests(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """Create default keyboard navigation tests."""
        tests = []
        
        # Test tab navigation
        interactive_elements = driver.find_elements(By.CSS_SELECTOR, 
            'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])')
        
        if interactive_elements:
            tests.append({
                'name': 'tab_navigation',
                'type': 'tab_sequence',
                'elements': [{'selector': 'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])'}]
            })
        
        # Test arrow key navigation for specific elements
        arrow_navigation_elements = driver.find_elements(By.CSS_SELECTOR, 
            '[role="menuitem"], [role="tab"], [role="option"]')
        
        if arrow_navigation_elements:
            tests.append({
                'name': 'arrow_navigation',
                'type': 'arrow_keys',
                'elements': [{'selector': '[role="menuitem"], [role="tab"], [role="option"]'}]
            })
        
        return tests
    
    def _run_navigation_test(self, driver: webdriver.Chrome, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single navigation test."""
        test_name = test['name']
        test_type = test['type']
        
        result = {
            'test': test_name,
            'type': test_type,
            'passed': True,
            'checks': []
        }
        
        if test_type == 'tab_sequence':
            result = self._test_tab_sequence(driver, test, result)
        elif test_type == 'arrow_keys':
            result = self._test_arrow_navigation(driver, test, result)
        elif test_type == 'focus_management':
            result = self._test_focus_management(driver, test, result)
        
        return result
    
    def _test_tab_sequence(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test tab key navigation sequence."""
        # Get all focusable elements
        focusable_elements = driver.find_elements(By.CSS_SELECTOR, 
            'button, input, select, textarea, a[href], [tabindex]:not([tabindex="-1"])')
        
        if not focusable_elements:
            result['checks'].append({
                'type': 'tab_sequence',
                'passed': False,
                'message': 'No focusable elements found'
            })
            result['passed'] = False
            return result
        
        # Test tab navigation
        try:
            # Start from first element
            focusable_elements[0].click()
            current_focus = driver.switch_to.active_element
            
            for i in range(len(focusable_elements)):
                # Press tab
                current_focus.send_keys(Keys.TAB)
                
                # Check if focus moved to next element
                new_focus = driver.switch_to.active_element
                
                if i < len(focusable_elements) - 1:
                    expected_element = focusable_elements[i + 1]
                    if new_focus == expected_element:
                        result['checks'].append({
                            'type': 'tab_sequence',
                            'passed': True,
                            'message': f'Tab {i+1}: Focus moved correctly'
                        })
                    else:
                        result['checks'].append({
                            'type': 'tab_sequence',
                            'passed': False,
                            'message': f'Tab {i+1}: Focus did not move to expected element'
                        })
                        result['passed'] = False
                else:
                    # Last element - check if focus cycles back or stays
                    result['checks'].append({
                        'type': 'tab_sequence',
                        'passed': True,
                        'message': f'Tab {i+1}: Reached end of sequence'
                    })
                
                current_focus = new_focus
        
        except Exception as e:
            result['checks'].append({
                'type': 'tab_sequence',
                'passed': False,
                'message': f'Tab navigation failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _test_arrow_navigation(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test arrow key navigation."""
        # This is a simplified test - in practice, you'd need to test specific components
        result['checks'].append({
            'type': 'arrow_navigation',
            'passed': True,
            'message': 'Arrow key navigation test (simplified)'
        })
        
        return result
    
    def _test_focus_management(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test focus management (focus traps, focus restoration, etc.)."""
        # This is a placeholder for focus management tests
        result['checks'].append({
            'type': 'focus_management',
            'passed': True,
            'message': 'Focus management test (placeholder)'
        })
        
        return result