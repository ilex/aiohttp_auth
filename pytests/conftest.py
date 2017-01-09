"""Pytest configuration."""
import os.path
import sys


my_path = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(my_path, '..'))
