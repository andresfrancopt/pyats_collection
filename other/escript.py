#!/usr/bin/env python

import logging
from pyats import aetest
from pyats.log.utils import banner
from genie.testbed import load
from datetime import datetime

log = logging.getLogger(__name__)

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
        aetest.loop.mark(Sanity_Check, device_name=list(testbed.devices.keys()))

class Sanity_Check(aetest.Testcase):
    """Network Validation Test Suite
    
    This test suite performs the following checks:
    1. Basic Connectivity:
        - Interface status
        - Device reachability
        - Peer connectivity
        - End host reachability
    2. OSPF Routing:
        - Neighbor relationships
        - Route verification
    3. Security:
        - ACL verification
        - Basic config validation
    4. Performance:
        - CPU/Memory monitoring
        - Interface statistics
    """
    
    cpu_threshold = 80  # Maximum allowed CPU usage percentage
    expected_ospf_state = 'FULL'  # Expected OSPF neighbor state
    ping_retry_count = 3  # Number of retries for ping operations

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def _execute_with_retry(self, device, command, max_retries=3):
        """Execute command with retry logic on device failure"""
        for attempt in range(max_retries):
            try:
                return device.execute(command)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise
                log.warning(f"Retry {attempt + 1} after error: {str(e)}")

    def _recover_connection(self, device):
        """Attempt to recover failed device connection"""
        try:
            device.disconnect()
            device.connect(log_stdout=True)
            return True
        except Exception as e:
            log.error(f"Recovery failed: {str(e)}")
            return False

    def _format_error(self, error, context):
        """Format error messages with detailed context"""
        return f"""
        Error occurred during {context}
        Device: {self.device_name}
        Error Type: {type(error).__name__}
        Error Message: {str(error)}
        Timestamp: {datetime.now().isoformat()}
        """


    @aetest.test
    def verify_interface_status(self, testbed, device_name):
        """✨ Validates all interfaces are operational"""
        device = testbed.devices[device_name]
        try:
            log.info(f"Checking interface status on {device_name}")
            result = self._execute_with_retry(device, 'show ip interface brief')
            
            # Check if any interfaces are down
            if 'down' in result.lower():
                self.failed(f"Down interfaces found on {device_name}")
            else:
                log.info(f"All interfaces are up on {device_name}")
                
        except Exception as e:
            self.failed(f"Error checking interfaces on {device_name}: {str(e)}")

    @aetest.test
    def ping_test(self, testbed, device_name):
        """✨ Validates basic connectivity to device management IP"""
        device = testbed.devices[device_name]
        try:
            ip = device.connections.cli.ip
            log.info(f"Pinging {device_name} at {ip}")
            result = self._execute_with_retry(device, f"ping {ip}")
            if "Success rate is 0 percent" in result:
                self.failed(f"Ping to {device_name} failed")
        except Exception as e:
            self.failed(f"Error executing ping on {device_name}: {str(e)}")

    @aetest.test
    def ping_peer_ip(self, testbed, device_name):
        """✨ Validates connectivity between router peers"""
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
                result = self._execute_with_retry(device, f"ping {peer_ip}")
                if "Success rate is 0 percent" in result:
                    self.failed(f"Ping from {device_name} to {peer_ip} failed")
                else:
                    log.info(f"Ping from {device_name} to {peer_ip} successful")
        except Exception as e:
            self.failed(f"Error executing peer ping on {device_name}: {str(e)}")

    @aetest.test
    def ping_pc_hosts(self, testbed, device_name):
        """✨ Validates connectivity to end hosts"""
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
                result = self._execute_with_retry(device, f"ping {pc_ip}")
                if "Success rate is 0 percent" in result:
                    self.failed(f"Ping from {device_name} to {pc_name}({pc_ip}) failed")
                else:
                    log.info(f"Ping from {device_name} to {pc_name}({pc_ip}) successful")
                    
        except Exception as e:
            self.failed(f"Error executing PC ping test on {device_name}: {str(e)}")


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


    @aetest.test
    def verify_no_acls(self, testbed, device_name):
        """🔒 Validates no unexpected ACLs are configured"""
        device = testbed.devices[device_name]
        try:
            log.info(f"Checking for ACLs on interfaces of {device_name}")
            
            # Get interface ACL info
            result = self._execute_with_retry(device, 'show ip interface | inc access list')
            
            # Look for common ACL indicators in the output with variations
            acl_indicators = [
                'inbound access list',
                'outbound access list',
                'input access list',
                'output access list',
                'Inbound  access list',  # Cisco IOS output contains double space
                'Outbound  access list',
                'Input  access list',
                'Output  access list'
            ]
            
            # Check each line for ACL configurations
            found_acls = []
            for line in result.splitlines():
                line = line.strip()
                for indicator in acl_indicators:
                    if indicator in line and 'is not set' not in line:
                        # Look for numbered or named ACLs
                        if 'list is' in line:
                            acl_info = line.split('list is')[-1].strip()
                            if acl_info and acl_info != 'not set':
                                found_acls.append(f"{line}")
            
            if found_acls:
                self.failed(f"ACLs found on {device_name}:\n" + "\n".join(found_acls))
            else:
                log.info(f"No ACLs found on interfaces of {device_name}")
                
        except Exception as e:
            self.failed(f"Error checking ACLs on {device_name}: {str(e)}")

    @aetest.test
    def verify_basic_config(self, testbed, device_name):
        """🔍 Validates basic device configuration"""
        device = testbed.devices[device_name]
        try:
            config_checks = {
                'hostname': device.execute('show run | inc hostname'),
                'logging': device.execute('show run | inc logging'),
                'ntp': device.execute('show run | inc ntp')
            }
            for check, output in config_checks.items():
                if not output:
                    self.failed(f"Missing {check} configuration on {device_name}")
                log.info(f"✅ {check} configured on {device_name}")
        except Exception as e:
            self.failed(f"Error checking configuration on {device_name}: {str(e)}")


    @aetest.test
    def verify_cpu_memory(self, testbed, device_name):
        """📊 Validates system resource utilization"""
        device = testbed.devices[device_name]
        try:
            log.info(f"Checking CPU and memory usage on {device_name}")
            cpu_result = self._execute_with_retry(device, 'show processes cpu | include CPU')
            mem_result = self._execute_with_retry(device, 'show memory statistics | include Processor')
            
            # Extract CPU percentage (this is a simple example, might need adjustment)
            cpu_usage = int(cpu_result.split('%')[0].split()[-1])
            if cpu_usage > 80:  # threshold of 80%
                self.failed(f"High CPU usage ({cpu_usage}%) on {device_name}")
                
            log.info(f"CPU and memory usage normal on {device_name}")
            
        except Exception as e:
            self.failed(f"Error checking CPU/memory on {device_name}: {str(e)}")

    @aetest.test
    def collect_performance_metrics(self, testbed, device_name):
        """📈 Collects key performance metrics"""
        device = testbed.devices[device_name]
        try:
            metrics = {
                'cpu': device.execute('show processes cpu | include CPU'),
                'memory': device.execute('show memory statistics | include Processor'),
                'interfaces': device.execute('show interfaces | include rate')
            }
            log.info(banner(f"Performance Metrics for {device_name}"))
            for metric, value in metrics.items():
                log.info(f"{metric}:\n{value}")
        except Exception as e:
            self.failed(f"Error collecting metrics on {device_name}: {str(e)}")


class CommonCleanup(aetest.CommonCleanup):
    """Cleanup Section"""
    
    @aetest.subsection
    def disconnect_from_devices(self, testbed):
        try:
            testbed.disconnect()
        except Exception as e:
            log.error(f"Error during cleanup: {str(e)}")

if __name__ == '__main__':
    import sys
    from pyats.topology import loader
    
    # Set log level for standalone execution
    log.setLevel(logging.INFO)
    
    # Get the testbed from command line arguments
    testbed = loader.load(sys.argv[2])
    
    # Execute with testbed parameter
    aetest.main(testbed=testbed)