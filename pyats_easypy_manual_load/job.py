from pyats.easypy import run

# job file needs to have a main() definition
# which is the primary entry point for starting job files

def main():
    # run testscript 1
    run(testscript='escript.py')
