## script to generate hierarchy of databases supplied by a given config file
from helper_functions.DBconnector import DBConnector
from helper_functions.get_credentials import get_credentials

db_connector = DBConnector()
hierarchy = db_connector.get_schema_hierarchy()

with open("../required_fields/hierarchy.txt", "w") as f:
    f.write(hierarchy)
