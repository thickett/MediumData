class get_credentials:
    def __init__(self):
        with open("./example_config.yaml", "r") as file:
            credentials = yaml.safe_load(file)
        self.credentials = credentials

    def get_api_key(self):
        """Returns api key that is in config."""
        api_key = self.credentials["openAI"]["api_key"]
        return api_key

    def get_db_conn(self):
        """Returns DB uri,db name."""
        return self.credentials["DB"]


class DBConnector:
    def __init__(self):
      # an arbitrary method for pulling credentials from a config file
        self.get_credentials_object = get_credentials.get_credentials()
      # here self.db_details is simply the db_uri of the database in question.
        self.db_details = self.get_credentials_object.get_db_conn()

    def get_schema_hierarchy(self):
      #set up a string so we can format our output nicely for our llm.
        output_stream = io.StringIO()
        for db, details in self.db_details.items():
            uri = details["uri"]
            schemas = details["schemas"]
            self.engine = create_engine(uri)
            self.inspector = sqlalchemy.inspect(self.engine)

            db_hierarchy = {}

            schema_hierarchy = {}
            # table_names = self.inspector.get_table_names(schema=schema)
            for schema, tables in schemas.items():
                table_names = tables
                col_details = [
                    self.inspector.get_columns(schema=schema, table_name=table)
                    for table in table_names
                ]
                schema_hierarchy[schema] = {
                    table: col for table, col in zip(table_names, col_details)
                }
            db_hierarchy[uri] = schema_hierarchy
            # Create a StringIO object to capture the output, i.e this is the string we paste into the prompt.
            for db in db_hierarchy.keys():
                output_stream.write(f"- {db}\n")
                for schema in db_hierarchy[db].keys():
                    output_stream.write(f"   - {schema}\n")
                    for table in db_hierarchy[db][schema].keys():
                        output_stream.write(f"      - {table}\n")
                        for column in db_hierarchy[db][schema][table]:
                            output_stream.write(
                                f'         - {column["name"]}, {column["type"]}\n'
                            )
            output_stream.write("\n")
        hierarchy = output_stream.getvalue()
        output_stream.close()
        return hierarchy
