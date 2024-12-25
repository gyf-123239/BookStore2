from flask import Blueprint
from flask import request
from flask import jsonify
from be.model.buyer import Buyer
from be.model import search

bp_buyer = Blueprint("buyer", __name__, url_prefix="/buyer")

@bp_buyer.route("/new_order", methods=["POST"])
def new_order():
    user_id: str = request.json.get("user_id")
    store_id: str = request.json.get("store_id")
    books: [] = request.json.get("books")
    id_and_count = []
    for book in books:
        book_id = book.get("id")
        count = book.get("count")
        id_and_count.append((book_id, count))

    b = Buyer()
    code, message, order_id = b.new_order(user_id, store_id, id_and_count)
    return jsonify({"message": message, "order_id": order_id}), code


@bp_buyer.route("/payment", methods=["POST"])
def payment():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    password: str = request.json.get("password")
    b = Buyer()
    code, message = b.payment(user_id, password, order_id)
    return jsonify({"message": message}), code


@bp_buyer.route("/add_funds", methods=["POST"])
def add_funds():
    user_id = request.json.get("user_id")
    password = request.json.get("password")
    add_value = request.json.get("add_value")
    b = Buyer()
    code, message = b.add_funds(user_id, password, add_value)
    return jsonify({"message": message}), code

# 附加内容的前端
# 确认收货接口：买家用户id、订单id，返回响应消息、状态码
@bp_buyer.route("/receive_order", methods=["POST"])
def receive_order():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")

    b = Buyer()
    code, message = b.receive_order(user_id, order_id)
    return jsonify({"message": message}), code

# 获取买家订单接口：买家用户id，返回响应消息、订单列表、状态码
@bp_buyer.route("/get_buyer_orders", methods=["POST"])
def get_buyer_orders():
    user_id: str = request.json.get("user_id")
    b = Buyer()
    code, message, orders = b.get_buyer_orders(user_id)
    return jsonify({"message": message, "orders": orders}), code

# 取消订单接口：买家用户id、订单id，返回响应消息、状态码
@bp_buyer.route("/cancel_order", methods=["POST"])
def cancel_order():
    user_id: str = request.json.get("user_id")
    order_id: str = request.json.get("order_id")
    b = Buyer()
    code, message = b.cancel_order(user_id, order_id)
    return jsonify({"message": message}), code

@bp_buyer.route("/search", methods=["POST"])
def search_books():
    json_obj = request.get_json()
    
    keyword = json_obj.get("keyword", "")
    search_scope = json_obj.get("search_scope", "all")
    search_in_store = json_obj.get("search_in_store", False)
    store_id = json_obj.get("store_id", None)

    u = search.Search()
    code, books = u.search_books(
        keyword=keyword,
        search_scope=search_scope,
        search_in_store=search_in_store,
        store_id=store_id
    )

    # 将查询结果转换为可序列化的格式
    if code == 200:
        books_list = []
        for book in books:
            book_dict = {
                'id': book[0],
                'title': book[1],
                'author': book[2],
                'publisher': book[3],
                'original_title': book[4],
                'translator': book[5],
                'pub_year': book[6],
                'pages': book[7],
                'price': book[8],
                'currency_unit': book[9],
                'binding': book[10],
                'isbn': book[11],
                'author_intro': book[12],
                'book_intro': book[13],
                'content': book[14],
                'tags': book[15]
            }
            books_list.append(book_dict)
        return jsonify({"code": code, "books": books_list}), 200
    else:
        return jsonify({"code": code, "message": books}), code
