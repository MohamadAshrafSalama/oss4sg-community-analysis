#!/usr/bin/env python3
"""
Code Metrics Analyzer

This script analyzes source code repositories to extract comprehensive metrics including:
- Lines of code (total, comment, non-comment)
- Character counts (total, code, comment)
- Repository size and README analysis
- Language-specific comment detection

Supports a wide range of programming languages and handles various comment styles.

Usage:
    python code_metrics_analyzer.py <input_directory> <output_csv>
    
Example:
    python code_metrics_analyzer.py /path/to/repositories output_metrics.csv
"""

import os
import csv
import json
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# =============================================================================
# LANGUAGE CONFIGURATION
# =============================================================================

# Comprehensive mapping of file extensions to comment styles
COMMENT_STYLE_MAP = {
    # Hash-style single line comments (#)
    '.py': 'hash',      # Python
    '.sh': 'hash',      # Shell/Bash
    '.bash': 'hash',    # Bash
    '.zsh': 'hash',     # Zsh
    '.fish': 'hash',    # Fish shell
    '.rb': 'hash',      # Ruby
    '.r': 'hash',       # R
    '.R': 'hash',       # R (capital)
    '.pl': 'hash',      # Perl
    '.pm': 'hash',      # Perl module
    '.yaml': 'hash',    # YAML
    '.yml': 'hash',     # YAML
    '.toml': 'hash',    # TOML
    '.ini': 'hash',     # INI files
    '.cfg': 'hash',     # Config files
    '.conf': 'hash',    # Config files
    '.properties': 'hash', # Properties files
    '.gitignore': 'hash',  # Git ignore
    '.dockerignore': 'hash', # Docker ignore
    
    # Slash-star style (// single line, /* */ block comments)
    '.js': 'slash_star',   # JavaScript
    '.jsx': 'slash_star',  # React JSX
    '.ts': 'slash_star',   # TypeScript
    '.tsx': 'slash_star',  # TypeScript JSX
    '.c': 'slash_star',    # C
    '.cpp': 'slash_star',  # C++
    '.cxx': 'slash_star',  # C++
    '.cc': 'slash_star',   # C++
    '.c++': 'slash_star',  # C++
    '.h': 'slash_star',    # C/C++ header
    '.hpp': 'slash_star',  # C++ header
    '.hxx': 'slash_star',  # C++ header
    '.h++': 'slash_star',  # C++ header
    '.java': 'slash_star', # Java
    '.scala': 'slash_star', # Scala
    '.kt': 'slash_star',   # Kotlin
    '.kts': 'slash_star',  # Kotlin script
    '.go': 'slash_star',   # Go
    '.rs': 'slash_star',   # Rust
    '.swift': 'slash_star', # Swift
    '.dart': 'slash_star', # Dart
    '.php': 'slash_star',  # PHP (also supports #, but keeping simple)
    '.cs': 'slash_star',   # C#
    '.fs': 'slash_star',   # F#
    '.m': 'slash_star',    # Objective-C
    '.mm': 'slash_star',   # Objective-C++
    '.groovy': 'slash_star', # Groovy
    '.gradle': 'slash_star', # Gradle
    '.ino': 'slash_star',  # Arduino
    '.pde': 'slash_star',  # Processing
    '.glsl': 'slash_star', # GLSL
    '.hlsl': 'slash_star', # HLSL
    '.metal': 'slash_star', # Metal
    '.jsonc': 'slash_star', # JSON with comments
    
    # CSS style (/* */ block comments only)
    '.css': 'css_style',
    '.scss': 'css_style',  # Sass
    '.sass': 'css_style',  # Sass
    '.less': 'css_style',  # Less
    '.styl': 'css_style',  # Stylus
    
    # HTML/XML style (<!-- --> comments)
    '.html': 'html_style',
    '.htm': 'html_style',
    '.xml': 'html_style',
    '.svg': 'html_style',
    '.vue': 'html_style',  # Vue.js (simplified - ignores embedded JS/CSS)
    '.xhtml': 'html_style',
    '.rss': 'html_style',
    '.atom': 'html_style',
    
    # SQL style (-- single line, /* */ block comments)
    '.sql': 'sql_style',
    '.mysql': 'sql_style',
    '.pgsql': 'sql_style',
    '.sqlite': 'sql_style',
    
    # LaTeX style (% comments)
    '.tex': 'latex_style',
    '.latex': 'latex_style',
    '.ltx': 'latex_style',
    
    # MATLAB style (% comments)
    '.m': 'matlab_style',  # Note: conflicts with Objective-C, context matters
    
    # Assembly style (; comments)
    '.asm': 'assembly_style',
    '.s': 'assembly_style',
    '.S': 'assembly_style',
    
    # Haskell style (-- single line, {- -} block comments)
    '.hs': 'haskell_style',
    '.lhs': 'haskell_style',
    
    # Lua style (-- single line, --[[ ]] block comments)
    '.lua': 'lua_style',
    
    # Lisp family (; comments)
    '.lisp': 'lisp_style',
    '.cl': 'lisp_style',
    '.el': 'lisp_style',    # Emacs Lisp
    '.scm': 'lisp_style',   # Scheme
    '.clj': 'lisp_style',   # Clojure
    '.cljs': 'lisp_style',  # ClojureScript
    
    # Special cases
    '.ipynb': 'jupyter_notebook',  # Jupyter Notebook
    '.json': 'no_comments',        # JSON (no comments allowed)
    '.md': 'markdown',             # Markdown
    '.rst': 'restructured_text',   # reStructuredText
    '.txt': 'plain_text',          # Plain text
}

# =============================================================================
# COMMENT DETECTION FUNCTIONS
# =============================================================================

def detect_comment_line(line: str, style: str, in_block_comment: bool) -> Tuple[bool, bool, int]:
    """
    Analyze a line to determine if it's a comment and count comment characters.
    
    Args:
        line: The line of text to analyze
        style: The comment style for this file type
        in_block_comment: Whether we're currently inside a block comment
        
    Returns:
        Tuple of (is_comment_line, new_in_block_comment, comment_character_count)
    """
    stripped = line.lstrip()
    comment_chars = 0
    
    # Handle special cases first
    if style == 'no_comments':
        return False, False, 0
    elif style == 'jupyter_notebook':
        # For Jupyter notebooks, we'd need to parse JSON - keeping simple for now
        return False, False, 0
    elif style in ['markdown', 'restructured_text', 'plain_text']:
        # These are documentation formats - treat entire content as "code"
        return False, False, 0
    
    # Handle block comment continuation
    if style == 'slash_star' and in_block_comment:
        comment_chars = len(line)
        if '*/' in line:
            in_block_comment = False
        return True, in_block_comment, comment_chars
    elif style == 'css_style' and in_block_comment:
        comment_chars = len(line)
        if '*/' in line:
            in_block_comment = False
        return True, in_block_comment, comment_chars
    elif style == 'html_style' and in_block_comment:
        comment_chars = len(line)
        if '-->' in line:
            in_block_comment = False
        return True, in_block_comment, comment_chars
    elif style == 'sql_style' and in_block_comment:
        comment_chars = len(line)
        if '*/' in line:
            in_block_comment = False
        return True, in_block_comment, comment_chars
    elif style == 'haskell_style' and in_block_comment:
        comment_chars = len(line)
        if '-}' in line:
            in_block_comment = False
        return True, in_block_comment, comment_chars
    elif style == 'lua_style' and in_block_comment:
        comment_chars = len(line)
        if ']]' in line:
            in_block_comment = False
        return True, in_block_comment, comment_chars
    
    # Handle single-line comments and block comment starts
    if style == 'hash':
        if stripped.startswith('#'):
            return True, False, len(line)
    elif style == 'slash_star':
        if stripped.startswith('//'):
            return True, False, len(line)
        elif '/*' in line:
            in_block_comment = True
            comment_chars = len(line) - line.find('/*')
            return True, in_block_comment, comment_chars
    elif style == 'css_style':
        if '/*' in line:
            in_block_comment = True
            comment_chars = len(line) - line.find('/*')
            return True, in_block_comment, comment_chars
    elif style == 'html_style':
        if '<!--' in line:
            in_block_comment = True
            comment_chars = len(line) - line.find('<!--')
            return True, in_block_comment, comment_chars
    elif style == 'sql_style':
        if stripped.startswith('--'):
            return True, False, len(line)
        elif '/*' in line:
            in_block_comment = True
            comment_chars = len(line) - line.find('/*')
            return True, in_block_comment, comment_chars
    elif style in ['latex_style', 'matlab_style']:
        if stripped.startswith('%'):
            return True, False, len(line)
    elif style == 'assembly_style':
        if stripped.startswith(';'):
            return True, False, len(line)
    elif style == 'haskell_style':
        if stripped.startswith('--'):
            return True, False, len(line)
        elif '{-' in line:
            in_block_comment = True
            comment_chars = len(line) - line.find('{-')
            return True, in_block_comment, comment_chars
    elif style == 'lua_style':
        if stripped.startswith('--'):
            if '--[[' in line:
                in_block_comment = True
                comment_chars = len(line) - line.find('--[[')
                return True, in_block_comment, comment_chars
            else:
                return True, False, len(line)
    elif style == 'lisp_style':
        if stripped.startswith(';'):
            return True, False, len(line)
    
    return False, in_block_comment, 0

# =============================================================================
# FILE PROCESSING FUNCTIONS
# =============================================================================

def analyze_file(filepath: Path) -> Dict:
    """
    Analyze a single file and return metrics.
    
    Args:
        filepath: Path to the file to analyze
        
    Returns:
        Dictionary containing file metrics
    """
    total_lines = 0
    total_chars = 0
    comment_lines = 0
    code_chars = 0
    comment_chars = 0
    
    # Determine file type and comment style
    ext = filepath.suffix.lower()
    style = COMMENT_STYLE_MAP.get(ext, 'unknown')
    
    if style == 'unknown':
        # For unknown file types, treat everything as code
        style = 'no_comments'
    
    in_block_comment = False
    
    try:
        # Try different encodings
        for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
            try:
                with open(filepath, 'r', encoding=encoding, errors='ignore') as f:
                    for line in f:
                        total_lines += 1
                        line_len = len(line)
                        total_chars += line_len
                        
                        is_comment, new_in_block, comment_len = detect_comment_line(
                            line, style, in_block_comment
                        )
                        in_block_comment = new_in_block
                        
                        if is_comment:
                            comment_lines += 1
                            comment_chars += comment_len
                        else:
                            code_chars += line_len
                break  # Successfully read file, exit encoding loop
            except UnicodeDecodeError:
                continue  # Try next encoding
        else:
            # If all encodings failed, treat as binary and skip detailed analysis
            with open(filepath, 'rb') as f:
                total_chars = len(f.read())
                total_lines = 1  # Treat as single "line" of binary data
                code_chars = total_chars
                
    except Exception as e:
        print(f"Error processing file {filepath}: {e}", file=sys.stderr)
        return {
            "lines": 0, "chars": 0, "comment_lines": 0, 
            "non_comment_lines": 0, "code_chars": 0, "comment_chars": 0
        }
    
    non_comment_lines = total_lines - comment_lines
    
    return {
        "lines": total_lines,
        "chars": total_chars,
        "comment_lines": comment_lines,
        "non_comment_lines": non_comment_lines,
        "code_chars": code_chars,
        "comment_chars": comment_chars
    }

def find_readme_file(repo_path: Path) -> Optional[Path]:
    """
    Find a README file in the repository root.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Path to README file if found, None otherwise
    """
    readme_candidates = [
        "README", "README.md", "readme", "readme.md", "README.rst", 
        "readme.rst", "README.txt", "readme.txt", "README.MD", 
        "Readme.md", "ReadMe.md", "README.adoc", "README.asciidoc"
    ]
    
    for candidate in readme_candidates:
        readme_path = repo_path / candidate
        if readme_path.is_file():
            return readme_path
    
    return None

def analyze_repository(repo_path: Path) -> Dict:
    """
    Analyze an entire repository and compute comprehensive metrics.
    
    Args:
        repo_path: Path to the repository
        
    Returns:
        Dictionary containing repository metrics
    """
    repo_metrics = {
        "lines": 0, "chars": 0, "comment_lines": 0, "non_comment_lines": 0,
        "code_chars": 0, "comment_chars": 0, "repo_size": 0, "readme_chars": 0
    }
    
    # Find and analyze README file
    readme_path = find_readme_file(repo_path)
    if readme_path:
        try:
            for encoding in ['utf-8', 'utf-8-sig', 'latin1', 'cp1252']:
                try:
                    with open(readme_path, 'r', encoding=encoding, errors='ignore') as f:
                        content = f.read()
                        repo_metrics["readme_chars"] = len(content)
                    break
                except UnicodeDecodeError:
                    continue
        except Exception as e:
            print(f"Error reading README {readme_path}: {e}", file=sys.stderr)
    
    # Walk through all files in the repository
    for file_path in repo_path.rglob('*'):
        if file_path.is_file():
            # Add to total repository size
            try:
                repo_metrics["repo_size"] += file_path.stat().st_size
            except OSError:
                pass
            
            # Analyze source code files
            file_metrics = analyze_file(file_path)
            for key in ["lines", "chars", "comment_lines", "non_comment_lines", "code_chars", "comment_chars"]:
                repo_metrics[key] += file_metrics[key]
    
    # Convert repository size to MB
    repo_metrics["repo_size_mb"] = repo_metrics["repo_size"] / (1024 * 1024)
    
    # Calculate ratios
    if repo_metrics["comment_lines"] > 0:
        repo_metrics["ratio_code_to_comments"] = repo_metrics["non_comment_lines"] / repo_metrics["comment_lines"]
    else:
        repo_metrics["ratio_code_to_comments"] = float('inf') if repo_metrics["non_comment_lines"] > 0 else 0
    
    if repo_metrics["comment_chars"] > 0:
        repo_metrics["ratio_code_chars_to_comment_chars"] = repo_metrics["code_chars"] / repo_metrics["comment_chars"]
    else:
        repo_metrics["ratio_code_chars_to_comment_chars"] = float('inf') if repo_metrics["code_chars"] > 0 else 0
    
    return repo_metrics

# =============================================================================
# MAIN PROCESSING FUNCTIONS
# =============================================================================

def process_repositories(input_directory: Path, output_csv: Path):
    """
    Process all repositories in the input directory and save metrics to CSV.
    
    Args:
        input_directory: Directory containing repositories (each subdirectory is a repo)
        output_csv: Output CSV file path
    """
    fieldnames = [
        "name", "lines_of_code", "characters", "comment_lines", "non_comment_lines",
        "ratio_code_to_comments", "code_characters", "comment_characters",
        "ratio_code_chars_to_comment_chars", "repo_size_mb", "full_repo_size_mb",
        "readme_characters"
    ]
    
    with open(output_csv, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        
        # Process each repository directory
        for repo_dir in input_directory.iterdir():
            if repo_dir.is_dir() and not repo_dir.name.startswith('.'):
                print(f"Processing repository: {repo_dir.name}")
                
                try:
                    metrics = analyze_repository(repo_dir)
                    
                    # Convert repository name from folder format to owner/repo format if needed
                    repo_name = repo_dir.name
                    if "_" in repo_name:
                        # Assume format is "owner_repo"
                        owner, repo = repo_name.split("_", 1)
                        repo_name = f"{owner}/{repo}"
                    
                    row = {
                        "name": repo_name,
                        "lines_of_code": metrics["lines"],
                        "characters": metrics["chars"],
                        "comment_lines": metrics["comment_lines"],
                        "non_comment_lines": metrics["non_comment_lines"],
                        "ratio_code_to_comments": round(metrics["ratio_code_to_comments"], 3) if metrics["ratio_code_to_comments"] != float('inf') else 'inf',
                        "code_characters": metrics["code_chars"],
                        "comment_characters": metrics["comment_chars"],
                        "ratio_code_chars_to_comment_chars": round(metrics["ratio_code_chars_to_comment_chars"], 3) if metrics["ratio_code_chars_to_comment_chars"] != float('inf') else 'inf',
                        "repo_size_mb": round(metrics["repo_size_mb"], 3),
                        "full_repo_size_mb": round(metrics["repo_size_mb"], 3),  # Same as repo_size_mb for consistency
                        "readme_characters": metrics["readme_chars"]
                    }
                    
                    writer.writerow(row)
                    
                except Exception as e:
                    print(f"Error processing repository {repo_dir.name}: {e}", file=sys.stderr)
                    continue

def main():
    """Main function to handle command line arguments and process repositories."""
    parser = argparse.ArgumentParser(
        description='Analyze code metrics for repositories',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s /path/to/repositories output_metrics.csv
  %(prog)s --help
        """
    )
    
    parser.add_argument(
        'input_directory',
        type=Path,
        help='Directory containing repositories to analyze'
    )
    
    parser.add_argument(
        'output_csv',
        type=Path,
        help='Output CSV file for metrics'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose output'
    )
    
    args = parser.parse_args()
    
    # Validate input directory
    if not args.input_directory.exists():
        print(f"Error: Input directory '{args.input_directory}' does not exist.", file=sys.stderr)
        sys.exit(1)
    
    if not args.input_directory.is_dir():
        print(f"Error: '{args.input_directory}' is not a directory.", file=sys.stderr)
        sys.exit(1)
    
    # Create output directory if it doesn't exist
    args.output_csv.parent.mkdir(parents=True, exist_ok=True)
    
    print(f"Analyzing repositories in: {args.input_directory}")
    print(f"Output will be saved to: {args.output_csv}")
    print(f"Supported file extensions: {len(COMMENT_STYLE_MAP)} types")
    
    try:
        process_repositories(args.input_directory, args.output_csv)
        print("\n✅ Analysis completed successfully!")
        print(f"Results saved to: {args.output_csv}")
    except Exception as e:
        print(f"\n❌ Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main() 