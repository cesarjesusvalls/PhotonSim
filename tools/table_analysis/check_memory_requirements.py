#!/usr/bin/env python3
"""
Check memory requirements for high-resolution lookup table.
"""

import numpy as np

def estimate_memory_requirements():
    """Estimate memory for different bin configurations."""
    
    print("=== Lookup Table Memory Requirements ===\n")
    
    configs = [
        ("Previous", 20, 25, 20),
        ("High Resolution", 100, 100, 100),
        ("Ultra High", 200, 200, 200),
    ]
    
    for name, e_bins, a_bins, d_bins in configs:
        total_bins = e_bins * a_bins * d_bins
        
        # Each bin stores a float64 (8 bytes)
        histogram_size_mb = total_bins * 8 / (1024**2)
        
        # Metadata (bin edges, centers, etc.) - roughly 3 arrays per dimension
        metadata_size_mb = (e_bins + a_bins + d_bins) * 3 * 8 / (1024**2)
        
        total_size_mb = histogram_size_mb + metadata_size_mb
        
        print(f"{name}:")
        print(f"  Bins: {e_bins} × {a_bins} × {d_bins} = {total_bins:,}")
        print(f"  Histogram: {histogram_size_mb:.1f} MB")
        print(f"  Metadata: {metadata_size_mb:.1f} MB")
        print(f"  Total: {total_size_mb:.1f} MB")
        print(f"  Coverage estimate: {min(100, total_bins/10000*27):.1f}%")
        print()

def test_array_creation():
    """Test if we can create the 100x100x100 array."""
    print("=== Testing 100×100×100 Array Creation ===")
    
    try:
        # Test creating the array
        test_array = np.zeros((100, 100, 100), dtype=np.float64)
        memory_mb = test_array.nbytes / (1024**2)
        
        print(f"✅ Successfully created 100×100×100 array")
        print(f"✅ Memory used: {memory_mb:.1f} MB")
        print(f"✅ Shape: {test_array.shape}")
        print(f"✅ Data type: {test_array.dtype}")
        
        # Test some operations
        test_array[50, 50, 50] = 1000
        test_result = test_array[50, 50, 50]
        print(f"✅ Array operations work: {test_result}")
        
        del test_array
        print(f"✅ Array cleanup successful")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to create array: {e}")
        return False

def main():
    estimate_memory_requirements()
    success = test_array_creation()
    
    if success:
        print("\n🚀 Ready to create high-resolution lookup table!")
        print("Recommended command:")
        print("python3 tools/create_photon_table.py --events 1000 --energy-bins 100 --angle-bins 100 --distance-bins 100")
    else:
        print("\n⚠️  Consider reducing bin numbers or increasing available memory.")

if __name__ == "__main__":
    main()