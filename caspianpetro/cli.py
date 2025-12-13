"""Command-Line Interface for CaspianPetro"""

import argparse
import sys
from pathlib import Path
from caspianpetro.sgx_parser import SGXParser
from caspianpetro.parquet_recovery import ParquetRecovery
from caspianpetro.forensics import ForensicsTools


def main():
    parser = argparse.ArgumentParser(description='CaspianPetro - Legacy Seismic Data Tools')
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Parse SGX
    sgx_parser = subparsers.add_parser('parse-sgx', help='Parse .sgx files')
    sgx_parser.add_argument('input', help='Input .sgx file or directory')
    sgx_parser.add_argument('-o', '--output', help='Output Parquet file')
    
    # Recover Parquet
    recover_parser = subparsers.add_parser('recover', help='Recover corrupted Parquet')
    recover_parser.add_argument('input', help='Input file or directory')
    recover_parser.add_argument('-o', '--output', required=True, help='Output path')
    
    # Extract flags
    flags_parser = subparsers.add_parser('extract-flags', help='Extract hidden flags')
    flags_parser.add_argument('input', help='Input file or directory')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    try:
        if args.command == 'parse-sgx':
            input_path = Path(args.input)
            
            if input_path.is_dir():
                df = SGXParser.parse_directory(input_path, combine=True)
            else:
                p = SGXParser()
                df = p.parse_file(input_path)
            
            if args.output:
                df.to_parquet(args.output, index=False)
                print(f"\n✓ Saved to: {args.output}")
            else:
                print(df)
        
        elif args.command == 'recover':
            input_path = Path(args.input)
            output_path = Path(args.output)
            
            if input_path.is_dir():
                ParquetRecovery.recover_directory(input_path, output_path)
            else:
                recovery = ParquetRecovery()
                df = recovery.recover_file(input_path, output_path)
                print(f"\n✓ Recovered {len(df)} rows")
        
        elif args.command == 'extract-flags':
            forensics = ForensicsTools()
            input_path = Path(args.input)
            
            if input_path.is_dir():
                results = forensics.extract_flags_from_directory(input_path)
                for filename, flags in results.items():
                    print(f"{filename}: {flags}")
            else:
                flags = forensics.extract_flags(input_path)
                for flag in flags:
                    print(flag)
    
    except Exception as e:
        print(f"✗ Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
