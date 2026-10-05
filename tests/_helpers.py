import copy
import json
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "scripts"))

EXAMPLE_REPORT = os.path.join(ROOT, "examples", "report.example.pt-BR.json")
EXAMPLE_BRIEF = os.path.join(ROOT, "examples", "brief.example.json")


def load(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def example_report():
    return copy.deepcopy(load(EXAMPLE_REPORT))


def example_brief():
    return copy.deepcopy(load(EXAMPLE_BRIEF))


def has(module):
    try:
        __import__(module)
        return True
    except ImportError:
        return False
