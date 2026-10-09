import sys
import random

# Oh my god a different change (made on branch hw_1a) !!
if len(sys.argv) < 2:
    print("Script just accepts a single filename as a command-line argument")
    sys.exit(1)

filename = sys.argv[1]

with open(filename, 'r') as f:
    for line in f:
        if random.random() < 0.01:
            print(line, end="")