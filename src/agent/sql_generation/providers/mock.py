from utils.logging import setup_logger


logger = setup_logger(__name__)

class MockSQLGenerator:
    def __init__(self):
        self._call_count = 0

    def generate(self, current_schema: str, user_input: str, error_log: str | None = None) -> str:
        self._call_count += 1
        
        if error_log:
            print(f"\n[Mock] Error from previous attempt: {error_log}")

        if self._call_count == 1:
            logger.warning("\n[Mock] First generation. Making intentional syntax error...")
            # Intentional syntax error (ALTER TABL)
            return "ALTER TABL users ADD COLUMN test_column VARCHAR(50);"
        
        logger.info(f"\n[Mock] Attempt: {self._call_count}. Returning valid SQL...")
        return "ALTER TABLE users ADD COLUMN last_login TIMESTAMP;"