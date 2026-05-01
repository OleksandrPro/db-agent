class MockSQLGenerator:
    def generate(self, current_schema: str, user_input: str) -> str:
        return "ALTER TABLE users ADD COLUMN last_login TIMESTAMP;"