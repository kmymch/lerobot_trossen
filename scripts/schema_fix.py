#!/usr/bin/env python3
"""
Fix schema order inconsistencies in meta/episodes and create a new dataset.

This script:
1. Detects schema inconsistencies in meta/episodes parquet files
2. Reorders columns to match the first episode's schema
3. Creates a new dataset repository with the fixed schema
"""

import sys
import shutil
from pathlib import Path
from datetime import datetime

import pandas as pd
import pyarrow.parquet as pq
from tqdm import tqdm

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.utils import init_logging


class EpisodesSchemaFixer:
    """Fix and create a new dataset with consistent episode schemas."""
    
    def __init__(self, repo_id: str, new_repo_id: str = None):
        self.repo_id = repo_id
        self.dataset = LeRobotDataset(repo_id)
        self.root = self.dataset.root
        self.episodes_dir = self.root / "meta" / "episodes"
        
        # Generate new repo_id if not provided
        if new_repo_id is None:
            self.new_repo_id = f"{repo_id}-schema-fixed"
        else:
            self.new_repo_id = new_repo_id
    
    def get_parquet_schema(self, parquet_file: Path) -> list:
        """Get column names from parquet file in order."""
        pf = pq.ParquetFile(parquet_file)
        schema = pf.schema_arrow
        return [field.name for field in schema]
    
    def detect_inconsistencies(self) -> dict:
        """Detect schema inconsistencies and return report."""
        parquet_files = sorted(self.episodes_dir.glob("chunk-*/file-*.parquet"))
        
        schemas = {}
        inconsistencies = {}
        first_schema = None
        
        print(f"Checking schema consistency for {len(parquet_files)} files...")
        
        for parquet_file in tqdm(parquet_files):
            try:
                schema = self.get_parquet_schema(parquet_file)
                file_key = str(parquet_file.relative_to(self.episodes_dir))
                schemas[file_key] = schema
                
                if first_schema is None:
                    first_schema = schema
                elif schema != first_schema:
                    inconsistencies[file_key] = {
                        'expected_count': len(first_schema),
                        'actual_count': len(schema),
                        'columns_match': set(first_schema) == set(schema)
                    }
            except Exception as e:
                print(f"Error reading {parquet_file}: {e}")
        
        return {
            'first_schema': first_schema,
            'all_schemas': schemas,
            'inconsistencies': inconsistencies,
            'has_issues': len(inconsistencies) > 0
        }
    
    def fix_and_copy_dataset(self, output_root: Path = None) -> Path:
        """
        Fix schema inconsistencies and copy to new location.
        
        Args:
            output_root: Root directory for new dataset (default: original location)
        
        Returns:
            Path to the new dataset root
        """
        # Detect issues
        consistency_info = self.detect_inconsistencies()
        target_schema = consistency_info['first_schema']
        
        if consistency_info['has_issues']:
            print(f"\n⚠ Found {len(consistency_info['inconsistencies'])} files with schema inconsistencies")
            print("These files will be reordered to match the first episode's schema")
        else:
            print("\n✓ All schemas are already consistent!")
        
        # Determine output location
        if output_root is None:
            output_root = self.root.parent
        
        new_dataset_root = output_root / self.new_repo_id
        
        print(f"\nCopying dataset to: {new_dataset_root}")
        
        # Copy entire dataset structure
        if new_dataset_root.exists():
            print(f"Removing existing directory: {new_dataset_root}")
            shutil.rmtree(new_dataset_root)
        
        # Copy all files
        shutil.copytree(self.root, new_dataset_root)
        
        # Fix episode parquet files
        new_episodes_dir = new_dataset_root / "meta" / "episodes"
        parquet_files = sorted(new_episodes_dir.glob("chunk-*/file-*.parquet"))
        
        print(f"\nFixing schema in {len(parquet_files)} episode files...")
        
        for parquet_file in tqdm(parquet_files):
            try:
                df = pd.read_parquet(parquet_file)
                current_schema = list(df.columns)
                
                if current_schema != target_schema:
                    # Check if all columns exist
                    missing_cols = set(target_schema) - set(df.columns)
                    extra_cols = set(df.columns) - set(target_schema)
                    
                    if missing_cols:
                        print(f"  ⚠ {parquet_file.name}: Missing {missing_cols}")
                    if extra_cols:
                        print(f"  ⚠ {parquet_file.name}: Extra {extra_cols}")
                    
                    # Reorder to match target schema
                    if not missing_cols:
                        df = df[target_schema]
                        df.to_parquet(parquet_file, index=False)
                
            except Exception as e:
                print(f"Error processing {parquet_file}: {e}")
        
        print("✓ Schema fixed and dataset copied!")
        return new_dataset_root
    
    def generate_report(self) -> str:
        """Generate detailed inconsistency report."""
        consistency_info = self.detect_inconsistencies()
        
        report = f"Schema Consistency Report\n"
        report += f"{'=' * 80}\n"
        report += f"Original Repository: {self.repo_id}\n"
        report += f"New Repository: {self.new_repo_id}\n"
        report += f"Timestamp: {datetime.now()}\n\n"
        
        if not consistency_info['has_issues']:
            report += "✓ All schemas are consistent!\n"
            return report
        
        report += f"⚠ Found {len(consistency_info['inconsistencies'])} files with inconsistencies\n\n"
        
        report += "First schema (reference):\n"
        for i, col in enumerate(consistency_info['first_schema']):
            report += f"  {i:3d}: {col}\n"
        
        report += f"\n{'=' * 80}\n"
        report += "Files with inconsistent schema:\n\n"
        
        for file_key, info in consistency_info['inconsistencies'].items():
            report += f"{file_key}\n"
            report += f"  - Expected columns: {info['expected_count']}\n"
            report += f"  - Actual columns: {info['actual_count']}\n"
            report += f"  - Same column set: {info['columns_match']}\n\n"
        
        return report
    
    def push_to_hub(self, new_dataset_root: Path) -> None:
        """Push the fixed dataset to Hugging Face Hub."""
        try:
            print(f"\nPushing {self.new_repo_id} to Hugging Face Hub...")
            dataset = LeRobotDataset(self.new_repo_id, root=new_dataset_root)
            dataset.push_to_hub()
            print("✓ Successfully pushed to Hub!")
        except Exception as e:
            print(f"Error pushing to Hub: {e}")
            print("You can manually push using the LeRobot CLI")


if __name__ == "__main__":
    init_logging()
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Error: Dataset repository ID is required")
        print("Usage: python schema_fix.py <repo_id> [options]")
        print("\nOptions:")
        print("  --report    : Generate detailed report without fixing")
        print("  --fix-only  : Fix inconsistencies locally (do not push)")
        print("  --new-id <id>: Custom new repository ID")
        print("\nDefault: Fix and push to Hugging Face Hub")
        sys.exit(1)
    
    repo_id = sys.argv[1]
    
    # Validate repo_id format
    if "/" not in repo_id:
        print("Error: Invalid repository ID format")
        print("Expected format: <username>/<datasetname>")
        print(f"Got: {repo_id}")
        sys.exit(1)
    
    new_repo_id = None
    report_only = "--report" in sys.argv
    fix_only = "--fix-only" in sys.argv
    push_to_hub = not (report_only or fix_only)  # Default is True
    
    # Check for custom new-id
    if "--new-id" in sys.argv:
        idx = sys.argv.index("--new-id")
        if idx + 1 < len(sys.argv):
            new_repo_id = sys.argv[idx + 1]
    
    fixer = EpisodesSchemaFixer(repo_id, new_repo_id)
    
    if report_only:
        # Just generate report
        report = fixer.generate_report()
        print(report)
        
        # Save report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = Path(__file__).parent / f"schema_report_{repo_id.replace('/', '_')}_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report)
        print(f"\nReport saved to: {report_file}")
    
    elif fix_only:
        # Fix locally only
        new_root = fixer.fix_and_copy_dataset()
        print(f"\n✓ Fixed dataset at: {new_root}")
    
    else:
        # Default: Fix and push to Hub
        new_root = fixer.fix_and_copy_dataset()
        fixer.push_to_hub(new_root)
