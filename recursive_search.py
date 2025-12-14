#!/usr/bin/env python3
import os

def collect_all_files(directory, output_file):
    """
    Recursively collect ALL files into a single text file.
    
    Args:
        directory: Root directory to start searching
        output_file: Output text file path
    """
    with open(output_file, 'w', encoding='utf-8', errors='ignore') as outfile:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                filepath = os.path.join(root, filename)
                
                # Write separator and file path
                outfile.write(f"\n{'='*80}\n")
                outfile.write(f"FILE: {filepath}\n")
                outfile.write(f"{'='*80}\n\n")
                
                try:
                    with open(filepath, 'r', encoding='utf-8', errors='ignore') as infile:
                        outfile.write(infile.read())
                        outfile.write('\n')
                except Exception as e:
                    outfile.write(f"Error reading file: {e}\n")

# Usage
if __name__ == "__main__":
    collect_all_files('.', 'all_contents.txt')
    print("All files collected into all_contents.txt")

