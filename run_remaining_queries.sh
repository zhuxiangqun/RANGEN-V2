#!/bin/bash
echo "Running Q2..."
python3 verify_q2.py > verify_q2_run4.log 2>&1
echo "Q2 finished. Exit code: $?"

echo "Running Q3..."
python3 verify_q3.py > verify_q3_run4.log 2>&1
echo "Q3 finished. Exit code: $?"

echo "Running Q4..."
python3 verify_q4.py > verify_q4_run4.log 2>&1
echo "Q4 finished. Exit code: $?"
