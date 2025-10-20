"""
Interaction verification tools for GUI testing.
"""

import time
from typing import Any, Dict, List, Optional, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from .core import BaseVerifier, VerificationResult, VerificationStatus


class InteractionVerifier(BaseVerifier):
    """Main interaction verification class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.click_tester = ClickTester(config)
        self.form_validator = FormValidator(config)
        self.hover_tester = HoverTester(config)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Run interaction verification checks."""
        checks = kwargs.get('checks', ['click', 'form', 'hover'])
        results = []
        
        for check in checks:
            if check == 'click':
                result = self.click_tester.verify(target, **kwargs)
                results.append(result)
            elif check == 'form':
                result = self.form_validator.verify(target, **kwargs)
                results.append(result)
            elif check == 'hover':
                result = self.hover_tester.verify(target, **kwargs)
                results.append(result)
        
        # Determine overall status
        if all(r.status == VerificationStatus.PASS for r in results):
            status = VerificationStatus.PASS
            message = "All interaction checks passed"
        elif any(r.status == VerificationStatus.FAIL for r in results):
            status = VerificationStatus.FAIL
            message = "Some interaction checks failed"
        else:
            status = VerificationStatus.WARNING
            message = "Some interaction checks have warnings"
        
        return VerificationResult(
            check_name="InteractionVerifier",
            status=status,
            message=message,
            details={"individual_results": [r.__dict__ for r in results]}
        )


class ClickTester(BaseVerifier):
    """Test click interactions and their effects."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = config.get('timeout', 10)
        self.wait_time = config.get('wait_time', 1)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Test click interactions."""
        driver = target
        click_tests = kwargs.get('click_tests', [])
        
        if not click_tests:
            return VerificationResult(
                check_name="ClickTester",
                status=VerificationStatus.WARNING,
                message="No click tests specified"
            )
        
        results = []
        all_passed = True
        
        for test in click_tests:
            try:
                result = self._run_click_test(driver, test)
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
        message = f"Click tests: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="ClickTester",
            status=status,
            message=message,
            details={"click_results": results}
        )
    
    def _run_click_test(self, driver: webdriver.Chrome, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single click test."""
        test_name = test['name']
        selector = test['selector']
        by_type = test.get('by', By.CSS_SELECTOR)
        expected_result = test.get('expected_result', {})
        
        result = {
            'test': test_name,
            'passed': True,
            'checks': []
        }
        
        try:
            # Find the element
            element = driver.find_element(by_type, selector)
            
            # Record initial state
            initial_state = self._capture_element_state(driver, element, test)
            
            # Perform click
            element.click()
            time.sleep(self.wait_time)
            
            # Record post-click state
            post_click_state = self._capture_element_state(driver, element, test)
            
            # Check expected results
            result = self._check_click_results(driver, test, initial_state, post_click_state, result)
            
        except Exception as e:
            result['checks'].append({
                'type': 'click_execution',
                'passed': False,
                'message': f'Click test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _capture_element_state(self, driver: webdriver.Chrome, element: WebElement, test: Dict[str, Any]) -> Dict[str, Any]:
        """Capture the current state of an element."""
        state = {
            'visible': element.is_displayed(),
            'enabled': element.is_enabled(),
            'text': element.text,
            'classes': element.get_attribute('class'),
            'url': driver.current_url,
            'title': driver.title
        }
        
        # Capture specific attributes if specified
        attributes_to_check = test.get('attributes_to_check', [])
        for attr in attributes_to_check:
            state[attr] = element.get_attribute(attr)
        
        # Capture parent/child states if specified
        if test.get('check_parent', False):
            parent = element.find_element(By.XPATH, '..')
            state['parent_classes'] = parent.get_attribute('class')
            state['parent_visible'] = parent.is_displayed()
        
        return state
    
    def _check_click_results(self, driver: webdriver.Chrome, test: Dict[str, Any], 
                           initial_state: Dict[str, Any], post_click_state: Dict[str, Any], 
                           result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if click produced expected results."""
        expected_result = test.get('expected_result', {})
        
        # Check visibility changes
        if 'should_hide' in expected_result:
            if expected_result['should_hide']:
                if post_click_state['visible']:
                    result['checks'].append({
                        'type': 'visibility_change',
                        'passed': False,
                        'message': 'Element should have been hidden but is still visible'
                    })
                    result['passed'] = False
                else:
                    result['checks'].append({
                        'type': 'visibility_change',
                        'passed': True,
                        'message': 'Element was hidden as expected'
                    })
        
        # Check class changes
        if 'expected_classes' in expected_result:
            expected_classes = expected_result['expected_classes']
            actual_classes = post_click_state['classes']
            
            for expected_class in expected_classes:
                if expected_class in actual_classes:
                    result['checks'].append({
                        'type': 'class_change',
                        'passed': True,
                        'message': f'Element has expected class: {expected_class}'
                    })
                else:
                    result['checks'].append({
                        'type': 'class_change',
                        'passed': False,
                        'message': f'Element missing expected class: {expected_class}'
                    })
                    result['passed'] = False
        
        # Check text changes
        if 'expected_text' in expected_result:
            expected_text = expected_result['expected_text']
            actual_text = post_click_state['text']
            
            if expected_text in actual_text:
                result['checks'].append({
                    'type': 'text_change',
                    'passed': True,
                    'message': f'Element text contains expected text: {expected_text}'
                })
            else:
                result['checks'].append({
                    'type': 'text_change',
                    'passed': False,
                    'message': f'Element text does not contain expected text: {expected_text}'
                })
                result['passed'] = False
        
        # Check URL changes
        if 'expected_url_change' in expected_result:
            expected_url_change = expected_result['expected_url_change']
            initial_url = initial_state['url']
            post_click_url = post_click_state['url']
            
            if expected_url_change:
                if initial_url != post_click_url:
                    result['checks'].append({
                        'type': 'url_change',
                        'passed': True,
                        'message': 'URL changed as expected'
                    })
                else:
                    result['checks'].append({
                        'type': 'url_change',
                        'passed': False,
                        'message': 'URL did not change as expected'
                    })
                    result['passed'] = False
        
        # Check for new elements appearing
        if 'expected_new_elements' in expected_result:
            new_element_selectors = expected_result['expected_new_elements']
            
            for selector in new_element_selectors:
                try:
                    new_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if new_element.is_displayed():
                        result['checks'].append({
                            'type': 'new_element',
                            'passed': True,
                            'message': f'New element appeared: {selector}'
                        })
                    else:
                        result['checks'].append({
                            'type': 'new_element',
                            'passed': False,
                            'message': f'New element found but not visible: {selector}'
                        })
                        result['passed'] = False
                except:
                    result['checks'].append({
                        'type': 'new_element',
                        'passed': False,
                        'message': f'New element not found: {selector}'
                    })
                    result['passed'] = False
        
        return result


class FormValidator(BaseVerifier):
    """Validate form interactions and validation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = config.get('timeout', 10)
        self.wait_time = config.get('wait_time', 1)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Validate form interactions."""
        driver = target
        form_tests = kwargs.get('form_tests', [])
        
        if not form_tests:
            # Find all forms and create default tests
            form_tests = self._create_default_form_tests(driver)
        
        results = []
        all_passed = True
        
        for test in form_tests:
            try:
                result = self._run_form_test(driver, test)
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
        message = f"Form tests: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="FormValidator",
            status=status,
            message=message,
            details={"form_results": results}
        )
    
    def _create_default_form_tests(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """Create default form validation tests."""
        forms = driver.find_elements(By.TAG_NAME, 'form')
        tests = []
        
        for i, form in enumerate(forms):
            form_id = form.get_attribute('id') or f'form_{i}'
            
            # Test form submission
            tests.append({
                'name': f'form_submission_{form_id}',
                'form_selector': f'form#{form_id}' if form.get_attribute('id') else f'form:nth-of-type({i+1})',
                'type': 'submission'
            })
            
            # Test required field validation
            required_fields = form.find_elements(By.CSS_SELECTOR, 'input[required], select[required], textarea[required]')
            if required_fields:
                tests.append({
                    'name': f'required_validation_{form_id}',
                    'form_selector': f'form#{form_id}' if form.get_attribute('id') else f'form:nth-of-type({i+1})',
                    'type': 'required_validation',
                    'required_fields': [{'selector': f'input[required]:nth-of-type({j+1})', 'by': By.CSS_SELECTOR} for j in range(len(required_fields))]
                })
        
        return tests
    
    def _run_form_test(self, driver: webdriver.Chrome, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single form test."""
        test_name = test['name']
        test_type = test['type']
        
        result = {
            'test': test_name,
            'type': test_type,
            'passed': True,
            'checks': []
        }
        
        if test_type == 'submission':
            result = self._test_form_submission(driver, test, result)
        elif test_type == 'required_validation':
            result = self._test_required_validation(driver, test, result)
        elif test_type == 'field_validation':
            result = self._test_field_validation(driver, test, result)
        
        return result
    
    def _test_form_submission(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test form submission."""
        form_selector = test['form_selector']
        
        try:
            form = driver.find_element(By.CSS_SELECTOR, form_selector)
            
            # Fill out form if test data provided
            if 'test_data' in test:
                self._fill_form_data(driver, form, test['test_data'])
            
            # Submit form
            submit_button = form.find_element(By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"], button:not([type])')
            submit_button.click()
            time.sleep(self.wait_time)
            
            # Check for success indicators
            expected_result = test.get('expected_result', {})
            
            if 'success_url' in expected_result:
                current_url = driver.current_url
                if expected_result['success_url'] in current_url:
                    result['checks'].append({
                        'type': 'url_redirect',
                        'passed': True,
                        'message': f'Redirected to expected URL: {current_url}'
                    })
                else:
                    result['checks'].append({
                        'type': 'url_redirect',
                        'passed': False,
                        'message': f'Expected URL containing {expected_result["success_url"]}, got {current_url}'
                    })
                    result['passed'] = False
            
            if 'success_message' in expected_result:
                success_message = expected_result['success_message']
                try:
                    message_element = driver.find_element(By.XPATH, f"//*[contains(text(), '{success_message}')]")
                    if message_element.is_displayed():
                        result['checks'].append({
                            'type': 'success_message',
                            'passed': True,
                            'message': f'Success message displayed: {success_message}'
                        })
                    else:
                        result['checks'].append({
                            'type': 'success_message',
                            'passed': False,
                            'message': f'Success message found but not visible: {success_message}'
                        })
                        result['passed'] = False
                except:
                    result['checks'].append({
                        'type': 'success_message',
                        'passed': False,
                        'message': f'Success message not found: {success_message}'
                    })
                    result['passed'] = False
        
        except Exception as e:
            result['checks'].append({
                'type': 'form_submission',
                'passed': False,
                'message': f'Form submission test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _test_required_validation(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test required field validation."""
        form_selector = test['form_selector']
        required_fields = test.get('required_fields', [])
        
        try:
            form = driver.find_element(By.CSS_SELECTOR, form_selector)
            
            # Try to submit form without filling required fields
            submit_button = form.find_element(By.CSS_SELECTOR, 'input[type="submit"], button[type="submit"], button:not([type])')
            submit_button.click()
            time.sleep(self.wait_time)
            
            # Check for validation messages
            for field_spec in required_fields:
                field_selector = field_spec['selector']
                field_by = field_spec.get('by', By.CSS_SELECTOR)
                
                try:
                    field = form.find_element(field_by, field_selector)
                    
                    # Check if field has validation message
                    validation_message = field.get_attribute('validationMessage')
                    if validation_message:
                        result['checks'].append({
                            'type': 'required_validation',
                            'passed': True,
                            'message': f'Required field validation working: {field_selector}'
                        })
                    else:
                        # Check for custom validation message
                        try:
                            error_element = field.find_element(By.XPATH, 'following-sibling::*[contains(@class, "error") or contains(@class, "invalid")]')
                            if error_element.is_displayed():
                                result['checks'].append({
                                    'type': 'required_validation',
                                    'passed': True,
                                    'message': f'Custom validation message displayed for: {field_selector}'
                                })
                            else:
                                result['checks'].append({
                                    'type': 'required_validation',
                                    'passed': False,
                                    'message': f'No validation message for required field: {field_selector}'
                                })
                                result['passed'] = False
                        except:
                            result['checks'].append({
                                'type': 'required_validation',
                                'passed': False,
                                'message': f'No validation message for required field: {field_selector}'
                            })
                            result['passed'] = False
                
                except Exception as e:
                    result['checks'].append({
                        'type': 'required_validation',
                        'passed': False,
                        'message': f'Error checking field {field_selector}: {str(e)}'
                    })
                    result['passed'] = False
        
        except Exception as e:
            result['checks'].append({
                'type': 'required_validation',
                'passed': False,
                'message': f'Required validation test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _test_field_validation(self, driver: webdriver.Chrome, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test individual field validation."""
        field_selector = test['field_selector']
        field_by = test.get('by', By.CSS_SELECTOR)
        validation_tests = test.get('validation_tests', [])
        
        try:
            field = driver.find_element(field_by, field_selector)
            
            for validation_test in validation_tests:
                test_value = validation_test['value']
                expected_valid = validation_test['expected_valid']
                
                # Clear field and enter test value
                field.clear()
                field.send_keys(test_value)
                
                # Trigger validation (blur event)
                field.send_keys(Keys.TAB)
                time.sleep(0.5)
                
                # Check validation state
                is_valid = field.get_attribute('validity')['valid'] if field.get_attribute('validity') else True
                
                if is_valid == expected_valid:
                    result['checks'].append({
                        'type': 'field_validation',
                        'passed': True,
                        'message': f'Validation correct for value "{test_value}": {is_valid}'
                    })
                else:
                    result['checks'].append({
                        'type': 'field_validation',
                        'passed': False,
                        'message': f'Validation incorrect for value "{test_value}": expected {expected_valid}, got {is_valid}'
                    })
                    result['passed'] = False
        
        except Exception as e:
            result['checks'].append({
                'type': 'field_validation',
                'passed': False,
                'message': f'Field validation test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _fill_form_data(self, driver: webdriver.Chrome, form: WebElement, test_data: Dict[str, str]):
        """Fill form with test data."""
        for field_name, value in test_data.items():
            try:
                field = form.find_element(By.NAME, field_name)
                field.clear()
                field.send_keys(value)
            except:
                # Try by ID
                try:
                    field = form.find_element(By.ID, field_name)
                    field.clear()
                    field.send_keys(value)
                except:
                    # Try by CSS selector
                    try:
                        field = form.find_element(By.CSS_SELECTOR, f'[name="{field_name}"]')
                        field.clear()
                        field.send_keys(value)
                    except:
                        pass  # Skip if field not found


class HoverTester(BaseVerifier):
    """Test hover interactions and their effects."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = config.get('timeout', 10)
        self.hover_delay = config.get('hover_delay', 0.5)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Test hover interactions."""
        driver = target
        hover_tests = kwargs.get('hover_tests', [])
        
        if not hover_tests:
            return VerificationResult(
                check_name="HoverTester",
                status=VerificationStatus.WARNING,
                message="No hover tests specified"
            )
        
        results = []
        all_passed = True
        
        for test in hover_tests:
            try:
                result = self._run_hover_test(driver, test)
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
        message = f"Hover tests: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="HoverTester",
            status=status,
            message=message,
            details={"hover_results": results}
        )
    
    def _run_hover_test(self, driver: webdriver.Chrome, test: Dict[str, Any]) -> Dict[str, Any]:
        """Run a single hover test."""
        test_name = test['name']
        selector = test['selector']
        by_type = test.get('by', By.CSS_SELECTOR)
        expected_result = test.get('expected_result', {})
        
        result = {
            'test': test_name,
            'passed': True,
            'checks': []
        }
        
        try:
            # Find the element
            element = driver.find_element(by_type, selector)
            
            # Record initial state
            initial_state = self._capture_hover_state(driver, test)
            
            # Perform hover
            actions = ActionChains(driver)
            actions.move_to_element(element).perform()
            time.sleep(self.hover_delay)
            
            # Record post-hover state
            post_hover_state = self._capture_hover_state(driver, test)
            
            # Check expected results
            result = self._check_hover_results(test, initial_state, post_hover_state, result)
            
        except Exception as e:
            result['checks'].append({
                'type': 'hover_execution',
                'passed': False,
                'message': f'Hover test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _capture_hover_state(self, driver: webdriver.Chrome, test: Dict[str, Any]) -> Dict[str, Any]:
        """Capture the current state for hover testing."""
        state = {
            'url': driver.current_url,
            'title': driver.title
        }
        
        # Check for tooltip or popup elements
        tooltip_selectors = test.get('tooltip_selectors', [])
        for selector in tooltip_selectors:
            try:
                tooltip = driver.find_element(By.CSS_SELECTOR, selector)
                state[f'tooltip_{selector}'] = tooltip.is_displayed()
            except:
                state[f'tooltip_{selector}'] = False
        
        # Check for hover effects on the target element
        target_selector = test['selector']
        try:
            target_element = driver.find_element(By.CSS_SELECTOR, target_selector)
            state['target_classes'] = target_element.get_attribute('class')
            state['target_visible'] = target_element.is_displayed()
        except:
            state['target_classes'] = ''
            state['target_visible'] = False
        
        return state
    
    def _check_hover_results(self, test: Dict[str, Any], initial_state: Dict[str, Any], 
                           post_hover_state: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Check if hover produced expected results."""
        expected_result = test.get('expected_result', {})
        
        # Check for tooltip appearance
        if 'tooltip_should_appear' in expected_result:
            tooltip_selector = expected_result['tooltip_should_appear']
            tooltip_key = f'tooltip_{tooltip_selector}'
            
            if tooltip_key in post_hover_state and post_hover_state[tooltip_key]:
                result['checks'].append({
                    'type': 'tooltip_appearance',
                    'passed': True,
                    'message': f'Tooltip appeared: {tooltip_selector}'
                })
            else:
                result['checks'].append({
                    'type': 'tooltip_appearance',
                    'passed': False,
                    'message': f'Tooltip did not appear: {tooltip_selector}'
                })
                result['passed'] = False
        
        # Check for class changes
        if 'expected_classes' in expected_result:
            expected_classes = expected_result['expected_classes']
            actual_classes = post_hover_state['target_classes']
            
            for expected_class in expected_classes:
                if expected_class in actual_classes:
                    result['checks'].append({
                        'type': 'class_change',
                        'passed': True,
                        'message': f'Element has expected class after hover: {expected_class}'
                    })
                else:
                    result['checks'].append({
                        'type': 'class_change',
                        'passed': False,
                        'message': f'Element missing expected class after hover: {expected_class}'
                    })
                    result['passed'] = False
        
        # Check for new elements appearing
        if 'expected_new_elements' in expected_result:
            new_element_selectors = expected_result['expected_new_elements']
            
            for selector in new_element_selectors:
                try:
                    new_element = driver.find_element(By.CSS_SELECTOR, selector)
                    if new_element.is_displayed():
                        result['checks'].append({
                            'type': 'new_element',
                            'passed': True,
                            'message': f'New element appeared on hover: {selector}'
                        })
                    else:
                        result['checks'].append({
                            'type': 'new_element',
                            'passed': False,
                            'message': f'New element found but not visible on hover: {selector}'
                        })
                        result['passed'] = False
                except:
                    result['checks'].append({
                        'type': 'new_element',
                        'passed': False,
                        'message': f'New element not found on hover: {selector}'
                    })
                    result['passed'] = False
        
        return result