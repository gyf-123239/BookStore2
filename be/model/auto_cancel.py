from datetime import datetime, timedelta
from be.model import db_conn
import logging


class OrderAutoCancel(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    def cancel_unpaid_orders(self):
        try:
            with self.conn:
                with self.conn.cursor() as cursor:
                    # 查询未支付的订单
                    cursor.execute("""
                        SELECT order_id, created_at
                        FROM new_order
                        WHERE status = 'unpaid'
                    """)
                    unpaid_orders = cursor.fetchall()

                    current_time = datetime.now()
                    earliest_time = current_time - timedelta(minutes=1)

                    for order in unpaid_orders:
                        order_id, order_time_str = order
                        order_time = datetime.fromisoformat(order_time_str)
                        if order_time < earliest_time:
                            # 更新订单状态为已取消
                            cursor.execute("""
                                UPDATE new_order
                                SET status = 'cancelled'
                                WHERE order_id = %s
                            """, (order_id,))
        except Exception as e:  
            logging.error(f"Error auto cancel_unpaid_orders: {e}")
            return 530, "not"
        return 200, "ok"


if __name__ == "__main__":
    order_auto_cancel = OrderAutoCancel()
    order_auto_cancel.cancel_unpaid_orders()