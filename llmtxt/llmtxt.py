import os
import sqlite3
from typing import List, Dict, Any
import json

DB_PATH = os.path.join("database", "chinook.db")
OUTPUT_FILE = os.path.join("llmtxt", "database_llm.txt")

def get_table_schema(cursor: sqlite3.Cursor, table_name: str) -> Dict[str, Any]:
    """Get detailed schema information for a table."""
 
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = cursor.fetchall()
    

    cursor.execute(f"PRAGMA foreign_key_list({table_name})")
    foreign_keys = cursor.fetchall()
    
 
    cursor.execute(f"PRAGMA index_list({table_name})")
    indexes = cursor.fetchall()
    
 
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 3")
    sample_data = cursor.fetchall()
    
 
    cursor.execute(f"SELECT * FROM {table_name} LIMIT 0")
    column_names = [description[0] for description in cursor.description]
    
    return {
        "table_name": table_name,
        "columns": [
            {
                "name": col[1],
                "type": col[2],
                "not_null": bool(col[3]),
                "default_value": col[4],
                "primary_key": bool(col[5])
            }
            for col in columns
        ],
        "foreign_keys": [
            {
                "from_column": fk[3],
                "to_table": fk[2],
                "to_column": fk[4]
            }
            for fk in foreign_keys
        ],
        "indexes": [idx[1] for idx in indexes if not idx[1].startswith('sqlite_')],
        "sample_data": [
            dict(zip(column_names, row))
            for row in sample_data
        ],
        "row_count": get_row_count(cursor, table_name)
    }

def get_row_count(cursor: sqlite3.Cursor, table_name: str) -> int:
    """Get the number of rows in a table."""
    cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
    return cursor.fetchone()[0]

def format_schema_for_llm(schema: Dict[str, Any]) -> str:
    """Format the schema information in a clear, LLM-friendly way."""
    output = []
    
 
    output.append(f"## Table: {schema['table_name']}")
    output.append(f"**Row count:** {schema['row_count']:,}")
    output.append("")
    
 
    output.append("### Columns:")
    for col in schema['columns']:
        col_info = f"- **{col['name']}** ({col['type']})"
        if col['primary_key']:
            col_info += " [PRIMARY KEY]"
        if col['not_null']:
            col_info += " [NOT NULL]"
        if col['default_value'] is not None:
            col_info += f" [DEFAULT: {col['default_value']}]"
        output.append(col_info)
    output.append("")
    
 
    if schema['foreign_keys']:
        output.append("### Foreign Keys:")
        for fk in schema['foreign_keys']:
            output.append(f"- {fk['from_column']} → {fk['to_table']}.{fk['to_column']}")
        output.append("")
    
 
    if schema['indexes']:
        output.append("### Indexes:")
        for idx in schema['indexes']:
            output.append(f"- {idx}")
        output.append("")
    
 
    if schema['sample_data']:
        output.append("### Sample Data:")
        for i, row in enumerate(schema['sample_data'], 1):
            output.append(f"**Row {i}:**")
            for key, value in row.items():
 
                if isinstance(value, str) and len(str(value)) > 100:
                    value = str(value)[:100] + "..."
                output.append(f"  {key}: {value}")
            output.append("")
    
    return "\n".join(output)

def generate_llm_text():
    """Generate the complete LLM text file from the database."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
 
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
                
    llm_text = []
    llm_text.append("# Database Schema Documentation")
    llm_text.append("")
    llm_text.append("This document provides a comprehensive overview of the database structure, including table schemas, relationships, and sample data.")
    llm_text.append("")
    llm_text.append(f"**Database:** {os.path.basename(DB_PATH)}")
    llm_text.append(f"**Total Tables:** {len(tables)}")
    llm_text.append("")
    
    # Add table overview
    llm_text.append("## Table Overview")
    for table in tables:
        row_count = get_row_count(cursor, table)
        llm_text.append(f"- **{table}**: {row_count:,} rows")
    llm_text.append("")
    
    # Add detailed schema for each table
    llm_text.append("## Detailed Table Schemas")
    llm_text.append("")
    
    for table in tables:
        schema = get_table_schema(cursor, table)
        llm_text.append(format_schema_for_llm(schema))
        llm_text.append("---")
        llm_text.append("")
    
    # Add relationships summary
    llm_text.append("## Database Relationships Summary")
    llm_text.append("")
    
    all_relationships = []
    for table in tables:
        schema = get_table_schema(cursor, table)
        for fk in schema['foreign_keys']:
            all_relationships.append({
                'from_table': table,
                'from_column': fk['from_column'],
                'to_table': fk['to_table'],
                'to_column': fk['to_column']
            })
    
    if all_relationships:
        llm_text.append("### Foreign Key Relationships:")
        for rel in all_relationships:
            llm_text.append(f"- **{rel['from_table']}.{rel['from_column']}** → **{rel['to_table']}.{rel['to_column']}**")
    else:
        llm_text.append("No foreign key relationships found in this database.")
    
    llm_text.append("")
    llm_text.append("---")
    llm_text.append("*This document was programmatically generated from the database schema.*")
    
    # Write to file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(llm_text))
    
    print(f"LLM text file generated successfully: {OUTPUT_FILE}")
    print(f"File size: {os.path.getsize(OUTPUT_FILE):,} bytes")
    
    conn.close()

if __name__ == "__main__":
    generate_llm_text() 