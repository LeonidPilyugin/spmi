import json
import sys
from pathlib import Path
from ...utils.exception import SpmiException

EXECUTABLE = "/usr/bin/env python3"

def generate_command(data: dict) -> str:
    path = Path(__file__)
    json_string = json.dumps(data, separators=(',', ':'))
    
    if "'" in json_string:
        raise SpmiException("Incorrect data")
    if "'" in str(path):
        raise SpmiException("Incorrect SPMI path")

    argument = f"{EXECUTABLE} '{path}' '{json_string}'"

    return argument


def parse_args() -> dict:
    return json.loads(sys.argv[1])

if __name__ == "__main__":
    pass

