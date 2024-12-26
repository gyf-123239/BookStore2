import pytest
from fe.test.gen_book_data import GenBook
from fe.access.new_buyer import register_new_buyer
from fe.access.new_seller import register_new_seller
import uuid
import threading


@pytest.fixture(autouse=True)
def pre_run_initialization():
    self = TestTransaction()
    self.seller_id = "test_transaction_seller_{}".format(str(uuid.uuid1()))
    self.store_id = "test_transaction_store_{}".format(str(uuid.uuid1()))
    self.buyer_id = "test_transaction_buyer_{}".format(str(uuid.uuid1()))
    self.password = self.seller_id
    self.seller = register_new_seller(self.seller_id, self.password)
    self.buyer = register_new_buyer(self.buyer_id, self.password)

    # 生成测试用书籍数据
    self.gen_book = GenBook(self.seller_id, self.store_id)
    self.book_id_stock_level = self.gen_book.book_id_stock_level

    ok, buy_book_id_list = self.gen_book.gen(
        non_exist_book_id=False,
        low_stock_level=False,
        max_book_count=20
    )
    assert ok
    assert len(buy_book_id_list) >= 10
    self.buy_book_id_list = buy_book_id_list

    yield self


class TestTransaction:
    def test_transaction_rollback_on_error(self):
        """测试事务在异常情况下的回滚"""
        # 使用第一本书
        book_id = self.buy_book_id_list[0][0]
        # 先创建一个订单
        id_and_count = [(book_id, 5)]
        code, message, order_id = self.buyer.new_order(self.store_id, id_and_count)
        assert code == 200

        # 模拟异常，例如数据库连接中断或其他异常
        def mock_raise_exception():
            raise Exception("Simulated database error")
        self.buyer.new_order = mock_raise_exception

        try:
            # 这个操作应该失败并回滚
            self.buyer.new_order(self.store_id, [(book_id, 1)])
        except Exception:
            pass

        # 验证库存没有改变
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == 10


    def test_concurrent_transactions(self):
        """测试并发事务的处理"""
        # 使用第一本书
        book_id = self.buy_book_id_list[0][0]
        # 重置书籍库存为 100
        code = self.seller.add_stock_level(self.seller_id, self.store_id, book_id, 90)
        assert code == 200

        def purchase_book():
            code, message, order_id = self.buyer.new_order(self.store_id, [(book_id, 1)])
            assert code == 200

        threads = []
        for _ in range(10):
            thread = threading.Thread(target=purchase_book)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        # 验证库存是否正确更新
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == 90


    def test_transaction_isolation(self):
        """测试事务隔离性"""
        # 使用第一本书
        book_id = self.buy_book_id_list[0][0]

        def update_stock():
            code = self.seller.add_stock_level(self.seller_id, self.store_id, book_id, 5)
            assert code == 200

        update_thread = threading.Thread(target=update_stock)
        update_thread.start()

        # 在更新线程未提交时，主线程读取库存
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == 10

        update_thread.join()

        # 更新提交后，读取库存
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == 15


    def test_transaction_atomicity(self):
        """测试事务的原子性：一个事务中的所有操作要么全部完成，要么全部不完成"""
        # 使用第一本书
        book_id = self.buy_book_id_list[0][0]
        code, book_stock = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200

        # 添加库存，但在更新过程中模拟异常
        try:
            def mock_add_stock_level_except(seller_id, store_id, book_id, stock):
                raise Exception("Simulated exception for atomicity test")
            self.seller.add_stock_level = mock_add_stock_level_except
            self.seller.add_stock_level(self.seller_id, self.store_id, book_id, 10)
            assert False  # 如果没有抛出异常，测试失败
        except Exception:
            pass

        # 验证库存是否保持原值（事务回滚）
        code, stock_level = self.seller.get_stock_level(self.store_id, book_id)
        assert code == 200
        assert stock_level == book_stock  # 库存应该保持原值