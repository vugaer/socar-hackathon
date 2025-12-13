"""Forensics Tools - Hidden Data Extraction"""

import re
from pathlib import Path
from typing import Union, List, Dict


class ForensicsTools:
    """Tools for extracting hidden data and flags"""
    
    FLAG_PATTERNS = [
        rb'FLAG\{[A-Z0-9_]+\}',
        rb'flag\{[a-z0-9_]+\}',
        rb'CTF\{[^\}]+\}',
        rb'CPETRO\{[^\}]+\}',
    ]
    
    def __init__(self):
        self.findings = []
    
    def extract_flags(self, filepath: Union[str, Path]) -> List[str]:
        """Extract hidden flags from a file"""
        filepath = Path(filepath)
        
        with open(filepath, 'rb') as f:
            data = f.read()
        
        flags = []
        
        for pattern in self.FLAG_PATTERNS:
            match = re.search(pattern, data)
            if match:
                try:
                    flag_str = match.group(0).decode('ascii', errors='ignore')
                    if flag_str not in flags:
                        flags.append(flag_str)
                        self.findings.append({
                            'file': filepath.name,
                            'flag': flag_str,
                            'offset': data.find(match.group(0)),
                        })
                except:
                    pass
        
        return flags
    
    def extract_flags_from_directory(self, directory: Union[str, Path], pattern: str = "*.parquet") -> Dict[str, List[str]]:
        """Extract flags from all files in a directory"""
        directory = Path(directory)
        results = {}
        
        for file in directory.glob(pattern):
            flags = self.extract_flags(file)
            if flags:
                results[file.name] = flags
        
        return results
