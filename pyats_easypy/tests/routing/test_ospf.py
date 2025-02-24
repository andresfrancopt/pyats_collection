#!/usr/bin/env python

import logging
import os
from pyats import aetest
from pyats.log.utils import banner
from genie.testbed import load

log = logging.getLogger(__name__)

# Update the testbed path to use absolute path from project root
TESTBED_PATH = os.path.join(os.path.dirname(__file__), 
                            '..', '..', 'testbeds', 'testbed.yaml')

# Rest of your test classes from script.py...
class common_setup(aetest.CommonSetup):
    """Common Setup Section"""

    @aetest.subsection
    def connect_to_devices(self, testbed):
        """Connect to all devices from the testbed"""
        try:
            testbed.connect(log_stdout=True)
            log.info("Successfully connected to all devices")
        except Exception as e:
            log.error(f"Failed to connect to device: {str(e)}")
            self.failed(f"Failed to connect to device: {str(e)}")

    @aetest.subsection
    def loop_mark(self, testbed):
        """Mark testcases to run per device"""
        aetest.loop.mark(OSPF_Test, device_name=list(testbed.devices.keys()))

class OSPF_Test(aetest.Testcase):
    """OSPF Routing Test Suite
    
    This test suite validates OSPF routing:
    - OSPF neighbor relationships
    - OSPF route verification
    - Expected network reachability"""

    def _execute_with_retry(self, device, command, max_retries=3):
        """Execute command with retry logic on device failure"""
        for attempt in range(max_retries):
            try:
                return device.execute(command)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                log.warning(f"Retry {attempt + 1} after error: {str(e)}")

    @aetest.test
    def verify_ospf_neighbors(self, testbed, device_name):
        """🌐 Validates OSPF neighbor relationships"""
        device = testbed.devices[device_name]
        try:
            log.info(f"Checking OSPF neighbors on {device_name}")
            result = self._execute_with_retry(device, 'show ip ospf neighbor')
            
            if 'FULL' not in result:
                self.failed(f"No FULL OSPF neighbors found on {device_name}")
            else:
                log.info(f"OSPF neighbors verified on {device_name}")
                
        except Exception as e:
            self.failed(f"Error checking OSPF on {device_name}: {str(e)}")

    @aetest.test
    def verify_ospf_routes(self, testbed, device_name):
        """🌐 Validates OSPF routes are properly learned"""
        device = testbed.devices[device_name]
        try:
            log.info(f"Checking OSPF routes on {device_name}")
            result = self._execute_with_retry(device, 'show ip route ospf')
            
            expected_networks = {
                'R1': ['172.16.2.0'],  # R2's subnet
                'R2': ['172.16.1.0']   # R1's subnet
            }
            
            # Check for device-specific expected networks
            if device_name in expected_networks:
                for network in expected_networks[device_name]:
                    if network not in result:
                        self.failed(f"Network {network} not found in OSPF routes on {device_name}")
                    else:
                        log.info(f"Network {network} found in OSPF routes on {device_name}")
                        
                log.info(f"OSPF routes verified on {device_name}")
            else:
                log.info(f"No specific routes to verify for {device_name}")
            
        except Exception as e:
            self.failed(f"Error checking OSPF routes on {device_name}: {str(e)}")
            

class CommonCleanup(aetest.CommonCleanup):
    """Cleanup Section"""
    
    @aetest.subsection
    def disconnect_from_devices(self, testbed):
        try:
            testbed.disconnect()
        except Exception as e:
            log.error(f"Error during cleanup: {str(e)}")


if __name__ == '__main__':
    # Set log level for standalone execution
    log.setLevel(logging.INFO)
    
    try:
        # Load testbed using absolute path
        testbed = load(TESTBED_PATH)
        log.info(f"Successfully loaded testbed file: {TESTBED_PATH}")
    except Exception as e:
        log.error(f"Failed to load testbed file: {TESTBED_PATH}")
        log.error(f"Error: {str(e)}")
        sys.exit(1)
    
    # Execute with testbed parameter
    aetest.main(testbed=testbed)