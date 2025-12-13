#!/usr/bin/env python3
"""
Data Quality Tests for Data Vault
==================================
Tests to ensure data integrity, completeness, and validity
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple
import sys

project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))


class DataVaultQualityTests:
    """Comprehensive data quality tests for the vault"""
    
    def __init__(self, vault_dir: str):
        self.vault_dir = Path(vault_dir)
        self.test_results = []
        self.failed_tests = []
        
    def log_test(self, test_name: str, passed: bool, message: str, details: dict = None):
        """Log test result"""
        result = {
            'test': test_name,
            'status': '✅ PASS' if passed else '❌ FAIL',
            'message': message,
            'details': details or {}
        }
        self.test_results.append(result)
        
        if not passed:
            self.failed_tests.append(result)
        
        print(f"{result['status']} | {test_name}")
        print(f"   {message}")
        if details:
            for key, value in details.items():
                print(f"   - {key}: {value}")
        print()
    
    def test_hub_uniqueness(self) -> bool:
        """Test 1: Hub hash keys must be unique"""
        print("="*70)
        print("TEST 1: Hub Hash Key Uniqueness")
        print("="*70 + "\n")
        
        all_passed = True
        
        for hub_file in ['hub_well', 'hub_survey', 'hub_sensor']:
            df = pd.read_parquet(self.vault_dir / f"{hub_file}.parquet")
            hash_key_col = f"{hub_file.split('_')[1]}_hash_key"
            
            total_records = len(df)
            unique_keys = df[hash_key_col].nunique()
            duplicates = total_records - unique_keys
            
            passed = duplicates == 0
            all_passed = all_passed and passed
            
            self.log_test(
                f"{hub_file} - Hash Key Uniqueness",
                passed,
                f"Found {duplicates} duplicate hash keys" if not passed else "All hash keys are unique",
                {
                    'total_records': total_records,
                    'unique_keys': unique_keys,
                    'duplicates': duplicates
                }
            )
        
        return all_passed
    
    def test_business_key_uniqueness(self) -> bool:
        """Test 2: Business keys in hubs must be unique"""
        print("="*70)
        print("TEST 2: Business Key Uniqueness")
        print("="*70 + "\n")
        
        all_passed = True
        
        tests = [
            ('hub_well', 'well_id'),
            ('hub_survey', 'survey_type_id'),
            ('hub_sensor', 'sensor_id')
        ]
        
        for hub_file, business_key in tests:
            df = pd.read_parquet(self.vault_dir / f"{hub_file}.parquet")
            
            total_records = len(df)
            unique_keys = df[business_key].nunique()
            duplicates = total_records - unique_keys
            
            passed = duplicates == 0
            all_passed = all_passed and passed
            
            self.log_test(
                f"{hub_file} - {business_key} Uniqueness",
                passed,
                f"Found {duplicates} duplicate business keys" if not passed else "All business keys are unique",
                {
                    'total_records': total_records,
                    'unique_keys': unique_keys
                }
            )
        
        return all_passed
    
    def test_referential_integrity(self) -> bool:
        """Test 3: Link foreign keys must exist in hubs"""
        print("="*70)
        print("TEST 3: Referential Integrity")
        print("="*70 + "\n")
        
        # Load data
        link_df = pd.read_parquet(self.vault_dir / "link_seismic_reading.parquet")
        hub_well = pd.read_parquet(self.vault_dir / "hub_well.parquet")
        hub_survey = pd.read_parquet(self.vault_dir / "hub_survey.parquet")
        hub_sensor = pd.read_parquet(self.vault_dir / "hub_sensor.parquet")
        
        all_passed = True
        
        # Test well references
        well_orphans = ~link_df['well_hash_key'].isin(hub_well['well_hash_key'])
        well_orphan_count = well_orphans.sum()
        passed = well_orphan_count == 0
        all_passed = all_passed and passed
        
        self.log_test(
            "Link → Hub_Well Integrity",
            passed,
            f"Found {well_orphan_count} orphaned well references" if not passed else "All well references are valid",
            {
                'link_records': len(link_df),
                'valid_references': (~well_orphans).sum(),
                'orphaned_references': well_orphan_count
            }
        )
        
        # Test survey references
        survey_orphans = ~link_df['survey_hash_key'].isin(hub_survey['survey_hash_key'])
        survey_orphan_count = survey_orphans.sum()
        passed = survey_orphan_count == 0
        all_passed = all_passed and passed
        
        self.log_test(
            "Link → Hub_Survey Integrity",
            passed,
            f"Found {survey_orphan_count} orphaned survey references" if not passed else "All survey references are valid",
            {
                'link_records': len(link_df),
                'valid_references': (~survey_orphans).sum(),
                'orphaned_references': survey_orphan_count
            }
        )
        
        # Test sensor references (allow NULL for SGX data)
        sensor_refs = link_df[link_df['sensor_hash_key'].notna()]
        if len(sensor_refs) > 0:
            sensor_orphans = ~sensor_refs['sensor_hash_key'].isin(hub_sensor['sensor_hash_key'])
            sensor_orphan_count = sensor_orphans.sum()
            passed = sensor_orphan_count == 0
            all_passed = all_passed and passed
            
            self.log_test(
                "Link → Hub_Sensor Integrity",
                passed,
                f"Found {sensor_orphan_count} orphaned sensor references" if not passed else "All sensor references are valid",
                {
                    'link_records_with_sensor': len(sensor_refs),
                    'valid_references': (~sensor_orphans).sum(),
                    'orphaned_references': sensor_orphan_count,
                    'null_sensors': (link_df['sensor_hash_key'].isna()).sum()
                }
            )
        
        return all_passed
    
    def test_satellite_link_integrity(self) -> bool:
        """Test 4: Satellite records must reference existing links"""
        print("="*70)
        print("TEST 4: Satellite → Link Integrity")
        print("="*70 + "\n")
        
        sat_df = pd.read_parquet(self.vault_dir / "sat_seismic_measurements.parquet")
        link_df = pd.read_parquet(self.vault_dir / "link_seismic_reading.parquet")
        
        orphans = ~sat_df['link_hash_key'].isin(link_df['link_hash_key'])
        orphan_count = orphans.sum()
        
        passed = orphan_count == 0
        
        self.log_test(
            "Sat_Seismic_Measurements → Link Integrity",
            passed,
            f"Found {orphan_count} orphaned satellite records" if not passed else "All satellite records reference valid links",
            {
                'satellite_records': len(sat_df),
                'valid_references': (~orphans).sum(),
                'orphaned_records': orphan_count
            }
        )
        
        return passed
    
    def test_data_completeness(self) -> bool:
        """Test 5: Critical fields must not be NULL"""
        print("="*70)
        print("TEST 5: Data Completeness")
        print("="*70 + "\n")
        
        all_passed = True
        
        # Check satellite measurements
        sat_df = pd.read_parquet(self.vault_dir / "sat_seismic_measurements.parquet")
        
        critical_fields = ['depth_ft', 'amplitude', 'quality_flag']
        
        for field in critical_fields:
            null_count = sat_df[field].isna().sum()
            passed = null_count == 0
            all_passed = all_passed and passed
            
            self.log_test(
                f"Sat_Seismic_Measurements - {field} Completeness",
                passed,
                f"Found {null_count} NULL values" if not passed else "No NULL values found",
                {
                    'total_records': len(sat_df),
                    'null_count': null_count,
                    'completeness_pct': f"{((len(sat_df) - null_count) / len(sat_df) * 100):.2f}%"
                }
            )
        
        return all_passed
    
    def test_metadata_presence(self) -> bool:
        """Test 6: All tables must have metadata columns"""
        print("="*70)
        print("TEST 6: Metadata Presence")
        print("="*70 + "\n")
        
        all_passed = True
        required_metadata = ['load_timestamp', 'record_source']
        
        vault_files = list(self.vault_dir.glob("*.parquet"))
        
        for vault_file in vault_files:
            df = pd.read_parquet(vault_file)
            
            missing_cols = [col for col in required_metadata if col not in df.columns]
            passed = len(missing_cols) == 0
            all_passed = all_passed and passed
            
            self.log_test(
                f"{vault_file.stem} - Metadata Columns",
                passed,
                f"Missing columns: {missing_cols}" if not passed else "All metadata columns present",
                {
                    'required_columns': required_metadata,
                    'present_columns': [col for col in required_metadata if col in df.columns],
                    'missing_columns': missing_cols
                }
            )
        
        return all_passed
    
    def test_row_counts(self) -> bool:
        """Test 7: Verify expected row counts"""
        print("="*70)
        print("TEST 7: Row Count Validation")
        print("="*70 + "\n")
        
        all_passed = True
        
        # Expected minimums based on source data
        expected_counts = {
            'hub_well': 1,  # At least 1 well
            'hub_survey': 3,  # Exactly 3 survey types
            'hub_sensor': 1,  # At least 1 sensor
            'link_seismic_reading': 100,  # At least 100 readings
            'sat_seismic_measurements': 100  # At least 100 measurements
        }
        
        for table, min_expected in expected_counts.items():
            df = pd.read_parquet(self.vault_dir / f"{table}.parquet")
            actual_count = len(df)
            
            passed = actual_count >= min_expected
            all_passed = all_passed and passed
            
            self.log_test(
                f"{table} - Row Count",
                passed,
                f"Expected >= {min_expected}, got {actual_count}",
                {
                    'expected_minimum': min_expected,
                    'actual_count': actual_count,
                    'status': 'above minimum' if passed else 'below minimum'
                }
            )
        
        return all_passed
    
    def test_hash_key_format(self) -> bool:
        """Test 8: Hash keys must be valid MD5 format"""
        print("="*70)
        print("TEST 8: Hash Key Format Validation")
        print("="*70 + "\n")
        
        all_passed = True
        
        # MD5 hash is 32 hex characters
        import re
        md5_pattern = re.compile(r'^[a-f0-9]{32}$')
        
        hash_key_tables = [
            ('hub_well', 'well_hash_key'),
            ('hub_survey', 'survey_hash_key'),
            ('hub_sensor', 'sensor_hash_key'),
            ('link_seismic_reading', 'link_hash_key')
        ]
        
        for table, hash_col in hash_key_tables:
            df = pd.read_parquet(self.vault_dir / f"{table}.parquet")
            
            invalid = ~df[hash_col].astype(str).str.match(md5_pattern)
            invalid_count = invalid.sum()
            
            passed = invalid_count == 0
            all_passed = all_passed and passed
            
            self.log_test(
                f"{table} - {hash_col} Format",
                passed,
                f"Found {invalid_count} invalid hash keys" if not passed else "All hash keys are valid MD5 format",
                {
                    'total_keys': len(df),
                    'valid_keys': (~invalid).sum(),
                    'invalid_keys': invalid_count
                }
            )
        
        return all_passed
    
    def run_all_tests(self):
        """Run all data quality tests"""
        print("\n" + "="*70)
        print("DATA VAULT QUALITY TEST SUITE")
        print("="*70 + "\n")
        
        tests = [
            self.test_hub_uniqueness,
            self.test_business_key_uniqueness,
            self.test_referential_integrity,
            self.test_satellite_link_integrity,
            self.test_data_completeness,
            self.test_metadata_presence,
            self.test_row_counts,
            self.test_hash_key_format
        ]
        
        for test in tests:
            test()
        
        # Final Summary
        print("="*70)
        print("TEST SUMMARY")
        print("="*70)
        
        total_tests = len(self.test_results)
        passed_tests = total_tests - len(self.failed_tests)
        
        print(f"\nTotal Tests: {total_tests}")
        print(f"Passed: {passed_tests} ✅")
        print(f"Failed: {len(self.failed_tests)} ❌")
        print(f"Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if self.failed_tests:
            print("\n" + "="*70)
            print("FAILED TESTS")
            print("="*70)
            for failure in self.failed_tests:
                print(f"\n❌ {failure['test']}")
                print(f"   {failure['message']}")
        else:
            print("\n✅ ALL TESTS PASSED!")
        
        print("\n" + "="*70)
        
        return len(self.failed_tests) == 0


if __name__ == '__main__':
    tester = DataVaultQualityTests(
        vault_dir='track_2_data_vault/vault_data'
    )
    
    all_passed = tester.run_all_tests()
    
    sys.exit(0 if all_passed else 1)
