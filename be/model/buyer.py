import uuid
from datetime import datetime
import logging
import psycopg2
from be.model import db_conn
from be.model import error

class Buyer(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def new_order(self, user_id: str, store_id: str, id_and_count: [(str, int)]) -> (int, str, str):
        order_id = ""
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + (order_id,)
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id) + (order_id,)
            with self.conn:
                uid = "{}_{}_{}".format(user_id, store_id, str(uuid.uuid1()))

                for book_id, count in id_and_count:
                    with self.conn.cursor() as cursor:
                        # 查询商店中图书信息
                        cursor.execute("""
                            SELECT stock_level, price
                            FROM store
                            WHERE store_id = %s AND book_id = %s
                        """, (store_id, book_id))
                        store_data = cursor.fetchone()
                        if store_data is None:
                            return error.error_non_exist_book_id(book_id) + (order_id,)

                        stock_level, price = store_data

                        if stock_level < count:
                            return error.error_stock_level_low(book_id) + (order_id,)

                        # 更新库存
                        cursor.execute("""
                            UPDATE store
                            SET stock_level = stock_level - %s
                            WHERE store_id = %s AND book_id = %s
                        """, (count, store_id, book_id))

                        # 插入订单详情信息
                        cursor.execute("""
                            INSERT INTO new_order_detail (order_id, book_id, count, price)
                            VALUES (%s, %s, %s, %s)
                        """, (uid, book_id, count, price))

                # 插入新订单信息
                with self.conn.cursor() as cursor:
                    cursor.execute("""
                        INSERT INTO new_order (order_id, store_id, user_id, status, created_at)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (uid, store_id, user_id, "unpaid", datetime.now().isoformat()))
                order_id = uid

        except Exception as e: 
            logging.error(f"Error creating new order: {e}")
            return 530, "{}".format(str(e)), ""

        return 200, "ok", order_id

    def payment(self, user_id: str, password: str, order_id: str) -> (int, str):
        try:
            with self.conn:
                with self.conn.cursor() as cursor:
                    # 查询订单信息
                    cursor.execute("""
                        SELECT user_id, status
                        FROM new_order
                        WHERE order_id = %s
                    """, (order_id,))
                    order_data = cursor.fetchone()
                    if order_data is None:
                        return error.error_invalid_order_id(order_id)

                    buyer_id = order_data[0]
                    if buyer_id!= user_id:
                        return error.error_authorization_fail()
                    
                    if order_data[1] != "unpaid":
                        return error.error_status_fail()
                    
                    # 查询用户信息
                    cursor.execute("""
                        SELECT password, balance
                        FROM \"user\"
                        WHERE user_id = %s
                    """, (buyer_id,))
                    user_data = cursor.fetchone()

                    if user_data is None or user_data[0]!= password:
                        return error.error_authorization_fail(order_id)

                    # 查询订单详情并计算总价
                    cursor.execute("""
                        SELECT count, price
                        FROM new_order_detail
                        WHERE order_id = %s
                    """, (order_id,))
                    total_price = sum(detail[0] * detail[1] for detail in cursor.fetchall())

                    if user_data[1] < total_price:
                        return error.error_not_sufficient_funds(order_id)

                    # 更新买家余额
                    cursor.execute("""
                        UPDATE \"user\"
                        SET balance = balance - %s
                        WHERE user_id = %s
                    """, (total_price, buyer_id))

                    # 更新订单状态为已支付
                    cursor.execute("""
                        UPDATE new_order
                        SET status = 'paid'
                        WHERE order_id = %s
                    """, (order_id,))
                    return 200, "ok"
        except Exception as e:  
            logging.error(f"Error payment: {e}")
            return 530, "{}".format(str(e))
        
    def receive_order(self, user_id: str, order_id: str) -> (int, str):
        try:
            with self.conn:
                with self.conn.cursor() as cursor:
                    # 查询订单信息
                    cursor.execute("""
                    SELECT user_id, store_id, status 
                    FROM new_order 
                    WHERE order_id = %s
                    """,(order_id,))
                    order_info = cursor.fetchone()

                    if order_info is None:
                        return error.error_invalid_order_id(order_id)
                    
                    buyer_id = order_info[0]
                    if buyer_id != user_id:
                        return error.error_authorization_fail()
                    
                    status = order_info[2]
                    if status!= "shipped":
                        return error.error_status_fail(order_id)

                    store_id = order_info[1]

                    cursor.execute(
                    "SELECT user_id FROM user_store WHERE store_id = %s",
                    (store_id,)
                    )
                    seller = cursor.fetchone()
                    seller_id = seller[0]

                    cursor.execute(
                        "SELECT count, price FROM new_order_detail WHERE order_id = %s",
                        (order_id,)
                    )
                    order_details = cursor.fetchall()
                    total_price = sum(detail[0] * detail[1] for detail in order_details)

                    cursor.execute(
                        "UPDATE \"user\" SET balance = balance + %s WHERE user_id = %s",
                        (total_price, seller_id)
                    )
                    # 更新订单状态为已收货
                    cursor.execute("""
                        UPDATE new_order
                        SET status = 'received'
                        WHERE order_id = %s
                    """, (order_id,))

        except (Exception, psycopg2.Error) as e:
            logging.error(f"Error receive_order: {e}")
            return 530, "{}".format(str(e))

        return 200, "ok"

    def add_funds(self, user_id, password, add_value) -> (int, str):
        try:
            with self.conn:
                with self.conn.cursor() as cursor:
                    # 查询用户密码
                    cursor.execute("""
                        SELECT password
                        FROM "user"
                        WHERE user_id = %s
                    """, (user_id,))
                    user_password_result = cursor.fetchone()
                    if user_password_result is None:
                        return error.error_authorization_fail()

                    if user_password_result[0]!= password:
                        return error.error_authorization_fail()

                    # 更新用户余额
                    cursor.execute("""
                        UPDATE \"user\"
                        SET balance = balance + %s
                        WHERE user_id = %s
                    """, (add_value, user_id))
                    return 200, "ok"
        except (Exception, psycopg2.Error) as e:
            logging.error(f"Error adding funds: {e}")
            return 530, "{}".format(str(e))

    def get_buyer_orders(self, user_id: str) -> (int, str, list):
        try:
            if not self.user_id_exist(user_id):
                return error.error_non_exist_user_id(user_id) + ("None",)
            with self.conn.cursor() as cursor:
                # 查询买家的所有订单
                cursor.execute("""
                    SELECT store_id, order_id, status
                    FROM new_order
                    WHERE user_id = %s
                """, (user_id,))
                buyer_orders = []
                for row in cursor.fetchall():
                    buyer_orders.append({
                        'store_id': row[0],
                        'order_id': row[1],
                        'status': row[2]
                    })
            return 200, "ok", buyer_orders
        except (Exception, psycopg2.Error) as e:
            logging.error(f"Error get_buyer_orders: {e}")
            return 530, "{}".format(str(e)), []

    def cancel_order(self, user_id: str, order_id: str) -> (int, str):
        try:
            if not self.order_id_exist(user_id, order_id):
                return error.error_non_exist_order_id(order_id)
            with self.conn:
                with self.conn.cursor() as cursor:
                    # 查询订单信息
                    cursor.execute("""
                        SELECT status
                        FROM new_order
                        WHERE order_id = %s
                    """, (order_id,))
                    order_info = cursor.fetchone()
                    if order_info is None:
                        return error.error_invalid_order_id(order_id)
                    status = order_info[0]

                    if status != "unpaid":
                        # 查询用户信息
                        cursor.execute("""
                            SELECT balance
                            FROM \"user\"
                            WHERE user_id = %s
                        """, (user_id,))
                        user_info = cursor.fetchone()
                        if user_info is None:
                            return error.error_exist_user_id(user_id)
                        user_balance = user_info[0]

                        # 查询订单详情并计算订单价格
                        cursor.execute("""
                            SELECT count, price
                            FROM new_order_detail
                            WHERE order_id = %s
                        """, (order_id,))
                        order_price = 0
                        for detail in cursor:
                            count, price = detail
                            order_price += price * count

                        user_balance += order_price
                        # 更新用户余额
                        cursor.execute("""
                            UPDATE \"user\"
                            SET balance = %s
                            WHERE user_id = %s
                        """, (user_balance, user_id))

                    # 更新订单状态为已取消
                    cursor.execute("""
                        UPDATE new_order
                        SET status = 'cancelled'
                        WHERE order_id = %s
                    """, (order_id,))
                    return 200, "ok"
        except (Exception, psycopg2.Error) as e:
            logging.error(f"Error canceling order: {e}")
            return 530, "{}".format(str(e))