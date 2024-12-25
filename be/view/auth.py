from flask import Blueprint
from flask import request
from flask import jsonify
from be.model import user

# 创建认证蓝图，URL前缀为/auth
bp_auth = Blueprint("auth", __name__, url_prefix="/auth")


@bp_auth.route("/login", methods=["POST"])
def login():
    """
    用户登录接口
    请求体参数：
        - user_id: 用户ID
        - password: 用户密码
        - terminal: 终端标识
    返回：
        - message: 响应消息
        - token: 登录令牌
        - code: 状态码
    """
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    terminal = request.json.get("terminal", "")
    u = user.User()
    code, message, token = u.login(
        user_id=user_id, password=password, terminal=terminal
    )
    return jsonify({"message": message, "token": token}), code


@bp_auth.route("/logout", methods=["POST"])
def logout():
    """
    用户登出接口
    请求体参数：
        - user_id: 用户ID
    请求头参数：
        - token: 用户令牌
    返回：
        - message: 响应消息
        - code: 状态码
    """
    user_id: str = request.json.get("user_id")
    token: str = request.headers.get("token")
    u = user.User()
    code, message = u.logout(user_id=user_id, token=token)
    return jsonify({"message": message}), code


@bp_auth.route("/register", methods=["POST"])
def register():
    """
    用户注册接口
    请求体参数：
        - user_id: 用户ID
        - password: 用户密码
    返回：
        - message: 响应消息
        - code: 状态码
    """
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    u = user.User()
    code, message = u.register(user_id=user_id, password=password)
    return jsonify({"message": message}), code


@bp_auth.route("/unregister", methods=["POST"])
def unregister():
    """
    用户注销接口
    请求体参数：
        - user_id: 用户ID
        - password: 用户密码
    返回：
        - message: 响应消息
        - code: 状态码
    """
    user_id = request.json.get("user_id", "")
    password = request.json.get("password", "")
    u = user.User()
    code, message = u.unregister(user_id=user_id, password=password)
    return jsonify({"message": message}), code


@bp_auth.route("/password", methods=["POST"])
def change_password():
    """
    修改密码接口
    请求体参数：
        - user_id: 用户ID
        - oldPassword: 旧密码
        - newPassword: 新密码
    返回：
        - message: 响应消息
        - code: 状态码
    """
    user_id = request.json.get("user_id", "")
    old_password = request.json.get("oldPassword", "")
    new_password = request.json.get("newPassword", "")
    u = user.User()
    code, message = u.change_password(
        user_id=user_id, old_password=old_password, new_password=new_password
    )
    return jsonify({"message": message}), code
