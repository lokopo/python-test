"""
Visual verification tools for GUI testing.
"""

import base64
import io
import os
from typing import Any, Dict, List, Optional, Tuple, Union
from PIL import Image, ImageChops, ImageStat
import numpy as np
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .core import BaseVerifier, VerificationResult, VerificationStatus


class VisualVerifier(BaseVerifier):
    """Main visual verification class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.screenshot_comparator = ScreenshotComparator(config)
        self.element_detector = ElementDetector(config)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Run visual verification checks."""
        checks = kwargs.get('checks', ['screenshot', 'elements'])
        results = []
        
        for check in checks:
            if check == 'screenshot':
                result = self.screenshot_comparator.verify(target, **kwargs)
                results.append(result)
            elif check == 'elements':
                result = self.element_detector.verify(target, **kwargs)
                results.append(result)
        
        # Determine overall status
        if all(r.status == VerificationStatus.PASS for r in results):
            status = VerificationStatus.PASS
            message = "All visual checks passed"
        elif any(r.status == VerificationStatus.FAIL for r in results):
            status = VerificationStatus.FAIL
            message = "Some visual checks failed"
        else:
            status = VerificationStatus.WARNING
            message = "Some visual checks have warnings"
        
        return VerificationResult(
            check_name="VisualVerifier",
            status=status,
            message=message,
            details={"individual_results": [r.__dict__ for r in results]}
        )


class ScreenshotComparator(BaseVerifier):
    """Compare screenshots for visual regression testing."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.threshold = config.get('threshold', 0.95)  # Similarity threshold
        self.tolerance = config.get('tolerance', 5)  # Pixel difference tolerance
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Compare current screenshot with reference image."""
        reference_path = kwargs.get('reference_path')
        current_screenshot = kwargs.get('screenshot')
        
        if not reference_path and not current_screenshot:
            return VerificationResult(
                check_name="ScreenshotComparator",
                status=VerificationStatus.FAIL,
                message="No reference image or current screenshot provided"
            )
        
        try:
            if current_screenshot:
                current_img = self._process_screenshot(current_screenshot)
            else:
                # Take screenshot from webdriver
                current_img = self._take_screenshot(target)
            
            if reference_path:
                reference_img = Image.open(reference_path)
            else:
                return VerificationResult(
                    check_name="ScreenshotComparator",
                    status=VerificationStatus.FAIL,
                    message="No reference image provided"
                )
            
            # Compare images
            similarity, differences = self._compare_images(reference_img, current_img)
            
            if similarity >= self.threshold:
                status = VerificationStatus.PASS
                message = f"Screenshot matches reference (similarity: {similarity:.2f})"
            else:
                status = VerificationStatus.FAIL
                message = f"Screenshot differs from reference (similarity: {similarity:.2f})"
            
            return VerificationResult(
                check_name="ScreenshotComparator",
                status=status,
                message=message,
                details={
                    "similarity": similarity,
                    "differences": differences,
                    "threshold": self.threshold
                }
            )
            
        except Exception as e:
            return VerificationResult(
                check_name="ScreenshotComparator",
                status=VerificationStatus.FAIL,
                message=f"Screenshot comparison failed: {str(e)}"
            )
    
    def _process_screenshot(self, screenshot: Union[str, bytes]) -> Image.Image:
        """Process screenshot data into PIL Image."""
        if isinstance(screenshot, str):
            if screenshot.startswith('data:image'):
                # Base64 encoded image
                header, data = screenshot.split(',', 1)
                image_data = base64.b64decode(data)
                return Image.open(io.BytesIO(image_data))
            else:
                # File path
                return Image.open(screenshot)
        elif isinstance(screenshot, bytes):
            return Image.open(io.BytesIO(screenshot))
        else:
            raise ValueError("Invalid screenshot format")
    
    def _take_screenshot(self, driver: webdriver.Chrome) -> Image.Image:
        """Take screenshot using Selenium WebDriver."""
        screenshot_data = driver.get_screenshot_as_png()
        return Image.open(io.BytesIO(screenshot_data))
    
    def _compare_images(self, img1: Image.Image, img2: Image.Image) -> Tuple[float, Dict[str, Any]]:
        """Compare two images and return similarity score and differences."""
        # Resize images to same size if needed
        if img1.size != img2.size:
            img2 = img2.resize(img1.size, Image.Resampling.LANCZOS)
        
        # Convert to RGB if needed
        if img1.mode != 'RGB':
            img1 = img1.convert('RGB')
        if img2.mode != 'RGB':
            img2 = img2.convert('RGB')
        
        # Calculate difference
        diff = ImageChops.difference(img1, img2)
        
        # Calculate similarity using structural similarity
        img1_array = np.array(img1)
        img2_array = np.array(img2)
        
        # Calculate mean squared error
        mse = np.mean((img1_array - img2_array) ** 2)
        
        # Calculate similarity (higher is more similar)
        max_pixel_value = 255
        similarity = 1 - (mse / (max_pixel_value ** 2))
        
        # Count different pixels
        diff_array = np.array(diff)
        different_pixels = np.sum(diff_array > self.tolerance)
        total_pixels = diff_array.size
        
        differences = {
            "mse": float(mse),
            "different_pixels": int(different_pixels),
            "total_pixels": int(total_pixels),
            "difference_percentage": float(different_pixels / total_pixels * 100)
        }
        
        return similarity, differences


class ElementDetector(BaseVerifier):
    """Detect and verify presence of UI elements."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.timeout = config.get('timeout', 10)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Verify presence and properties of UI elements."""
        elements_to_check = kwargs.get('elements', [])
        driver = target
        
        if not elements_to_check:
            return VerificationResult(
                check_name="ElementDetector",
                status=VerificationStatus.WARNING,
                message="No elements specified for detection"
            )
        
        results = []
        all_found = True
        
        for element_spec in elements_to_check:
            try:
                element_result = self._check_element(driver, element_spec)
                results.append(element_result)
                if element_result['status'] != 'found':
                    all_found = False
            except Exception as e:
                results.append({
                    'selector': element_spec.get('selector', 'unknown'),
                    'status': 'error',
                    'message': str(e)
                })
                all_found = False
        
        status = VerificationStatus.PASS if all_found else VerificationStatus.FAIL
        message = f"Element detection: {sum(1 for r in results if r['status'] == 'found')}/{len(results)} elements found"
        
        return VerificationResult(
            check_name="ElementDetector",
            status=status,
            message=message,
            details={"element_results": results}
        )
    
    def _check_element(self, driver: webdriver.Chrome, element_spec: Dict[str, Any]) -> Dict[str, Any]:
        """Check a single element."""
        selector = element_spec['selector']
        by_type = element_spec.get('by', By.CSS_SELECTOR)
        expected_text = element_spec.get('text')
        expected_visible = element_spec.get('visible', True)
        
        try:
            element = driver.find_element(by_type, selector)
            
            result = {
                'selector': selector,
                'status': 'found',
                'visible': element.is_displayed(),
                'enabled': element.is_enabled(),
                'text': element.text,
                'tag_name': element.tag_name
            }
            
            # Check visibility expectation
            if expected_visible is not None and element.is_displayed() != expected_visible:
                result['status'] = 'visibility_mismatch'
                result['message'] = f"Expected visible={expected_visible}, got visible={element.is_displayed()}"
            
            # Check text expectation
            if expected_text and element.text != expected_text:
                result['status'] = 'text_mismatch'
                result['message'] = f"Expected text='{expected_text}', got text='{element.text}'"
            
            return result
            
        except Exception as e:
            return {
                'selector': selector,
                'status': 'not_found',
                'message': str(e)
            }
    
    def find_elements_by_text(self, driver: webdriver.Chrome, text: str, exact: bool = False) -> List[WebElement]:
        """Find elements containing specific text."""
        if exact:
            xpath = f"//*[text()='{text}']"
        else:
            xpath = f"//*[contains(text(), '{text}')]"
        
        return driver.find_elements(By.XPATH, xpath)
    
    def find_elements_by_attribute(self, driver: webdriver.Chrome, attribute: str, value: str) -> List[WebElement]:
        """Find elements with specific attribute value."""
        xpath = f"//*[@{attribute}='{value}']"
        return driver.find_elements(By.XPATH, xpath)
    
    def get_element_bounds(self, element: WebElement) -> Dict[str, int]:
        """Get element position and size."""
        location = element.location
        size = element.size
        return {
            'x': location['x'],
            'y': location['y'],
            'width': size['width'],
            'height': size['height']
        }