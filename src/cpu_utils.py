#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CPU Detection Utilities

Functions to detect CPU characteristics like hyperthreading and 
optimize parallelization accordingly.

@author: ffx
"""

import os
import platform


def detect_physical_cores():
    """
    Detect the number of physical CPU cores (excluding hyperthreading).
    
    Returns:
        int: Number of physical cores, or logical cores if detection fails
    """
    logical_cores = os.cpu_count() or 2
    
    try:
        # Linux: Read from /proc/cpuinfo
        if platform.system() == "Linux":
            return _detect_physical_cores_linux()
        
        # Windows: Use wmic command
        elif platform.system() == "Windows":
            return _detect_physical_cores_windows()
        
        # macOS: Use sysctl command
        elif platform.system() == "Darwin":
            return _detect_physical_cores_macos()
        
        else:
            # Fallback: assume no hyperthreading
            return logical_cores
            
    except Exception:
        # If detection fails, return logical cores as fallback
        return logical_cores


def _detect_physical_cores_linux():
    """Detect physical cores on Linux using /proc/cpuinfo"""
    try:
        with open('/proc/cpuinfo', 'r') as f:
            cpuinfo = f.read()
        
        # Count unique physical CPU IDs and core IDs
        physical_ids = set()
        core_ids_per_physical = {}
        
        current_physical_id = None
        current_core_id = None
        
        for line in cpuinfo.split('\n'):
            if line.startswith('physical id'):
                current_physical_id = line.split(':')[1].strip()
            elif line.startswith('core id'):
                current_core_id = line.split(':')[1].strip()
            elif line.startswith('processor') and current_physical_id is not None and current_core_id is not None:
                physical_ids.add(current_physical_id)
                if current_physical_id not in core_ids_per_physical:
                    core_ids_per_physical[current_physical_id] = set()
                core_ids_per_physical[current_physical_id].add(current_core_id)
                current_physical_id = None
                current_core_id = None
        
        # Calculate total physical cores
        total_physical_cores = sum(len(cores) for cores in core_ids_per_physical.values())
        
        if total_physical_cores > 0:
            return total_physical_cores
        else:
            # Fallback: assume logical cores are physical cores
            return os.cpu_count() or 2
            
    except (FileNotFoundError, ValueError, IndexError):
        return os.cpu_count() or 2


def _detect_physical_cores_windows():
    """Detect physical cores on Windows using wmic"""
    import subprocess
    
    try:
        # Get number of physical processors
        result = subprocess.run(
            ['wmic', 'cpu', 'get', 'NumberOfCores', '/value'],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode == 0:
            cores = 0
            for line in result.stdout.strip().split('\n'):
                if line.startswith('NumberOfCores='):
                    cores += int(line.split('=')[1])
            
            if cores > 0:
                return cores
        
        return os.cpu_count() or 2
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
        return os.cpu_count() or 2


def _detect_physical_cores_macos():
    """Detect physical cores on macOS using sysctl"""
    import subprocess
    
    try:
        result = subprocess.run(
            ['sysctl', '-n', 'hw.physicalcpu'],
            capture_output=True, text=True, timeout=5
        )
        
        if result.returncode == 0:
            cores = int(result.stdout.strip())
            if cores > 0:
                return cores
        
        return os.cpu_count() or 2
        
    except (subprocess.TimeoutExpired, subprocess.SubprocessError, ValueError):
        return os.cpu_count() or 2


def get_optimal_workers(min_workers=1, max_percentage=0.8):
    """
    Get optimal number of worker processes based on CPU capabilities.
    
    Takes hyperthreading into account - if detected, uses physical cores
    instead of logical cores for CPU-intensive tasks.
    
    Args:
        min_workers (int): Minimum number of workers to return
        max_percentage (float): Maximum percentage of cores to use (0.0-1.0)
        
    Returns:
        int: Optimal number of workers
    """
    logical_cores = os.cpu_count() or 2
    physical_cores = detect_physical_cores()
    
    # Use physical cores if hyperthreading is detected
    if physical_cores < logical_cores:
        # Hyperthreading detected - use physical cores
        effective_cores = physical_cores
        ht_detected = True
    else:
        # No hyperthreading or detection failed - use logical cores
        effective_cores = logical_cores
        ht_detected = False
    
    # Calculate optimal workers
    optimal_workers = max(min_workers, int(effective_cores * max_percentage))
    
    return optimal_workers, effective_cores, logical_cores, ht_detected


if __name__ == "__main__":
    # Test the detection
    logical = os.cpu_count()
    physical = detect_physical_cores()
    optimal, effective, total, ht = get_optimal_workers()
    
    print(f"Logical cores: {logical}")
    print(f"Physical cores: {physical}")
    print(f"Hyperthreading detected: {ht}")
    print(f"Effective cores for processing: {effective}")
    print(f"Optimal workers: {optimal}")