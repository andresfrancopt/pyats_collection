#!/usr/bin/env python

import os
from pyats.easypy import run
from genie.testbed import load

def main(runtime):
    """
    Main function that will be run by pyATS
    """
    # Get absolute path for testbed file
    testbed_path = os.path.join(os.path.dirname(__file__), 'testbed.yaml')
    
    # Load the testbed file
    testbed = load(testbed_path)
    
    # Get script path
    script_path = os.path.join(os.path.dirname(__file__), 'auto_script.py')
    
    # Run script with loaded testbed
    runtime.tasks.run(
        testscript=script_path,
        taskid="Connectivity Test",
        testbed=testbed
    )

if __name__ == '__main__':
    run(main)