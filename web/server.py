import os
import textwrap
import logging

from clickhouse_connect import get_client
from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse 
from pydantic import BaseModel
from typing import List

from utils.run_cfg import get_schema, execute_structured_sql
from utils.clickhouse_client import get_client
from evals.judge import judge_sql_query

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Defined CFG for the clickhouse table
postgres_grammar = textwrap.dedent(r"""
            // ---------- Punctuation & operators ----------
            SP: " "
            COMMA: ","
            GT: ">"
            EQ: "="
            SEMI: ";"

            // ---------- Start ----------
            start: "SELECT" SP select_list SP "FROM" SP table SP "WHERE" SP amount_filter SP "AND" SP date_filter SP "ORDER" SP "BY" SP sort_cols SP "LIMIT" SP NUMBER SEMI

            // ---------- Projections ----------
            select_list: column (COMMA SP column)*
            column: IDENTIFIER

            // ---------- Tables ----------
            table: IDENTIFIER

            // ---------- Filters ----------
            amount_filter: "total_amount" SP GT SP NUMBER
            date_filter: "order_date" SP GT SP DATE

            // ---------- Sorting ----------
            sort_cols: "order_date" SP "DESC"

            // ---------- Terminals ----------
            IDENTIFIER: /[A-Za-z_][A-Za-z0-9_]*/
            NUMBER: /[0-9]+/
            DATE: /'[0-9]{4}-[0-9]{2}-[0-9]{2}'/
    """)



app = FastAPI(name="CFG Evaluator")
router = APIRouter(prefix="/api", tags=["api"])


class GenerateSQLRequest(BaseModel):
    prompt: str
    table_name: str

class ExecuteSQLRequest(BaseModel):
    sql: str

class JudgeQueryRequest(BaseModel):
    generated_query: str
    ground_truth_query: str
    prompt: str = ""

class BatchJudgeRequest(BaseModel):
    evaluations: List[dict]


@router.post("/generate-sql")
async def generate_sql(request: GenerateSQLRequest):
    try:
        schema = get_schema(request.table_name)

        logger.info(f"Schema: {schema}")

        sql = execute_structured_sql(
            postgres_grammar,
            request.prompt,
            request.table_name,
            schema
        )

        logger.info(f"Generated SQL: {sql}")
        
        return {"sql": sql, "success": True}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@router.post("/execute-sql")
async def execute_sql(request: ExecuteSQLRequest):
    try:
        client = get_client(
            os.getenv("CLICKHOUSE_HOST"), 
            os.getenv("CLICKHOUSE_PORT"), 
            os.getenv("CLICKHOUSE_USER"), 
            os.getenv("CLICKHOUSE_PASSWORD"))
        
        result = client.query(request.sql).result_rows
        return {"result": result, "success": True}
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

@router.post("/judge-query")
async def judge_query(request: JudgeQueryRequest):
    try:
        result = judge_sql_query(
            generated_query=request.generated_query,
            ground_truth_query=request.ground_truth_query,
            prompt=request.prompt
        )
        return {
            "score": result["score"],
            "semantic_match": result["semantic_match"],
            "reasoning": result["reasoning"],
            "success": True
        }
    except Exception as e:
        logger.error(f"Error in judge_query: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e), "success": False}
        )

app.include_router(router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)