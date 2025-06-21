## Features

- **Database Analysis**: Automatic schema extraction from SQLite databases
- **LLM Documentation**: Generates comprehensive schema docs for AI consumption
- **Natural Language to SQL**: Converts English questions to SQL queries using GPT-3.5
- **Query Execution**: Runs generated SQL and formats results
- **Interactive CLI**: Command-line interface for easy querying

## Database

Uses the **Chinook** sample database (music store) with:
- 11 tables, 25,000+ records
- Artists, Albums, Tracks, Customers, Invoices, etc.
- Complex relationships and foreign keys

## Usage

### Interactive Mode
```bash
python genquery/cli.py
```

### Single Question



### Programmatic
```python
from genquery.query_generator import process_question
result = process_question("How many customers do we have?")
```

## Requirements

- Python 3.13+
- OpenAI API key
- Dependencies: `requests`, `openai`

## Example Queries

- "Show me all artists"
- "How many customers do we have?"
- "List all albums by AC/DC"
- "What are the top 5 most expensive tracks?"
- "Show customers and their total spending"

---

**ExplainDB** - Natural language database queries powered by AI.
