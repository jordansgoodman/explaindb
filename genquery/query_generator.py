import os
import sqlite3
from typing import List, Dict, Any
import json
import openai

# Paths
DB_PATH = os.path.join("database", "chinook.db")
SCHEMA_FILE_PATH = os.path.join("llmtxt", "database_llm.txt")

def get_openai_client():
    """Get OpenAI client with API key from environment."""
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        raise ValueError("OPENAI_API_KEY environment variable not set")
    
    return openai.OpenAI(api_key=api_key)

def load_schema_context(schema_file_path: str) -> str:
    """Load the database schema context from the LLM text file."""
    if not os.path.exists(schema_file_path):
        raise FileNotFoundError(f"Schema file not found: {schema_file_path}")
    
    with open(schema_file_path, 'r', encoding='utf-8') as f:
        return f.read()

def generate_sql_prompt(english_question: str, schema_context: str) -> str:
    """Generate a prompt for SQL generation based on the English question."""
    prompt = f"""You are a SQL expert. Given the following database schema and an English question, generate the appropriate SQL query.

DATABASE SCHEMA:
{schema_context}

ENGLISH QUESTION: {english_question}

Please generate a SQL query that answers this question. The query should:
1. Be syntactically correct SQL
2. Use the appropriate tables and columns from the schema
3. Include proper JOINs where needed
4. Use appropriate WHERE clauses and aggregations
5. Be optimized for readability

Return ONLY the SQL query, nothing else:"""
    return prompt

def get_sql_from_openai(question: str, schema_context: str) -> str:
    """Get SQL query from OpenAI API."""
    try:    
        client = get_openai_client()
        
        prompt = generate_sql_prompt(question, schema_context)
        
        response = client.chat.completions.create(
            model="gpt-3.5-turbo-16k",
            messages=[
                {
                    "role": "system",
                    "content": "You are a SQL expert. Generate only SQL queries, no explanations or additional text."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            temperature=0.1,
            max_tokens=500
        )
        
        sql_query = response.choices[0].message.content.strip()
        
        # Clean up the response - remove any markdown formatting
        if sql_query.startswith('```sql'):
            sql_query = sql_query[6:]
        if sql_query.endswith('```'):
            sql_query = sql_query[:-3]
        
        return sql_query.strip()
        
    except Exception as e:
        raise Exception(f"OpenAI API error: {e}")

def execute_query(sql_query: str, db_path: str) -> List[Dict[str, Any]]:
    """Execute a SQL query and return results as a list of dictionaries."""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(sql_query)
        
        # Get column names
        columns = [description[0] for description in cursor.description]
        
        # Fetch results
        rows = cursor.fetchall()
        results = []
        
        for row in rows:
            results.append(dict(zip(columns, row)))
        
        conn.close()
        return results
        
    except sqlite3.Error as e:
        raise Exception(f"SQL execution error: {e}")

def format_results(results: List[Dict[str, Any]]) -> str:
    """Format query results in a readable way."""
    if not results:
        return "No results found."
    
    # Get column names
    columns = list(results[0].keys())
    
    # Calculate column widths
    col_widths = {}
    for col in columns:
        col_widths[col] = len(col)
        for row in results:
            col_widths[col] = max(col_widths[col], len(str(row[col])))
    
    # Build header
    header = " | ".join(col.ljust(col_widths[col]) for col in columns)
    separator = "-" * len(header)
    
    # Build rows
    rows = []
    for row in results:
        row_str = " | ".join(str(row[col]).ljust(col_widths[col]) for col in columns)
        rows.append(row_str)
    
    return f"{header}\n{separator}\n" + "\n".join(rows)

def get_table_info(db_path: str) -> Dict[str, Any]:
    """Get basic information about all tables."""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
    tables = [row[0] for row in cursor.fetchall()]
    
    table_info = {}
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        row_count = cursor.fetchone()[0]
        table_info[table] = {"row_count": row_count}
    
    conn.close()
    return table_info

def process_question(question: str) -> Dict[str, Any]:
    """Process a question: generate SQL and execute it."""
    if not os.path.exists(DB_PATH):
        raise FileNotFoundError(f"Database not found at {DB_PATH}")
    
    if not os.path.exists(SCHEMA_FILE_PATH):
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_FILE_PATH}")
    
    schema_context = load_schema_context(SCHEMA_FILE_PATH)
    
    # Generate SQL using OpenAI
    print("Generating SQL query using OpenAI...")
    sql_query = get_sql_from_openai(question, schema_context)
    
    print(f"Generated SQL: {sql_query}")
    
    # Execute the query
    print("Executing query...")
    results = execute_query(sql_query, DB_PATH)
    
    return {
        "question": question,
        "sql_query": sql_query,
        "results": results,
        "formatted_results": format_results(results),
        "row_count": len(results)
    }

def interactive_query_generator():
    """Interactive query generator using OpenAI API."""
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return
    
    if not os.path.exists(SCHEMA_FILE_PATH):
        print(f"Schema file not found at {SCHEMA_FILE_PATH}")
        print("Please run the schema generation first: python llmtxt/llmtxt.py")
        return
    
    # Check for OpenAI API key
    if not os.getenv('OPENAI_API_KEY'):
        print("Error: OPENAI_API_KEY environment variable not set")
        print("Please set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    print("=== Database Query Generator with OpenAI ===")
    print("This tool converts English questions to SQL queries and executes them.")
    print("Type 'quit' to exit, 'help' for examples, or 'tables' to see table information.")
    print()
    
    while True:
        try:
            question = input("Enter your question in English: ").strip()
            
            if question.lower() == 'quit':
                break
            elif question.lower() == 'help':
                print("\nExample questions:")
                print("- Show me all artists")
                print("- How many customers do we have?")
                print("- List all albums by AC/DC")
                print("- What are the top 5 most expensive tracks?")
                print("- Show customers and their total spending")
                print("- Which genres have the most tracks?")
                print("- Find all tracks longer than 5 minutes")
                print("- Show employees and their managers")
                print()
                continue
            elif question.lower() == 'tables':
                table_info = get_table_info(DB_PATH)
                print("\nTables in the database:")
                for table, info in table_info.items():
                    print(f"- {table}: {info['row_count']:,} rows")
                print()
                continue
            elif not question:
                continue
            
            print("\n" + "="*50)
            
            # Process the question
            result = process_question(question)
            
            print("\n" + "="*50)
            print("RESULTS:")
            print("="*50)
            print(f"Question: {result['question']}")
            print(f"SQL Query: {result['sql_query']}")
            print(f"Rows returned: {result['row_count']}")
            print()
            print(result['formatted_results'])
            print("="*50)
            
            print("\n" + "-"*50 + "\n")
            
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")
            print("\n" + "-"*50 + "\n")

def generate_prompt_for_question(question: str) -> str:
    """Generate a SQL prompt for a specific question (non-interactive)."""
    if not os.path.exists(SCHEMA_FILE_PATH):
        raise FileNotFoundError(f"Schema file not found at {SCHEMA_FILE_PATH}")
    
    schema_context = load_schema_context(SCHEMA_FILE_PATH)
    return generate_sql_prompt(question, schema_context)

if __name__ == "__main__":
    interactive_query_generator() 