"""
Performance verification tools for GUI testing.
"""

import time
from typing import Any, Dict, List, Optional
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement

from .core import BaseVerifier, VerificationResult, VerificationStatus


class PerformanceVerifier(BaseVerifier):
    """Main performance verification class."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.load_time_checker = LoadTimeChecker(config)
        self.animation_checker = AnimationChecker(config)
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Run performance verification checks."""
        checks = kwargs.get('checks', ['load_time', 'animations'])
        results = []
        
        for check in checks:
            if check == 'load_time':
                result = self.load_time_checker.verify(target, **kwargs)
                results.append(result)
            elif check == 'animations':
                result = self.animation_checker.verify(target, **kwargs)
                results.append(result)
        
        # Determine overall status
        if all(r.status == VerificationStatus.PASS for r in results):
            status = VerificationStatus.PASS
            message = "All performance checks passed"
        elif any(r.status == VerificationStatus.FAIL for r in results):
            status = VerificationStatus.FAIL
            message = "Some performance checks failed"
        else:
            status = VerificationStatus.WARNING
            message = "Some performance checks have warnings"
        
        return VerificationResult(
            check_name="PerformanceVerifier",
            status=status,
            message=message,
            details={"individual_results": [r.__dict__ for r in results]}
        )


class LoadTimeChecker(BaseVerifier):
    """Check page load times and performance metrics."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_load_time = config.get('max_load_time', 3000)  # 3 seconds in milliseconds
        self.max_dom_ready_time = config.get('max_dom_ready_time', 2000)  # 2 seconds
        self.max_first_paint_time = config.get('max_first_paint_time', 1000)  # 1 second
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Check page load performance."""
        driver = target
        url = kwargs.get('url', driver.current_url)
        
        results = []
        all_passed = True
        
        # Test initial page load
        load_result = self._test_page_load(driver, url)
        results.append(load_result)
        if not load_result['passed']:
            all_passed = False
        
        # Test navigation performance
        if kwargs.get('test_navigation', False):
            nav_result = self._test_navigation_performance(driver, kwargs.get('navigation_urls', []))
            results.append(nav_result)
            if not nav_result['passed']:
                all_passed = False
        
        # Test resource loading
        if kwargs.get('test_resources', False):
            resource_result = self._test_resource_loading(driver)
            results.append(resource_result)
            if not resource_result['passed']:
                all_passed = False
        
        status = VerificationStatus.PASS if all_passed else VerificationStatus.FAIL
        message = f"Load time tests: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="LoadTimeChecker",
            status=status,
            message=message,
            details={"load_time_results": results}
        )
    
    def _test_page_load(self, driver: webdriver.Chrome, url: str) -> Dict[str, Any]:
        """Test page load performance."""
        result = {
            'test': 'page_load',
            'url': url,
            'passed': True,
            'checks': []
        }
        
        try:
            # Clear browser cache and navigate
            driver.delete_all_cookies()
            start_time = time.time()
            
            driver.get(url)
            
            # Wait for page to load completely
            driver.execute_script("return document.readyState") == "complete"
            
            load_time = (time.time() - start_time) * 1000  # Convert to milliseconds
            
            # Check total load time
            if load_time <= self.max_load_time:
                result['checks'].append({
                    'type': 'total_load_time',
                    'passed': True,
                    'message': f'Page loaded in {load_time:.0f}ms (under {self.max_load_time}ms limit)',
                    'load_time': load_time,
                    'limit': self.max_load_time
                })
            else:
                result['checks'].append({
                    'type': 'total_load_time',
                    'passed': False,
                    'message': f'Page load time {load_time:.0f}ms exceeds limit of {self.max_load_time}ms',
                    'load_time': load_time,
                    'limit': self.max_load_time
                })
                result['passed'] = False
            
            # Get performance metrics if available
            try:
                performance_metrics = driver.execute_script("""
                    var perfData = window.performance.timing;
                    return {
                        domContentLoaded: perfData.domContentLoadedEventEnd - perfData.navigationStart,
                        loadComplete: perfData.loadEventEnd - perfData.navigationStart,
                        firstPaint: 0
                    };
                """)
                
                # Check DOM ready time
                dom_ready_time = performance_metrics.get('domContentLoaded', 0)
                if dom_ready_time <= self.max_dom_ready_time:
                    result['checks'].append({
                        'type': 'dom_ready_time',
                        'passed': True,
                        'message': f'DOM ready in {dom_ready_time}ms (under {self.max_dom_ready_time}ms limit)',
                        'dom_ready_time': dom_ready_time,
                        'limit': self.max_dom_ready_time
                    })
                else:
                    result['checks'].append({
                        'type': 'dom_ready_time',
                        'passed': False,
                        'message': f'DOM ready time {dom_ready_time}ms exceeds limit of {self.max_dom_ready_time}ms',
                        'dom_ready_time': dom_ready_time,
                        'limit': self.max_dom_ready_time
                    })
                    result['passed'] = False
                
                # Check total load time from performance API
                load_complete_time = performance_metrics.get('loadComplete', 0)
                if load_complete_time > 0:
                    result['checks'].append({
                        'type': 'performance_api_load',
                        'passed': True,
                        'message': f'Performance API load time: {load_complete_time}ms',
                        'load_complete_time': load_complete_time
                    })
            
            except Exception as e:
                result['checks'].append({
                    'type': 'performance_metrics',
                    'passed': False,
                    'message': f'Could not get performance metrics: {str(e)}'
                })
        
        except Exception as e:
            result['checks'].append({
                'type': 'page_load_test',
                'passed': False,
                'message': f'Page load test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _test_navigation_performance(self, driver: webdriver.Chrome, urls: List[str]) -> Dict[str, Any]:
        """Test navigation performance between pages."""
        result = {
            'test': 'navigation_performance',
            'passed': True,
            'checks': []
        }
        
        if not urls:
            result['checks'].append({
                'type': 'navigation_test',
                'passed': True,
                'message': 'No navigation URLs provided'
            })
            return result
        
        total_nav_time = 0
        nav_times = []
        
        for url in urls:
            try:
                start_time = time.time()
                driver.get(url)
                nav_time = (time.time() - start_time) * 1000
                nav_times.append(nav_time)
                total_nav_time += nav_time
                
                result['checks'].append({
                    'type': 'navigation_time',
                    'passed': True,
                    'message': f'Navigation to {url}: {nav_time:.0f}ms',
                    'url': url,
                    'nav_time': nav_time
                })
            
            except Exception as e:
                result['checks'].append({
                    'type': 'navigation_time',
                    'passed': False,
                    'message': f'Navigation to {url} failed: {str(e)}',
                    'url': url
                })
                result['passed'] = False
        
        if nav_times:
            avg_nav_time = total_nav_time / len(nav_times)
            result['checks'].append({
                'type': 'average_navigation',
                'passed': True,
                'message': f'Average navigation time: {avg_nav_time:.0f}ms',
                'average_nav_time': avg_nav_time,
                'total_navigations': len(nav_times)
            })
        
        return result
    
    def _test_resource_loading(self, driver: webdriver.Chrome) -> Dict[str, Any]:
        """Test resource loading performance."""
        result = {
            'test': 'resource_loading',
            'passed': True,
            'checks': []
        }
        
        try:
            # Get resource loading information
            resources = driver.execute_script("""
                var resources = window.performance.getEntriesByType('resource');
                var resourceData = [];
                for (var i = 0; i < resources.length; i++) {
                    var resource = resources[i];
                    resourceData.push({
                        name: resource.name,
                        duration: resource.duration,
                        size: resource.transferSize || 0,
                        type: resource.initiatorType
                    });
                }
                return resourceData;
            """)
            
            if not resources:
                result['checks'].append({
                    'type': 'resource_loading',
                    'passed': True,
                    'message': 'No resource loading data available'
                })
                return result
            
            # Analyze resource loading times
            slow_resources = [r for r in resources if r['duration'] > 1000]  # > 1 second
            large_resources = [r for r in resources if r['size'] > 1000000]  # > 1MB
            
            if slow_resources:
                result['checks'].append({
                    'type': 'slow_resources',
                    'passed': False,
                    'message': f'Found {len(slow_resources)} slow-loading resources (>1s)',
                    'slow_resources': slow_resources[:5]  # Show first 5
                })
                result['passed'] = False
            else:
                result['checks'].append({
                    'type': 'slow_resources',
                    'passed': True,
                    'message': 'No slow-loading resources found'
                })
            
            if large_resources:
                result['checks'].append({
                    'type': 'large_resources',
                    'passed': False,
                    'message': f'Found {len(large_resources)} large resources (>1MB)',
                    'large_resources': large_resources[:5]  # Show first 5
                })
                result['passed'] = False
            else:
                result['checks'].append({
                    'type': 'large_resources',
                    'passed': True,
                    'message': 'No large resources found'
                })
            
            # Check total resource count
            total_resources = len(resources)
            if total_resources > 100:
                result['checks'].append({
                    'type': 'resource_count',
                    'passed': False,
                    'message': f'High number of resources loaded: {total_resources}'
                })
                result['passed'] = False
            else:
                result['checks'].append({
                    'type': 'resource_count',
                    'passed': True,
                    'message': f'Reasonable number of resources: {total_resources}'
                })
        
        except Exception as e:
            result['checks'].append({
                'type': 'resource_loading',
                'passed': False,
                'message': f'Resource loading test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result


class AnimationChecker(BaseVerifier):
    """Check animation performance and smoothness."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_animation_duration = config.get('max_animation_duration', 500)  # 500ms
        self.min_fps = config.get('min_fps', 30)  # Minimum FPS for smooth animation
    
    def verify(self, target: Any, **kwargs) -> VerificationResult:
        """Check animation performance."""
        driver = target
        animation_tests = kwargs.get('animation_tests', [])
        
        if not animation_tests:
            # Find elements with animations
            animation_tests = self._find_animation_elements(driver)
        
        results = []
        all_passed = True
        
        for test in animation_tests:
            try:
                result = self._test_animation(driver, test)
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
        message = f"Animation tests: {sum(1 for r in results if r['passed'])}/{len(results)} passed"
        
        return VerificationResult(
            check_name="AnimationChecker",
            status=status,
            message=message,
            details={"animation_results": results}
        )
    
    def _find_animation_elements(self, driver: webdriver.Chrome) -> List[Dict[str, Any]]:
        """Find elements with CSS animations or transitions."""
        animation_selectors = [
            '[style*="animation"]', '[style*="transition"]',
            '.animated', '.fade', '.slide', '.bounce',
            '[class*="animate"]', '[class*="transition"]'
        ]
        
        tests = []
        for selector in animation_selectors:
            try:
                elements = driver.find_elements(By.CSS_SELECTOR, selector)
                for i, element in enumerate(elements):
                    if element.is_displayed():
                        tests.append({
                            'name': f'animation_{selector}_{i}',
                            'selector': f"{selector}:nth-of-type({i+1})",
                            'by': By.CSS_SELECTOR,
                            'type': 'css_animation'
                        })
            except:
                continue
        
        return tests
    
    def _test_animation(self, driver: webdriver.Chrome, test: Dict[str, Any]) -> Dict[str, Any]:
        """Test a single animation."""
        test_name = test['name']
        selector = test['selector']
        by_type = test.get('by', By.CSS_SELECTOR)
        animation_type = test.get('type', 'css_animation')
        
        result = {
            'test': test_name,
            'passed': True,
            'checks': []
        }
        
        try:
            element = driver.find_element(by_type, selector)
            
            if animation_type == 'css_animation':
                result = self._test_css_animation(driver, element, test, result)
            elif animation_type == 'transition':
                result = self._test_css_transition(driver, element, test, result)
        
        except Exception as e:
            result['checks'].append({
                'type': 'animation_test',
                'passed': False,
                'message': f'Animation test failed: {str(e)}'
            })
            result['passed'] = False
        
        return result
    
    def _test_css_animation(self, driver: webdriver.Chrome, element: WebElement, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test CSS animation performance."""
        # Get computed animation properties
        animation_props = driver.execute_script("""
            var element = arguments[0];
            var computed = window.getComputedStyle(element);
            return {
                animationName: computed.animationName,
                animationDuration: computed.animationDuration,
                animationTimingFunction: computed.animationTimingFunction,
                animationIterationCount: computed.animationIterationCount
            };
        """, element)
        
        animation_name = animation_props['animationName']
        animation_duration = float(animation_props['animationDuration'].replace('s', '')) * 1000  # Convert to ms
        
        if animation_name == 'none':
            result['checks'].append({
                'type': 'animation_detection',
                'passed': True,
                'message': 'No animation detected on element'
            })
            return result
        
        # Check animation duration
        if animation_duration <= self.max_animation_duration:
            result['checks'].append({
                'type': 'animation_duration',
                'passed': True,
                'message': f'Animation duration {animation_duration}ms is acceptable (under {self.max_animation_duration}ms)',
                'duration': animation_duration,
                'limit': self.max_animation_duration
            })
        else:
            result['checks'].append({
                'type': 'animation_duration',
                'passed': False,
                'message': f'Animation duration {animation_duration}ms is too long (over {self.max_animation_duration}ms)',
                'duration': animation_duration,
                'limit': self.max_animation_duration
            })
            result['passed'] = False
        
        # Check animation timing function
        timing_function = animation_props['animationTimingFunction']
        if timing_function in ['ease', 'ease-in', 'ease-out', 'ease-in-out', 'linear']:
            result['checks'].append({
                'type': 'animation_timing',
                'passed': True,
                'message': f'Animation uses standard timing function: {timing_function}'
            })
        else:
            result['checks'].append({
                'type': 'animation_timing',
                'passed': False,
                'message': f'Animation uses non-standard timing function: {timing_function}'
            })
            result['passed'] = False
        
        return result
    
    def _test_css_transition(self, driver: webdriver.Chrome, element: WebElement, test: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Test CSS transition performance."""
        # Get computed transition properties
        transition_props = driver.execute_script("""
            var element = arguments[0];
            var computed = window.getComputedStyle(element);
            return {
                transitionProperty: computed.transitionProperty,
                transitionDuration: computed.transitionDuration,
                transitionTimingFunction: computed.transitionTimingFunction
            };
        """, element)
        
        transition_duration = float(transition_props['transitionDuration'].replace('s', '')) * 1000  # Convert to ms
        
        if transition_props['transitionProperty'] == 'none':
            result['checks'].append({
                'type': 'transition_detection',
                'passed': True,
                'message': 'No transition detected on element'
            })
            return result
        
        # Check transition duration
        if transition_duration <= self.max_animation_duration:
            result['checks'].append({
                'type': 'transition_duration',
                'passed': True,
                'message': f'Transition duration {transition_duration}ms is acceptable (under {self.max_animation_duration}ms)',
                'duration': transition_duration,
                'limit': self.max_animation_duration
            })
        else:
            result['checks'].append({
                'type': 'transition_duration',
                'passed': False,
                'message': f'Transition duration {transition_duration}ms is too long (over {self.max_animation_duration}ms)',
                'duration': transition_duration,
                'limit': self.max_animation_duration
            })
            result['passed'] = False
        
        return result