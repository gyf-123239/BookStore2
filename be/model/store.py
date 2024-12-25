import psycopg2
import logging
import threading

class Store:
    def __init__(self, db_path):
        self.init_tables_postgres()

    def init_tables_postgres(self):
        try:
            with self.get_db_conn_postgres() as conn:
                with conn.cursor() as cursor:
                    # user 表
                    cursor.execute("DROP TABLE IF EXISTS \"user\" CASCADE;")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS \"user\" (
                            user_id TEXT PRIMARY KEY,
                            password TEXT NOT NULL,
                            balance INTEGER NOT NULL,
                            token TEXT,
                            terminal TEXT
                        );
                    """)

                    # user_store 表
                    cursor.execute("DROP TABLE IF EXISTS user_store CASCADE;")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS user_store (
                            store_id TEXT,
                            user_id TEXT,
                            PRIMARY KEY (store_id, user_id)
                        );
                    """)

                    # store 表
                    cursor.execute("DROP TABLE IF EXISTS store CASCADE;")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS store (
                            store_id TEXT,
                            book_id TEXT,
                            price INTEGER,
                            stock_level INTEGER,
                            PRIMARY KEY (store_id, book_id)
                        );
                    """)

                    # new_order 表
                    cursor.execute("DROP TABLE IF EXISTS new_order CASCADE;")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS new_order (
                            order_id TEXT PRIMARY KEY,
                            store_id TEXT,
                            user_id TEXT,
                            status TEXT NOT NULL,
                            created_at TEXT NOT NULL
                        );
                    """)

                    # new_order_detail 表
                    cursor.execute("DROP TABLE IF EXISTS new_order_detail CASCADE;")
                    cursor.execute("""
                        CREATE TABLE IF NOT EXISTS new_order_detail (
                            order_id TEXT,
                            book_id TEXT,
                            count INTEGER,
                            price INTEGER,
                            PRIMARY KEY (order_id, book_id)
                        );
                    """)
        except (Exception, psycopg2.Error) as e:
            logging.error(e)
            conn.rollback()

    def get_db_conn_postgres(self) -> psycopg2.extensions.connection:
        return psycopg2.connect(
            host='localhost',
            user='postgres',
            password='040829',
            database='bookstore'
        )


database_instance: Store = None
# global variable for database sync
init_completed_event = threading.Event()


def init_database(db_path):
    global database_instance
    database_instance = Store(db_path)


def get_db_conn():
    global database_instance
    return database_instance.get_db_conn_postgres()