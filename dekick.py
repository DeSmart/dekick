#!/usr/bin/python3
"""
Entry point for DeKick.

It first checkes if all required packages are installed and then runs the main script thus it runs
without any main dependencies.
"""
from importlib import import_module
from os import environ

import debugpy

if environ.get("DEKICK_DEBUGGER") == "true":
    print("Waiting for debugger to attach on port 8753...")
    debugpy.listen(("0.0.0.0", 8753))
    debugpy.wait_for_client()


import_module("lib.main")
