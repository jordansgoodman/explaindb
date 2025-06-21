#!/usr/bin/env python3
"""
Command-line interface for the query generator with OpenAI integration.
"""

import sys
import os

# Add the parent directory to the path so we can import from genquery
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from genquery.query_generator import interactive_query_generator, process_question

def main():
    """Main CLI entry point."""
    if len(sys.argv) > 1:
        # If arguments provided, treat as a question
        question = " ".join(sys.argv[1:])
        try:
            result = process_question(question)
            
            print("="*50)
            print("RESULTS:")
            print("="*50)
            print(f"Question: {result['question']}")
            print(f"SQL Query: {result['sql_query']}")
            print(f"Rows returned: {result['row_count']}")
            print()
            print(result['formatted_results'])
            print("="*50)
            
        except Exception as e:
            print(f"Error: {e}")
            sys.exit(1)
    else:
        # Interactive mode
        interactive_query_generator()

if __name__ == "__main__":
    main() 