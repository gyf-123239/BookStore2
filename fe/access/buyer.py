import requests
from urllib.parse import urljoin
from fe.access.auth import Auth


class Buyer:
    def __init__(self, url_prefix, user_id, password):
        self.url_prefix = urljoin(url_prefix, "buyer/")
        self.user_id = user_id
        self.password = password
        self.token = ""
        self.terminal = "my terminal"
        self.auth = Auth(url_prefix)
        code, self.token = self.auth.login(self.user_id, self.password, self.terminal)
        assert code == 200

    def new_order(self, store_id: str, book_id_and_count: [(str, int)]) -> (int, str):
        books = []
        for id_count_pair in book_id_and_count:
            books.append({"id": id_count_pair[0], "count": id_count_pair[1]})
        json = {"user_id": self.user_id, "store_id": store_id, "books": books}
        # print(simplejson.dumps(json))
        url = urljoin(self.url_prefix, "new_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        response_json = r.json()
        return r.status_code, response_json.get("order_id")

    def payment(self, order_id: str):
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "payment")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def add_funds(self, add_value: str) -> int:
        json = {
            "user_id": self.user_id,
            "password": self.password,
            "add_value": add_value,
        }
        url = urljoin(self.url_prefix, "add_funds")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    # 增加新的内容接口
    # 获取买家订单接口：买家用户id，返回响应消息、订单列表、状态码
    def get_order_info(self, order_id):                        
        json = {
            "user_id": self.user_id,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "get_buyer_orders")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        assert r.status_code == 200
        result = r.json()
        orders_info = result['orders']
        order_info = {}
        for i in orders_info:
            if i['order_id'] == order_id:
                order_info = i
        assert len(order_info.keys()) != 0
        return order_info
    
    # 确认收货接口：买家用户id、订单id，返回响应消息、状态码
    def receive_order(self, order_id):
        json = {
            "user_id": self.user_id,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "receive_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    # 取消订单接口：买家用户id、订单id，返回响应消息、状态码
    def cancel_order(self, order_id):
        json = {
            "user_id": self.user_id,
            "order_id": order_id,
        }
        url = urljoin(self.url_prefix, "cancel_order")
        headers = {"token": self.token}
        r = requests.post(url, headers=headers, json=json)
        return r.status_code

    def search_books(self, keyword: str, search_scope: str = "all", 
                search_in_store: bool = False, store_id: str = None) -> (int, list): 
        json = {
            "keyword": keyword,
            "search_scope": search_scope,
            "search_in_store": search_in_store,
            "store_id": store_id
        }
        url = urljoin(self.url_prefix, "search")
        r = requests.post(url, json=json)
        return r.status_code, r.json().get("books", [])