# SOCAR Hackathon 2025 - Data Forensics Challenge
## Solution Summary

**Team:** Data Archaeologist  
**Challenge:** Track 1 - Forensics & Data Recovery  
**Date:** December 13, 2025

---

## 🏆 Results

### Task 1: Find Hidden Flag (100 points)
**Status:** ✅ COMPLETED  
**Flag:** `FLAG{DATA_ARCHAEOLOGIST_LVL_99}`  
**Location:** Offset 0xa060 in `archive_batch_seismic_readings.parquet`  
**Method:** Binary pattern matching for FLAG{} signature

### Task 2: Recover Corrupted Parquet Files (100 points)
**Status:** ✅ COMPLETED  
**Files Recovered:** 2/2  
- `archive_batch_seismic_readings.parquet` - 1750 rows
- `archive_batch_seismic_readings_2.parquet` - 1750 rows (hex-encoded)

**Corruption Types Handled:**
1. Appended data after valid Parquet footer
2. Hex-encoded binary data
3. Corrupted PAR1 magic bytes

### Bonus: Legacy SGX Format Parsing
**Status:** ✅ COMPLETED  
**Files Parsed:** 9 legacy seismic files (1991-1994)  
**Total Traces:** 3660 seismic readings  
**Output:** Combined Parquet format for modern analysis

---

## 📁 Project Structure


