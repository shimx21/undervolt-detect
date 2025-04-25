#!/bin/bash

# Define n_cores and target frequency
TOTAL_CORES=7         # Max id of cores (7 for 8 cores)
TARGET_FREQ="800000"  # (kHz)

# Check cpufreq-set
if ! command -v cpufreq-set &> /dev/null; then
    echo "Error: `cpufrequtils` not installed. run `sudo apt install cpufrequtils` first."
    exit 1
fi

# Set governor of all cores to `userspace`
for core in $(seq 0 $TOTAL_CORES); do
    sudo cpufreq-set -c $core -g userspace
    if [ $? -ne 0 ]; then
        echo "Failed to set governor for core $core ! Check whether the governor is supported."
        exit 1
    fi
done

# Fix CPU frequency for all cores
for core in $(seq 0 $TOTAL_CORES); do
    sudo cpufreq-set -c $core -f $TARGET_FREQ
    if [ $? -ne 0 ]; then
        echo "Frequence setuo fir core $core failed! Check whether the frequency is supported."
        exit 1
    fi
done

# Check if the frequency is set correctly
echo "Validating result..."
cpufreq-info | grep -E "current policy|current CPU frequency"
