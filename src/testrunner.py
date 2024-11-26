"""
Test Runner for Vehicle Fault Analysis System.
Executes tests in specified sequence with dependency management.
Author: Chris Yeo
"""

import os
import sys
import time
import pytest
import logging
from typing import List, Set, Dict
from datetime import datetime
from config.TestConfig import test_config

class TestRunner:
    """Manages test execution with dependencies and retries."""

    def __init__(self):
        """Initialize the test runner with configuration."""
        self.log_file = 'logs/test_runner.log'
        self._clear_log_file()
        self.logger = self._setup_logger()
        self.executed_tests: Set[str] = set()
        self.failed_tests: Set[str] = set()
        self.settings = test_config.get_execution_settings()

    def _clear_log_file(self):
        """Clear the log file and create a new one with a header."""
        os.makedirs('logs', exist_ok=True)
        with open(self.log_file, 'w') as f:
            f.write(f"=== Test Runner Log Started at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===\n")
            f.write("=" * 80 + "\n")

    def _setup_logger(self) -> logging.Logger:
        """Set up logging for the test runner."""
        logger = logging.getLogger('TestRunner')
        logger.setLevel(logging.INFO)
        
        # Remove any existing handlers
        logger.handlers = []
        
        # File handler
        fh = logging.FileHandler(self.log_file)
        fh.setLevel(logging.INFO)
        
        # Console handler
        ch = logging.StreamHandler()
        ch.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter('[%(asctime)s] %(levelname)s: %(message)s')
        fh.setFormatter(formatter)
        ch.setFormatter(formatter)
        
        logger.addHandler(fh)
        logger.addHandler(ch)
        
        return logger

    def _can_run_test(self, test_name: str) -> bool:
        """Check if a test's dependencies are satisfied."""
        deps = test_config.get_test_dependencies(test_name)
        return all(dep in self.executed_tests - self.failed_tests for dep in deps)

    def _run_single_test(self, test_name: str) -> bool:
        """Run a single test with retries."""
        test_file = test_config.get_test_file(test_name)
        if not test_file:
            self.logger.error(f"Test file not found for {test_name}")
            return False

        timeout = test_config.get_test_timeout(test_name)
        retry_count = self.settings['retry_count']
        retry_delay = self.settings['retry_delay']

        for attempt in range(retry_count + 1):
            if attempt > 0:
                self.logger.info(f"Retrying {test_name} (attempt {attempt + 1}/{retry_count + 1})")
                time.sleep(retry_delay)

            try:
                self.logger.info(f"Running {test_name} (timeout: {timeout}s)")
                start_time = time.time()
                
                # Run pytest with timeout
                result = pytest.main(['-v', test_file])
                
                execution_time = time.time() - start_time
                
                if result == pytest.ExitCode.OK:
                    self.logger.info(f"{test_name} passed in {execution_time:.2f}s")
                    return True
                else:
                    self.logger.error(f"{test_name} failed (attempt {attempt + 1}/{retry_count + 1})")
                    
                if execution_time >= timeout:
                    self.logger.error(f"{test_name} timed out after {timeout}s")
                    break
                    
            except Exception as e:
                self.logger.error(f"Error running {test_name}: {str(e)}")
                
        return False

    def run_tests(self) -> bool:
        """Run all tests in sequence with dependency management."""
        self.logger.info("Starting test execution")
        start_time = time.time()

        # Validate dependencies
        if not test_config.validate_test_dependencies():
            self.logger.error("Invalid test dependencies detected (circular dependencies)")
            return False

        # Get test sequence
        sequence = test_config.get_test_sequence()
        if not sequence:
            self.logger.error("No tests specified in sequence")
            return False

        self.logger.info(f"Test sequence: {' -> '.join(sequence)}")

        # Run tests in sequence
        for test_name in sequence:
            if not self._can_run_test(test_name):
                self.logger.error(f"Dependencies not met for {test_name}")
                if self.settings['stop_on_failure']:
                    return False
                continue

            success = self._run_single_test(test_name)
            self.executed_tests.add(test_name)
            
            if not success:
                self.failed_tests.add(test_name)
                if self.settings['stop_on_failure']:
                    self.logger.error("Stopping due to test failure")
                    return False

        # Report results
        execution_time = time.time() - start_time
        success_count = len(self.executed_tests - self.failed_tests)
        fail_count = len(self.failed_tests)
        
        self.logger.info(f"\nTest Execution Summary:")
        self.logger.info(f"Total time: {execution_time:.2f}s")
        self.logger.info(f"Tests passed: {success_count}")
        self.logger.info(f"Tests failed: {fail_count}")
        
        if self.failed_tests:
            self.logger.info(f"Failed tests: {', '.join(self.failed_tests)}")

        return len(self.failed_tests) == 0

def main():
    """Main entry point for test runner."""
    runner = TestRunner()
    success = runner.run_tests()
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
