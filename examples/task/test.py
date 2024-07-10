#!/usr/bin/python3

import signal

def exit_gracefully(signum, frame):
    print(f"Got signal {signal.Signals(signum).name}")

#signal.signal(signal.SIGINT, exit_gracefully)
#signal.signal(signal.SIGTERM, exit_gracefully)

print("Input first arg:")
arg = input()
print(f"The first arg is: {arg}")

print("Input second arg:")
arg = input()
print(f"The second arg is: {arg}")


