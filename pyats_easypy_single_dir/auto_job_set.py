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
    testbed_path = os.path.join(os.path.dirname(__file__), 'testbed.yaml')
    
    # Load the testbed file
    testbed = load(testbed_path)
    
    # Get script paths
    script1_path = os.path.join(os.path.dirname(__file__), 'auto_script1.py')
    script2_path = os.path.join(os.path.dirname(__file__), 'auto_script2.py')
    
    # Run connectivity tests
    runtime.tasks.run(
        testscript=script1_path,
        taskid="Connectivity Tests",
        testbed=testbed
    )
    
    # Run OSPF tests
    runtime.tasks.run(
        testscript=script2_path,
        taskid="OSPF Tests",
        testbed=testbed
    )

if __name__ == '__main__':
    run(main)