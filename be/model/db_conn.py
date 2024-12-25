import psycopg2
from be.model import store

class DBConn:
    def __init__(self):
        # 获取数据库连接
        self.conn = store.get_db_conn()

    def user_id_exist(self, user_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM \"user\" WHERE user_id = %s", (user_id,))
                result = cursor.fetchone()[0]
                return result > 0
        except (Exception, psycopg2.Error) as e:
            print(f"检查用户是否存在时出错: {str(e)}")
            return False

    def book_id_exist(self, store_id, book_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(
                    "SELECT COUNT(*) FROM store WHERE store_id = %s AND book_id = %s",
                    (store_id, book_id)
                )
                result = cursor.fetchone()[0]
                return result > 0
        except (Exception, psycopg2.Error) as e:
            print(f"检查特定商店中图书是否存在时出错: {str(e)}")
            return False

    def store_id_exist(self, store_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM user_store WHERE store_id = %s", (store_id,))
                result = cursor.fetchone()[0]
                return result > 0
        except (Exception, psycopg2.Error) as e:
            print(f"检查商店是否存在时出错: {str(e)}")
            return False

    def order_id_exist(self, order_id):
        try:
            with self.conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM new_order WHERE order_id = %s",(order_id,))
                result = cursor.fetchone()[0]
                return result > 0
        except (Exception, psycopg2.Error) as e:
            print(f"检查用户订单是否存在时出错: {str(e)}")
            return False