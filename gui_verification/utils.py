"""
Utility classes and functions for GUI verification.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager


class BrowserManager:
    """Manage browser instances for GUI verification."""
    
    def __init__(self, headless: bool = True, window_size: Tuple[int, int] = (1920, 1080)):
        self.headless = headless
        self.window_size = window_size
        self.driver = None
    
    def create_driver(self) -> webdriver.Chrome:
        """Create a new Chrome driver instance."""
        options = Options()
        
        if self.headless:
            options.add_argument('--headless')
        
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--disable-gpu')
        options.add_argument('--window-size={},{}'.format(*self.window_size))
        options.add_argument('--disable-extensions')
        options.add_argument('--disable-plugins')
        options.add_argument('--disable-images')  # Speed up loading
        
        # Disable logging to reduce noise
        options.add_argument('--log-level=3')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        
        try:
            service = Service(ChromeDriverManager().install())
            self.driver = webdriver.Chrome(service=service, options=options)
            self.driver.set_window_size(*self.window_size)
            return self.driver
        except Exception as e:
            raise Exception(f"Failed to create Chrome driver: {str(e)}")
    
    def get_driver(self) -> webdriver.Chrome:
        """Get existing driver or create new one."""
        if self.driver is None:
            return self.create_driver()
        return self.driver
    
    def close_driver(self):
        """Close the current driver."""
        if self.driver:
            self.driver.quit()
            self.driver = None
    
    def __enter__(self):
        """Context manager entry."""
        return self.get_driver()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_driver()


class ElementFinder:
    """Enhanced element finding utilities."""
    
    def __init__(self, driver: webdriver.Chrome):
        self.driver = driver
    
    def find_element_safe(self, by: By, value: str, timeout: int = 10) -> Optional[WebElement]:
        """Safely find an element with timeout."""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.presence_of_element_located((by, value)))
            return element
        except:
            return None
    
    def find_elements_safe(self, by: By, value: str, timeout: int = 10) -> List[WebElement]:
        """Safely find multiple elements with timeout."""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((by, value)))
            return self.driver.find_elements(by, value)
        except:
            return []
    
    def find_clickable_element(self, by: By, value: str, timeout: int = 10) -> Optional[WebElement]:
        """Find an element that is clickable."""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.element_to_be_clickable((by, value)))
            return element
        except:
            return None
    
    def find_visible_element(self, by: By, value: str, timeout: int = 10) -> Optional[WebElement]:
        """Find an element that is visible."""
        try:
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            
            wait = WebDriverWait(self.driver, timeout)
            element = wait.until(EC.visibility_of_element_located((by, value)))
            return element
        except:
            return None
    
    def find_element_by_text(self, text: str, exact: bool = False, tag: str = None) -> List[WebElement]:
        """Find elements containing specific text."""
        if exact:
            if tag:
                xpath = f"//{tag}[text()='{text}']"
            else:
                xpath = f"//*[text()='{text}']"
        else:
            if tag:
                xpath = f"//{tag}[contains(text(), '{text}')]"
            else:
                xpath = f"//*[contains(text(), '{text}')]"
        
        return self.driver.find_elements(By.XPATH, xpath)
    
    def find_element_by_attribute(self, attribute: str, value: str, tag: str = None) -> List[WebElement]:
        """Find elements with specific attribute value."""
        if tag:
            xpath = f"//{tag}[@{attribute}='{value}']"
        else:
            xpath = f"//*[@{attribute}='{value}']"
        
        return self.driver.find_elements(By.XPATH, xpath)
    
    def find_interactive_elements(self) -> List[WebElement]:
        """Find all interactive elements on the page."""
        interactive_selectors = [
            'button', 'input', 'select', 'textarea', 'a[href]',
            '[role="button"]', '[role="link"]', '[role="menuitem"]',
            '[role="tab"]', '[role="option"]', '[onclick]',
            '[tabindex]:not([tabindex="-1"])'
        ]
        
        elements = []
        for selector in interactive_selectors:
            try:
                found_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                elements.extend(found_elements)
            except:
                continue
        
        return elements
    
    def get_element_info(self, element: WebElement) -> Dict[str, Any]:
        """Get comprehensive information about an element."""
        try:
            return {
                'tag_name': element.tag_name,
                'text': element.text,
                'is_displayed': element.is_displayed(),
                'is_enabled': element.is_enabled(),
                'is_selected': element.is_selected(),
                'location': element.location,
                'size': element.size,
                'id': element.get_attribute('id'),
                'class': element.get_attribute('class'),
                'name': element.get_attribute('name'),
                'type': element.get_attribute('type'),
                'value': element.get_attribute('value'),
                'href': element.get_attribute('href'),
                'src': element.get_attribute('src'),
                'alt': element.get_attribute('alt'),
                'title': element.get_attribute('title'),
                'role': element.get_attribute('role'),
                'aria_label': element.get_attribute('aria-label'),
                'aria_labelledby': element.get_attribute('aria-labelledby'),
                'aria_describedby': element.get_attribute('aria-describedby'),
                'tabindex': element.get_attribute('tabindex'),
                'style': element.get_attribute('style')
            }
        except Exception as e:
            return {'error': str(e)}


class ColorUtils:
    """Utilities for color manipulation and analysis."""
    
    @staticmethod
    def hex_to_rgb(hex_color: str) -> Optional[Tuple[int, int, int]]:
        """Convert hex color to RGB tuple."""
        hex_color = hex_color.lstrip('#')
        if len(hex_color) == 6:
            try:
                return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
            except ValueError:
                return None
        return None
    
    @staticmethod
    def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
        """Convert RGB tuple to hex color."""
        return '#{:02x}{:02x}{:02x}'.format(*rgb)
    
    @staticmethod
    def calculate_luminance(rgb: Tuple[int, int, int]) -> float:
        """Calculate relative luminance of an RGB color."""
        r, g, b = [c / 255.0 for c in rgb]
        
        # Apply gamma correction
        r = r / 12.92 if r <= 0.03928 else ((r + 0.055) / 1.055) ** 2.4
        g = g / 12.92 if g <= 0.03928 else ((g + 0.055) / 1.055) ** 2.4
        b = b / 12.92 if b <= 0.03928 else ((b + 0.055) / 1.055) ** 2.4
        
        return 0.2126 * r + 0.7152 * g + 0.0722 * b
    
    @staticmethod
    def calculate_contrast_ratio(color1: Tuple[int, int, int], color2: Tuple[int, int, int]) -> float:
        """Calculate contrast ratio between two RGB colors."""
        lum1 = ColorUtils.calculate_luminance(color1)
        lum2 = ColorUtils.calculate_luminance(color2)
        
        lighter = max(lum1, lum2)
        darker = min(lum1, lum2)
        
        return (lighter + 0.05) / (darker + 0.05)
    
    @staticmethod
    def is_color_accessible(foreground: Tuple[int, int, int], 
                          background: Tuple[int, int, int], 
                          is_large_text: bool = False) -> Tuple[bool, float]:
        """Check if color combination meets accessibility standards."""
        contrast_ratio = ColorUtils.calculate_contrast_ratio(foreground, background)
        required_ratio = 3.0 if is_large_text else 4.5
        return contrast_ratio >= required_ratio, contrast_ratio
    
    @staticmethod
    def parse_css_color(color_str: str) -> Optional[Tuple[int, int, int]]:
        """Parse CSS color string to RGB tuple."""
        import re
        
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


class WaitUtils:
    """Utilities for waiting and timing."""
    
    @staticmethod
    def wait_for_element(driver: webdriver.Chrome, by: By, value: str, timeout: int = 10) -> WebElement:
        """Wait for element to be present."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.presence_of_element_located((by, value)))
    
    @staticmethod
    def wait_for_clickable(driver: webdriver.Chrome, by: By, value: str, timeout: int = 10) -> WebElement:
        """Wait for element to be clickable."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.element_to_be_clickable((by, value)))
    
    @staticmethod
    def wait_for_visible(driver: webdriver.Chrome, by: By, value: str, timeout: int = 10) -> WebElement:
        """Wait for element to be visible."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.visibility_of_element_located((by, value)))
    
    @staticmethod
    def wait_for_text_in_element(driver: webdriver.Chrome, by: By, value: str, 
                                text: str, timeout: int = 10) -> WebElement:
        """Wait for element to contain specific text."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.text_to_be_present_in_element((by, value), text))
    
    @staticmethod
    def wait_for_url_change(driver: webdriver.Chrome, current_url: str, timeout: int = 10) -> bool:
        """Wait for URL to change from current URL."""
        from selenium.webdriver.support.ui import WebDriverWait
        from selenium.webdriver.support import expected_conditions as EC
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(EC.url_changes(current_url))
    
    @staticmethod
    def wait_for_page_load(driver: webdriver.Chrome, timeout: int = 10) -> bool:
        """Wait for page to fully load."""
        from selenium.webdriver.support.ui import WebDriverWait
        
        def page_loaded(driver):
            return driver.execute_script("return document.readyState") == "complete"
        
        wait = WebDriverWait(driver, timeout)
        return wait.until(page_loaded)
    
    @staticmethod
    def sleep_with_progress(seconds: float, step: float = 0.1):
        """Sleep with progress indication."""
        steps = int(seconds / step)
        for i in range(steps):
            time.sleep(step)
            progress = (i + 1) / steps * 100
            print(f"\rWaiting... {progress:.1f}%", end="", flush=True)
        print()  # New line after completion