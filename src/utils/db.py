from sqlalchemy import create_engine, MetaData, text
from sqlalchemy.schema import CreateTable
from utils.logging import setup_logger

logger = setup_logger(__name__)

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
    logger.info(f"Database {engine.url.database} cleared.")

def clone_schema(source_engine, target_engine):
    clear_database(target_engine)
    
    metadata = MetaData()
    metadata.reflect(bind=source_engine)
    
    metadata.create_all(bind=target_engine)
    logger.info("Schema cloned to sandbox.")

def apply_sql_query(engine, sql_string: str):
    with engine.begin() as conn:
        conn.execute(text(sql_string))