import json
from datetime import datetime
import psycopg2
from be.model import error
from be.model import db_conn


class Seller(db_conn.DBConn):
    def __init__(self):
        # 连接到数据库
        db_conn.DBConn.__init__(self)

    # 在商店中添加书籍
    def add_book(
        self,
        user_id: str,
        store_id: str,
        book_id: str,
        book_json_str: str,
        stock_level: int,
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if self.book_id_exist(store_id, book_id):
                return error.error_exist_book_id(book_id)

            with self.conn.cursor() as cursor:
                # 将需要的数据插入到书店表中
                book_info = json.loads(book_json_str)
                cursor.execute("""
                    INSERT INTO store (store_id, book_id, price, stock_level)
                    VALUES (%s, %s, %s, %s)
                """, (store_id, book_id, book_info['price'], stock_level))
            self.conn.commit()
        except (Exception, psycopg2.Error) as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 增加库存
    def add_stock_level(
        self, user_id: str, store_id: str, book_id: str, add_stock_level: int
    ):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)
            if not self.book_id_exist(store_id, book_id):
                return error.error_non_exist_book_id(book_id)

            with self.conn.cursor() as cursor:
                # 更新指定书店的指定书籍的库存
                cursor.execute("""
                    UPDATE store
                    SET stock_level = stock_level + %s
                    WHERE store_id = %s AND book_id = %s
                """, (add_stock_level, store_id, book_id))
            self.conn.commit()
        except (Exception, psycopg2.Error) as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 创建书店
    def create_store(self, user_id: str, store_id: str) -> (int, str):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id)
            if self.store_id_exist(store_id):
                return error.error_exist_store_id(store_id)

            with self.conn.cursor() as cursor:
                # 在用户书店关系表中插入需要的数据
                cursor.execute("""
                    INSERT INTO user_store (store_id, user_id)
                    VALUES (%s, %s)
                """, (store_id, user_id))
            self.conn.commit()
        except (Exception, psycopg2.Error) as e:
            return 530, "{}".format(str(e))

        return 200, "ok"

    # 发货
    def ship_order(self, store_id: str, order_id: str) -> (int, str):
        try:
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            with self.conn.cursor() as cursor:
                # 查找需要发货的订单
                cursor.execute("""
                    SELECT status
                    FROM new_order
                    WHERE order_id = %s
                """, (order_id,))
                new_order_info = cursor.fetchone()
                if new_order_info is None:
                    return error.error_invalid_order_id(order_id)
                status = new_order_info[0]

                if status!= "paid":
                    return error.error_status_fail(order_id)

                # 更新订单状态为已发货
                cursor.execute("""
                    UPDATE new_order
                    SET status = 'shipped'
                    WHERE order_id = %s
                """, (order_id,))
            self.conn.commit()
        except (Exception, psycopg2.Error) as e:
            return 530, "{}".format(str(e))

        return 200, "ok"