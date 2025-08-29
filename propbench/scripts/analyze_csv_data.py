import pandas as pd
import json
import os
from pathlib import Path

def analyze_csv_structure():
    """Analyze the CSV files to understand the data structure for import mapping."""
    
    data_dir = Path("c:/src/propBench/data/16757_examples")
    
    files = {
        'properties': 'EN_ISO16757_sheet22_HeatPumps-Mono-properties.csv',
        'values': 'EN_ISO16757_sheet22_HeatPumps-Mono-values.csv', 
        'classes': 'EN_ISO16757_sheet22_HeatPumps-Mono-class.csv'
    }
    
    analysis = {}
    
    for file_type, filename in files.items():
        filepath = data_dir / filename
        if filepath.exists():
            try:
                df = pd.read_csv(filepath, encoding='utf-8')
                analysis[file_type] = {
                    'filename': filename,
                    'shape': df.shape,
                    'columns': df.columns.tolist(),
                    'first_row': df.iloc[0].to_dict() if len(df) > 0 else {},
                    'second_row': df.iloc[1].to_dict() if len(df) > 1 else {},
                    'sample_data': df.head(3).to_dict('records')
                }
                print(f"\n=== {file_type.upper()} FILE ANALYSIS ===")
                print(f"File: {filename}")
                print(f"Shape: {df.shape}")
                print(f"Columns: {df.columns.tolist()}")
                print("\nFirst few rows:")
                print(df.head(3))
                
            except Exception as e:
                print(f"Error reading {filename}: {e}")
                analysis[file_type] = {'error': str(e)}
    
    # Save analysis to JSON for reference
    output_file = Path("c:/src/propBench/data/csv_analysis.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(analysis, f, indent=2, default=str)
    
    print(f"\nAnalysis saved to: {output_file}")
    return analysis

if __name__ == "__main__":
    analyze_csv_structure()