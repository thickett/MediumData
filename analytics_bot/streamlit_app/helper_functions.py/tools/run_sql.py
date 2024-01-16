from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import pandas as pd
from langchain.tools import BaseTool
from sqlalchemy import create_engine


class SQLSchema(BaseModel):
    sql_code: str = Field(description="MUST be valid SQL code.")
    file_name: str = Field(
        description="A unique file name for the data to be saved to."
    )
    dburi: str = Field(
        description="The uri of the database you need to connect to.\
        this is found in the hierarchy."
    )


class run_sql(BaseTool):
    name = "run_sql"
    description = """this tool is used to run generated SQL code against a database. it requires SQL code as the input.
    Aim to format the sql code nicely with white space and line breaks."""

    args_schema: type[SQLSchema] = SQLSchema
    return_direct = False

    def _run(self, sql_code: SQLSchema, file_name: SQLSchema, dburi: SQLSchema):
        try:
            engine = create_engine(dburi)
            connection = engine.connect()
        except Exception as e:
            error_message = f"you have tried to connect to a databse that doesnt exist. makesure you are using one of the uris from the prompt. error: {e}"
            return {"error": error_message}

        try:
            data = pd.read_sql_query(sql_code, connection)
            # save off any sql code that was written
            with open(r"./Back_end/output_data/sql_code.sql", "w") as f:
                f.write(sql_code)
            # save off the returned data.
            data_directory = f"./Back_end/output_data/{file_name}.csv"
            data.to_csv(data_directory, index=False)
            return {
                "data_directry": data_directory,
                "columns": list(data.columns),
                "data": data.head(
                    100
                ),  # this is to ensure the data is not too large to be returned. (run into token limits otherwise.)
            }
        except Exception as e:
            error_message = f"An error occured. you are probably calling a table or schema that does not exist. look back at the database hierarchy and make sure you are referencing real tables. DO not query the same column as before.: {e}"
            return {"error": error_message}

