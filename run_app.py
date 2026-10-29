#!/usr/bin/env python3
"""
AI Driven Building Architectural Design System - Launch Orchestrator.
Launches api_server.py and automatically opens the user's default browser.
"""

import os
import sys
import webbrowser
import threading
import time

def open_browser():
    time.sleep(1.2)
    url = "http://127.0.0.1:8000"
    print(f"\n[LAUNCH] Opening Web Application Studio in default browser: {url}\n")
    webbrowser.open(url)

if __name__ == "__main__":
    from api_server import start_server

    # Launch browser in a background thread
    threading.Thread(target=open_browser, daemon=True).start()

    # Start API & web server
    start_server(port=8000)
