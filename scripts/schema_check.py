#!/usr/bin/env python3
"""Check the schema of meta/episodes parquet files in a lerobot dataset."""

import sys
from pathlib import Path
from datetime import datetime

import pyarrow.parquet as pq

from lerobot.datasets.lerobot_dataset import LeRobotDataset
from lerobot.utils.utils import init_logging


class FileAndConsoleLogger:
    """Logger that writes to both file and console."""
    
    def __init__(self, file_path: Path):
        self.file_path = file_path
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self.file = open(self.file_path, 'w', encoding='utf-8')
        
    def log(self, message: str = ""):
        """Log to both file and console."""
        print(message)
        self.file.write(message + '\n')
        self.file.flush()
    
    def close(self):
        """Close the file."""
        self.file.close()


def check_episodes_parquet_schema(episodes_dir: Path, logger: FileAndConsoleLogger):
    """
    Check the schema of all parquet files in meta/episodes directory.
    
    Args:
        episodes_dir: Path to the meta/episodes directory
        logger: FileAndConsoleLogger instance
    """
    parquet_files = sorted(episodes_dir.glob("**/*.parquet"))
    
    if not parquet_files:
        logger.log(f"No parquet files found in {episodes_dir}")
        return
    
    for parquet_file in parquet_files:
        logger.log(f"\nFile: {parquet_file.relative_to(episodes_dir.parent.parent)}")
        logger.log("-" * 80)
        
        try:
            pf = pq.ParquetFile(parquet_file)
            schema = pf.schema_arrow
            
            logger.log(f"Schema columns (total: {len(schema)}):")
            for i, field in enumerate(schema):
                logger.log(f"  {i:3d}: {field.name}")
            
        except Exception as e:
            logger.log(f"Error reading {parquet_file}: {e}")


if __name__ == "__main__":
    init_logging()
    
    # Parse command line arguments
    if len(sys.argv) < 2:
        print("Error: Dataset repository ID is required")
        print("Usage: python schema_check.py <repo_id>")
        sys.exit(1)
    
    repo_id = sys.argv[1]
    
    # Validate repo_id format (must contain "/" to split username and dataset)
    if "/" not in repo_id:
        print("Error: Invalid repository ID format")
        print("Expected format: <username>/<datasetname>")
        print(f"Got: {repo_id}")
        sys.exit(1)
    
    # Create output file with format: schema_username_datasetname.txt
    username, datasetname = repo_id.split("/", 1)
    output_file = Path(__file__).parent / f"schema_{username}_{datasetname}.txt"
    logger = FileAndConsoleLogger(output_file)
    
    logger.log("Meta Episodes Parquet Schema Checker")
    logger.log("=" * 80)
    logger.log(f"Repository ID: {repo_id}")
    logger.log(f"Output saved to: {output_file}\n")
    
    try:
        dataset = LeRobotDataset(repo_id)
        
        # Log basic dataset info
        logger.log(f"Dataset: {dataset.repo_id}")
        logger.log(f"Root: {dataset.root}")
        logger.log(f"Total episodes: {dataset.meta.total_episodes}")
        logger.log("")
        
        # Check episodes parquet files
        episodes_dir = dataset.root / "meta" / "episodes"
        
        if episodes_dir.exists():
            check_episodes_parquet_schema(episodes_dir, logger)
        else:
            logger.log(f"Episodes directory not found: {episodes_dir}")
    
    except Exception as e:
        logger.log(f"Error: {e}")
        logger.log(f"Make sure the repo_id is correct: {repo_id}")
    
    logger.log(f"\n✓ Analysis complete. Results saved to: {output_file}")
    logger.close()
    
    print(f"\nOutput file: {output_file}")
