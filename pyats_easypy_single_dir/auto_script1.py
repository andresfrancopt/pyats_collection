#!/usr/bin/env python

import logging
import os
from pyats import aetest
from pyats.log.utils import banner
from genie.testbed import load

log = logging.getLogger(__name__)

# Get the absolute path to testbed.yaml in the same directory as this script
TESTBED_PATH = os.path.join(os.path.dirname(__file__), 'testbed.yaml')

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
        aetest.loop.mark(Connectivity_Test, device_name=list(testbed.devices.keys()))

class Connectivity_Test(aetest.Testcase):
    """Network Connectivity Test Suite
    
    This test suite validates:
    - Basic device reachability
    - Peer router connectivity
    - End host reachability"""

    @aetest.test
    def ping_test(self, testbed, device_name):
        """✨ Validates basic connectivity to device management IP"""
        device = testbed.devices[device_name]
        try:
            ip = device.connections.cli.ip
            log.info(f"Pinging {device_name} at {ip}")
            result = device.execute(f"ping {ip}")
            if "Success rate is 0 percent" in result:
                self.failed(f"Ping to {device_name} failed")
        except Exception as e:
            self.failed(f"Error executing ping on {device_name}: {str(e)}")

    @aetest.test
    def ping_peer_ip(self, testbed, device_name):
        device = testbed.devices[device_name]
        try:
            # Define peer IP mapping
            peer_ips = {
                'R1': '172.16.0.2',  # R2's IP
                'R2': '172.16.0.1'   # R1's IP
            }
            
            # Get peer IP for current device
            if device_name in peer_ips:
                peer_ip = peer_ips[device_name]
                log.info(f"Device {device_name} pinging peer IP {peer_ip}")
                result = device.execute(f"ping {peer_ip}")
                if "Success rate is 0 percent" in result:
                    self.failed(f"Ping from {device_name} to {peer_ip} failed")
                else:
                    log.info(f"Ping from {device_name} to {peer_ip} successful")
        except Exception as e:
            self.failed(f"Error executing peer ping on {device_name}: {str(e)}")

    @aetest.test
    def ping_pc_hosts(self, testbed, device_name):
        device = testbed.devices[device_name]
        try:
            # Define PC host IPs
            pc_ips = {
                'PC1': '172.16.1.1',
                'PC2': '172.16.2.1'
            }
            
            # Try to ping each PC from the current device
            for pc_name, pc_ip in pc_ips.items():
                log.info(f"Device {device_name} pinging {pc_name} at {pc_ip}")
                result = device.execute(f"ping {pc_ip}")
                if "Success rate is 0 percent" in result:
                    self.failed(f"Ping from {device_name} to {pc_name}({pc_ip}) failed")
                else:
                    log.info(f"Ping from {device_name} to {pc_name}({pc_ip}) successful")
                    
        except Exception as e:
            self.failed(f"Error executing PC ping test on {device_name}: {str(e)}")

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
    
    # Load testbed directly from the known path
    testbed = load(TESTBED_PATH)
    
    # Execute with testbed parameter
    aetest.main(testbed=testbed)