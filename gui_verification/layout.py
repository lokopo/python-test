"""
Layout verification tools for GUI testing.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.action_chains import ActionChains

from .core import BaseVerifier, VerificationResult, VerificationStatus


class LayoutVerifier(BaseVerifier):
    """Main layout verification class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.position_checker = PositionChecker(config)
        self.size_checker = SizeChecker(config)
        self.alignment_checker = AlignmentChecker(config)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Run layout verification checks."""
        checks = kwargs.get('checks', ['position', 'size', 'alignment'])
        results = []
        
        for check in checks:
            if check == 'position':
                result = self.position_checker.verify(target, **kwargs)
                results.append(result)
            elif check == 'size':
                result = self.size_checker.verify(target, **kwargs)
                results.append(result)
            elif check == 'alignment':
                result = self.alignment_checker.verify(target, **kwargs)
                results.append(result)
        
        # Determine overall status
        if all(r.status == VerificationStatus.PASS for r in results):
            status = VerificationStatus.PASS
            message = "All layout checks passed"
        elif any(r.status == VerificationStatus.FAIL for r in results):
            status = VerificationStatus.FAIL
            message = "Some layout checks failed"
        else:
            status = VerificationStatus.WARNING
            message = "Some layout checks have warnings"
        
        return VerificationResult(
            check_name="LayoutVerifier",
            status=status,
            message=message,
            details={"individual_results": [r.__dict__ for r in results]}
        )


class PositionChecker(BaseVerifier):
    """Verify element positions and positioning."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.tolerance = config.get('position_tolerance', 5)  # Pixel tolerance for position checks
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Verify element positions."""
        driver = target
        position_checks = kwargs.get('position_checks', [])
        
        if not position_checks:
            return VerificationResult(
                check_name="PositionChecker",
                status=VerificationStatus.WARNING,
                message="No position checks specified"
            )
        
        results = []
        all_passed = True
        
        for check in position_checks:
            try:
                result = self._check_position(driver, check)
                results.append(result)
                if not result['passed']:
                    all_passed = False
            except Exception as e:
                results.append({
                    'element': check.get('selector', 'unknown'),
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"Position checks: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="PositionChecker",
            status=status,
            message=message,
            details={"position_results": results}
        )
    
    def _check_position(self, driver: webdriver.Chrome, check: Dict[str, Any]) -> Dict[str, Any]:
        """Check a single position requirement."""
        selector = check['selector']
        by_type = check.get('by', By.CSS_SELECTOR)
        
        element = driver.find_element(by_type, selector)
        bounds = self._get_element_bounds(element)
        
        result = {
            'element': selector,
            'bounds': bounds,
            'passed': True,
            'checks': []
        }
        
        # Check specific position requirements
        if 'expected_x' in check:
            expected_x = check['expected_x']
            actual_x = bounds['x']
            tolerance = check.get('tolerance', self.tolerance)
            
            if abs(actual_x - expected_x) > tolerance:
                result['passed'] = False
                result['checks'].append({
                    'type': 'x_position',
                    'expected': expected_x,
                    'actual': actual_x,
                    'difference': actual_x - expected_x,
                    'tolerance': tolerance,
                    'passed': False
                })
            else:
                result['checks'].append({
                    'type': 'x_position',
                    'expected': expected_x,
                    'actual': actual_x,
                    'difference': actual_x - expected_x,
                    'tolerance': tolerance,
                    'passed': True
                })
        
        if 'expected_y' in check:
            expected_y = check['expected_y']
            actual_y = bounds['y']
            tolerance = check.get('tolerance', self.tolerance)
            
            if abs(actual_y - expected_y) > tolerance:
                result['passed'] = False
                result['checks'].append({
                    'type': 'y_position',
                    'expected': expected_y,
                    'actual': actual_y,
                    'difference': actual_y - expected_y,
                    'tolerance': tolerance,
                    'passed': False
                })
            else:
                result['checks'].append({
                    'type': 'y_position',
                    'expected': expected_y,
                    'actual': actual_y,
                    'difference': actual_y - expected_y,
                    'tolerance': tolerance,
                    'passed': True
                })
        
        # Check relative positioning
        if 'relative_to' in check:
            relative_result = self._check_relative_position(driver, element, check['relative_to'])
            result['checks'].extend(relative_result['checks'])
            if not relative_result['passed']:
                result['passed'] = False
        
        return result
    
    def _check_relative_position(self, driver: webdriver.Chrome, element: WebElement, relative_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check position relative to another element."""
        relative_selector = relative_spec['selector']
        relative_by = relative_spec.get('by', By.CSS_SELECTOR)
        relative_element = driver.find_element(relative_by, relative_selector)
        relative_bounds = self._get_element_bounds(relative_element)
        element_bounds = self._get_element_bounds(element)
        
        result = {
            'passed': True,
            'checks': []
        }
        
        # Check if element is to the right of relative element
        if relative_spec.get('to_right_of', False):
            if element_bounds['x'] <= relative_bounds['x'] + relative_bounds['width']:
                result['passed'] = False
                result['checks'].append({
                    'type': 'to_right_of',
                    'passed': False,
                    'message': f"Element not to the right of {relative_selector}"
                })
            else:
                result['checks'].append({
                    'type': 'to_right_of',
                    'passed': True,
                    'message': f"Element is to the right of {relative_selector}"
                })
        
        # Check if element is below relative element
        if relative_spec.get('below', False):
            if element_bounds['y'] <= relative_bounds['y'] + relative_bounds['height']:
                result['passed'] = False
                result['checks'].append({
                    'type': 'below',
                    'passed': False,
                    'message': f"Element not below {relative_selector}"
                })
            else:
                result['checks'].append({
                    'type': 'below',
                    'passed': True,
                    'message': f"Element is below {relative_selector}"
                })
        
        return result
    
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


class SizeChecker(BaseVerifier):
    """Verify element sizes and dimensions."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.tolerance = config.get('size_tolerance', 5)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Verify element sizes."""
        driver = target
        size_checks = kwargs.get('size_checks', [])
        
        if not size_checks:
            return VerificationResult(
                check_name="SizeChecker",
                status=VerificationStatus.WARNING,
                message="No size checks specified"
            )
        
        results = []
        all_passed = True
        
        for check in size_checks:
            try:
                result = self._check_size(driver, check)
                results.append(result)
                if not result['passed']:
                    all_passed = False
            except Exception as e:
                results.append({
                    'element': check.get('selector', 'unknown'),
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"Size checks: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="SizeChecker",
            status=status,
            message=message,
            details={"size_results": results}
        )
    
    def _check_size(self, driver: webdriver.Chrome, check: Dict[str, Any]) -> Dict[str, Any]:
        """Check a single size requirement."""
        selector = check['selector']
        by_type = check.get('by', By.CSS_SELECTOR)
        
        element = driver.find_element(by_type, selector)
        bounds = self._get_element_bounds(element)
        
        result = {
            'element': selector,
            'bounds': bounds,
            'passed': True,
            'checks': []
        }
        
        # Check width
        if 'expected_width' in check:
            expected_width = check['expected_width']
            actual_width = bounds['width']
            tolerance = check.get('tolerance', self.tolerance)
            
            if abs(actual_width - expected_width) > tolerance:
                result['passed'] = False
                result['checks'].append({
                    'type': 'width',
                    'expected': expected_width,
                    'actual': actual_width,
                    'difference': actual_width - expected_width,
                    'tolerance': tolerance,
                    'passed': False
                })
            else:
                result['checks'].append({
                    'type': 'width',
                    'expected': expected_width,
                    'actual': actual_width,
                    'difference': actual_width - expected_width,
                    'tolerance': tolerance,
                    'passed': True
                })
        
        # Check height
        if 'expected_height' in check:
            expected_height = check['expected_height']
            actual_height = bounds['height']
            tolerance = check.get('tolerance', self.tolerance)
            
            if abs(actual_height - expected_height) > tolerance:
                result['passed'] = False
                result['checks'].append({
                    'type': 'height',
                    'expected': expected_height,
                    'actual': actual_height,
                    'difference': actual_height - expected_height,
                    'tolerance': tolerance,
                    'passed': False
                })
            else:
                result['checks'].append({
                    'type': 'height',
                    'expected': expected_height,
                    'actual': actual_height,
                    'difference': actual_height - expected_height,
                    'tolerance': tolerance,
                    'passed': True
                })
        
        # Check minimum size
        if 'min_width' in check:
            min_width = check['min_width']
            actual_width = bounds['width']
            
            if actual_width < min_width:
                result['passed'] = False
                result['checks'].append({
                    'type': 'min_width',
                    'expected': min_width,
                    'actual': actual_width,
                    'passed': False
                })
            else:
                result['checks'].append({
                    'type': 'min_width',
                    'expected': min_width,
                    'actual': actual_width,
                    'passed': True
                })
        
        if 'min_height' in check:
            min_height = check['min_height']
            actual_height = bounds['height']
            
            if actual_height < min_height:
                result['passed'] = False
                result['checks'].append({
                    'type': 'min_height',
                    'expected': min_height,
                    'actual': actual_height,
                    'passed': False
                })
            else:
                result['checks'].append({
                    'type': 'min_height',
                    'expected': min_height,
                    'actual': actual_height,
                    'passed': True
                })
        
        return result
    
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


class AlignmentChecker(BaseVerifier):
    """Verify element alignment and spacing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.tolerance = config.get('alignment_tolerance', 5)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Verify element alignment."""
        driver = target
        alignment_checks = kwargs.get('alignment_checks', [])
        
        if not alignment_checks:
            return VerificationResult(
                check_name="AlignmentChecker",
                status=VerificationStatus.WARNING,
                message="No alignment checks specified"
            )
        
        results = []
        all_passed = True
        
        for check in alignment_checks:
            try:
                result = self._check_alignment(driver, check)
                results.append(result)
                if not result['passed']:
                    all_passed = False
            except Exception as e:
                results.append({
                    'elements': check.get('elements', []),
                    'passed': False,
                    'error': str(e)
                })
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"Alignment checks: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="AlignmentChecker",
            status=status,
            message=message,
            details={"alignment_results": results}
        )
    
    def _check_alignment(self, driver: webdriver.Chrome, check: Dict[str, Any]) -> Dict[str, Any]:
        """Check alignment of multiple elements."""
        elements = check['elements']
        alignment_type = check.get('type', 'horizontal')  # horizontal, vertical, grid
        
        result = {
            'elements': elements,
            'alignment_type': alignment_type,
            'passed': True,
            'checks': []
        }
        
        if len(elements) < 2:
            result['checks'].append({
                'type': 'insufficient_elements',
                'passed': False,
                'message': 'Need at least 2 elements for alignment check'
            })
            result['passed'] = False
            return result
        
        # Get element bounds
        element_bounds = []
        for element_spec in elements:
            selector = element_spec['selector']
            by_type = element_spec.get('by', By.CSS_SELECTOR)
            element = driver.find_element(by_type, selector)
            bounds = self._get_element_bounds(element)
            element_bounds.append(bounds)
        
        if alignment_type == 'horizontal':
            result = self._check_horizontal_alignment(element_bounds, elements, result)
        elif alignment_type == 'vertical':
            result = self._check_vertical_alignment(element_bounds, elements, result)
        elif alignment_type == 'grid':
            result = self._check_grid_alignment(element_bounds, elements, check, result)
        
        return result
    
    def _check_horizontal_alignment(self, bounds_list: List[Dict], elements: List[Dict], result: Dict) -> Dict:
        """Check if elements are horizontally aligned."""
        # Check top alignment
        top_positions = [bounds['y'] for bounds in bounds_list]
        if len(set(top_positions)) == 1:
            result['checks'].append({
                'type': 'top_alignment',
                'passed': True,
                'message': 'All elements aligned at top'
            })
        else:
            max_diff = max(top_positions) - min(top_positions)
            if max_diff <= self.tolerance:
                result['checks'].append({
                    'type': 'top_alignment',
                    'passed': True,
                    'message': f'Top alignment within tolerance ({max_diff}px)'
                })
            else:
                result['checks'].append({
                    'type': 'top_alignment',
                    'passed': False,
                    'message': f'Top alignment exceeds tolerance ({max_diff}px > {self.tolerance}px)'
                })
                result['passed'] = False
        
        # Check center alignment
        center_positions = [bounds['y'] + bounds['height'] // 2 for bounds in bounds_list]
        if len(set(center_positions)) == 1:
            result['checks'].append({
                'type': 'center_alignment',
                'passed': True,
                'message': 'All elements center-aligned'
            })
        else:
            max_diff = max(center_positions) - min(center_positions)
            if max_diff <= self.tolerance:
                result['checks'].append({
                    'type': 'center_alignment',
                    'passed': True,
                    'message': f'Center alignment within tolerance ({max_diff}px)'
                })
            else:
                result['checks'].append({
                    'type': 'center_alignment',
                    'passed': False,
                    'message': f'Center alignment exceeds tolerance ({max_diff}px > {self.tolerance}px)'
                })
                result['passed'] = False
        
        return result
    
    def _check_vertical_alignment(self, bounds_list: List[Dict], elements: List[Dict], result: Dict) -> Dict:
        """Check if elements are vertically aligned."""
        # Check left alignment
        left_positions = [bounds['x'] for bounds in bounds_list]
        if len(set(left_positions)) == 1:
            result['checks'].append({
                'type': 'left_alignment',
                'passed': True,
                'message': 'All elements left-aligned'
            })
        else:
            max_diff = max(left_positions) - min(left_positions)
            if max_diff <= self.tolerance:
                result['checks'].append({
                    'type': 'left_alignment',
                    'passed': True,
                    'message': f'Left alignment within tolerance ({max_diff}px)'
                })
            else:
                result['checks'].append({
                    'type': 'left_alignment',
                    'passed': False,
                    'message': f'Left alignment exceeds tolerance ({max_diff}px > {self.tolerance}px)'
                })
                result['passed'] = False
        
        # Check center alignment
        center_positions = [bounds['x'] + bounds['width'] // 2 for bounds in bounds_list]
        if len(set(center_positions)) == 1:
            result['checks'].append({
                'type': 'center_alignment',
                'passed': True,
                'message': 'All elements center-aligned'
            })
        else:
            max_diff = max(center_positions) - min(center_positions)
            if max_diff <= self.tolerance:
                result['checks'].append({
                    'type': 'center_alignment',
                    'passed': True,
                    'message': f'Center alignment within tolerance ({max_diff}px)'
                })
            else:
                result['checks'].append({
                    'type': 'center_alignment',
                    'passed': False,
                    'message': f'Center alignment exceeds tolerance ({max_diff}px > {self.tolerance}px)'
                })
                result['passed'] = False
        
        return result
    
    def _check_grid_alignment(self, bounds_list: List[Dict], elements: List[Dict], check: Dict, result: Dict) -> Dict:
        """Check if elements are aligned in a grid."""
        expected_columns = check.get('columns', 2)
        expected_rows = check.get('rows', len(elements) // expected_columns)
        
        # Group elements by rows
        rows = []
        for i in range(0, len(bounds_list), expected_columns):
            row = bounds_list[i:i + expected_columns]
            rows.append(row)
        
        # Check each row for horizontal alignment
        for i, row in enumerate(rows):
            if len(row) > 1:
                row_result = self._check_horizontal_alignment(row, [], {'checks': []})
                for check_result in row_result['checks']:
                    check_result['row'] = i
                    result['checks'].append(check_result)
                    if not check_result['passed']:
                        result['passed'] = False
        
        # Check each column for vertical alignment
        for col in range(expected_columns):
            column_elements = [row[col] for row in rows if col < len(row)]
            if len(column_elements) > 1:
                col_result = self._check_vertical_alignment(column_elements, [], {'checks': []})
                for check_result in col_result['checks']:
                    check_result['column'] = col
                    result['checks'].append(check_result)
                    if not check_result['passed']:
                        result['passed'] = False
        
        return result
    
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