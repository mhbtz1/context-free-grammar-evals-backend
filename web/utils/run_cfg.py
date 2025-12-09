import os
from openai import OpenAI
from dotenv import load_dotenv

from .clickhouse_client import get_client

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

def get_schema(table_name):
    print(os.getenv("CLICKHOUSE_HOST"))
    print(os.getenv("CLICKHOUSE_PORT"))
    print(os.getenv("CLICKHOUSE_USER"))
    print(os.getenv("CLICKHOUSE_PASSWORD"))

    client = get_client(
        os.getenv("CLICKHOUSE_HOST"), 
        os.getenv("CLICKHOUSE_PORT"), 
        os.getenv("CLICKHOUSE_USER"), 
        os.getenv("CLICKHOUSE_PASSWORD"))
    
    query = f"""SELECT 
    column_name,
        data_type,
        is_nullable,
        column_default
    FROM information_schema.columns 
    WHERE table_name = '{table_name}';"""
    schema = client.query(query).result_rows
    return schema

def execute_structured_sql(grammar, prompt, table_name, schema):
    response_mssql = client.responses.create(
        model="gpt-5",
        input=f"""Here is the full table information:

        Table Name:
        <table_name>
        {table_name}
        </table_name>

        Table Schema:
        <table_schema>
        {schema}
        </table_schema>

        Natural Language Prompt:
        <prompt>
        {prompt}
        </prompt>

        You must only output the **single** resulting SQL query, nothing else
        """,
        text={"format": {"type": "text"}},
        tools=[
            {
                "type": "custom",
                "name": "mssql_grammar",
                "description": "Executes read-only SQL queries. YOU MUST REASON HEAVILY ABOUT THE QUERY AND MAKE SURE IT OBEYS THE GRAMMAR. ONLY OUTPUT THE RESULTING SQL QUERY, NOTHING ELSE.",
                "format": {
                    "type": "grammar",
                    "syntax": "lark",
                    "definition": grammar
                }
            },
        ],
        parallel_tool_calls=False
    )

    return response_mssql.output[1].content[0].text