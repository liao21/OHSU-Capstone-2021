@echo off
coverage run test_basic.py > test_output.txt
coverage html
pause