#!/usr/bin/env python

import os
from pyats.easypy import run
from genie.testbed import load

def main(runtime):
    """
    Main function that will be run by pyATS.
    Executes both connectivity and OSPF tests.
    """
    # Get absolute path for testbed file
    testbed_path = os.path.join(os.path.dirname(__file__), 
                                '..', 'testbeds', 'testbed.yaml')
    
    # Load the testbed file
    testbed = load(testbed_path)
    
    # Get script paths
    connectivity_path = os.path.join(os.path.dirname(__file__), 
                                    '..', 'tests', 'connectivity', 'test_basic.py')
    ospf_path = os.path.join(os.path.dirname(__file__), 
                            '..', 'tests', 'routing', 'test_ospf.py')
    
    # Run tests
    runtime.tasks.run(
        testscript=connectivity_path,
        taskid="Connectivity Tests",
        testbed=testbed
    )
    
    runtime.tasks.run(
        testscript=ospf_path,
        taskid="OSPF Tests",
        testbed=testbed
    )

if __name__ == '__main__':
    run(main)