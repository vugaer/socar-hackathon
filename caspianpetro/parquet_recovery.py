"""Parquet Recovery - Corrupted File Recovery"""

import struct
from pathlib import Path
from typing import Union, Optional
import pandas as pd


class ParquetRecovery:
    """Recovery tools for corrupted Parquet files"""
    
    MAGIC_BYTES = b'PAR1'
    
    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.recovery_log = []
    
    def recover_file(self, filepath: Union[str, Path], output_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
        """Recover a corrupted Parquet file"""
        filepath = Path(filepath)
        
        if self.verbose:
            print(f"\nRecovering: {filepath.name}")
            print("=" * 60)
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        self._log(f"Original size: {len(data)} bytes")
        
        cleaned_data = self._apply_recovery_strategies(data)
        
        if cleaned_data is None:
            raise ValueError("Could not recover Parquet file")
        
        if output_path:
            output_path = Path(output_path)
            output_path.parent.mkdir(parents=True, exist_ok=True)
            with open(output_path, 'wb') as f:
                f.write(cleaned_data)
            self._log(f"Saved to: {output_path}")
        
        import io
        df = pd.read_parquet(io.BytesIO(cleaned_data))
        
        if self.verbose:
            print(f"✓ SUCCESS! Recovered {len(df)} rows")
        
        return df
    
    def _apply_recovery_strategies(self, data: bytes) -> Optional[bytes]:
        """Apply recovery strategies"""
        
        if self._is_hex_encoded(data):
            self._log("Detected hex-encoded file")
            try:
                hex_string = data.decode('ascii').strip().replace('\n', '').replace(' ', '')
                data = bytes.fromhex(hex_string)
                self._log(f"Decoded to {len(data)} bytes")
            except Exception as e:
                self._log(f"Hex decoding failed: {e}")
                return None
        
        par1_positions = self._find_par1_positions(data)
        self._log(f"PAR1 positions: {par1_positions}")
        
        if not par1_positions:
            return None
        
        if len(par1_positions) >= 2 and par1_positions[0] == 0:
            cleaned_data = data[:par1_positions[-1] + 4]
            self._log(f"Truncated to {len(cleaned_data)} bytes")
            
            if self._verify_parquet(cleaned_data):
                return cleaned_data
        
        elif len(par1_positions) == 1:
            if self._verify_parquet(data):
                return data
        
        return None
    
    def _is_hex_encoded(self, data: bytes) -> bool:
        """Check if data is hex-encoded"""
        if data[:2] in [b'50', b'35']:
            try:
                sample = data[:100].decode('ascii')
                hex_chars = sum(c in '0123456789abcdefABCDEF' for c in sample)
                return hex_chars / len(sample) > 0.9
            except:
                pass
        return False
    
    def _find_par1_positions(self, data: bytes) -> list:
        """Find all PAR1 positions"""
        positions = []
        pos = 0
        while pos < len(data) - 3:
            pos = data.find(self.MAGIC_BYTES, pos)
            if pos == -1:
                break
            positions.append(pos)
            pos += 1
        return positions
    
    def _verify_parquet(self, data: bytes) -> bool:
        """Verify data is valid Parquet"""
        try:
            import io
            pd.read_parquet(io.BytesIO(data))
            return True
        except:
            return False
    
    def _log(self, message: str):
        """Log recovery operation"""
        self.recovery_log.append(message)
        if self.verbose:
            print(f"  {message}")
    
    @classmethod
    def recover_directory(cls, directory: Union[str, Path], output_directory: Union[str, Path], pattern: str = "*.parquet") -> int:
        """Recover all corrupted Parquet files in a directory"""
        directory = Path(directory)
        output_directory = Path(output_directory)
        output_directory.mkdir(parents=True, exist_ok=True)
        
        recovery = cls(verbose=True)
        files = sorted(directory.glob(pattern))
        
        print(f"Found {len(files)} file(s)\n")
        
        success = 0
        for file in files:
            try:
                output_path = output_directory / file.name
                recovery.recover_file(file, output_path)
                success += 1
            except Exception as e:
                print(f"✗ {file.name}: {e}")
        
        print(f"\n{'='*60}")
        print(f"Successfully recovered: {success}/{len(files)} files")
        print(f"{'='*60}")
        
        return success
