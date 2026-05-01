from sqlalchemy import create_engine, MetaData
from sqlalchemy.schema import CreateTable

def get_engine(url: str):
    return create_engine(url)

def fetch_schema_metadata(engine) -> MetaData:
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return metadata

def metadata_to_ddl(engine, metadata: MetaData) -> str:
    ddl_statements = []
    for table_name in metadata.tables:
        table_obj = metadata.tables[table_name]
        ddl = str(CreateTable(table_obj).compile(engine))
        ddl_statements.append(ddl.strip() + ";")
    
    return "\n\n".join(ddl_statements) if ddl_statements else "Database is empty."

def clear_database(engine):
    metadata = MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(bind=engine)
    print("Database cleared.")