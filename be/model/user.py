import jwt
import time
import logging
import psycopg2
from psycopg2 import errors
from be.model import error
from be.model import db_conn


def jwt_encode(user_id: str, terminal: str) -> str:
    encoded = jwt.encode(
        {"user_id": user_id, "terminal": terminal, "timestamp": time.time()},
        key=user_id,
        algorithm="HS256",
    )
    return encoded

def jwt_decode(encoded_token, user_id: str) -> str:
    decoded = jwt.decode(encoded_token, key=user_id, algorithms="HS256")
    return decoded

class User:
    token_lifetime: int = 3600  # 令牌有效期为3600秒（1小时）

    def __init__(self):
        db_conn.DBConn.__init__(self)

    def __check_token(self, user_id, db_token, token) -> bool:
        try:
            # 验证令牌是否匹配
            if db_token!= token:
                return False
            # 解码令牌并验证时间戳
            jwt_text = jwt_decode(encoded_token=token, user_id=user_id)
            ts = jwt_text["timestamp"]
            if ts is not None:
                now = time.time()
                # 检查令牌是否在有效期内
                if self.token_lifetime > now - ts >= 0:
                    return True
        except jwt.exceptions.InvalidSignatureError as e:
            logging.error(str(e))
            return False

    def register(self, user_id: str, password: str):
        try:
            # 生成终端标识和令牌
            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            # 插入用户数据
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO \"user\" (user_id, password, balance, token, terminal) VALUES (%s, %s, %s, %s, %s)",
                    (user_id, password, 0, token, terminal)
                )
                cursor.close()
        except (errors.DatabaseError, psycopg2.Error) as e:
            return error.error_exist_user_id(user_id)
        return 200, "ok"

    def check_token(self, user_id: str, token: str) -> (int, str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT token FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()

            if result is None:
                return error.error_authorization_fail()
            db_token = result[0]
            if not db_token or not self.__check_token(user_id, db_token, token):
                return error.error_authorization_fail()
            return 200, "ok"
        except (errors.DatabaseError, psycopg2.Error) as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

    def check_password(self, user_id: str, password: str) -> (int, str):
        try:
            cursor = self.conn.cursor()
            cursor.execute(
                "SELECT password FROM \"user\" WHERE user_id = %s",
                (user_id,)
            )
            result = cursor.fetchone()
            if result is None or result[0]!= password:
                return error.error_authorization_fail()
            return 200, "ok"
        except (errors.DatabaseError, psycopg2.Error) as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))

    def login(self, user_id: str, password: str, terminal: str) -> (int, str, str):
        token = ""
        try:
            # 验证密码
            code, message = self.check_password(user_id, password)
            if code!= 200:
                return code, message, ""

            # 生成新令牌并更新用户信息
            token = jwt_encode(user_id, terminal)
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE \"user\" SET token = %s, terminal = %s WHERE user_id = %s",
                    (token, terminal, user_id)
                )
                if cursor.rowcount == 0:
                    return error.error_authorization_fail() + ("",)
                cursor.close()
        except (errors.DatabaseError, psycopg2.Error) as e:
            return 528, "{}".format(str(e)), ""
        except Exception as e:
            return 530, "{}".format(str(e)), ""
        return 200, "ok", token

    def logout(self, user_id: str, token: str) -> (int, str):
        try:
            # 验证令牌
            code, message = self.check_token(user_id, token)
            if code!= 200:
                return code, message

            # 生成新的临时令牌替换旧令牌
            terminal = "terminal_{}".format(str(time.time()))
            dummy_token = jwt_encode(user_id, terminal)
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE \"user\" SET token = %s, terminal = %s WHERE user_id = %s",
                    (dummy_token, terminal, user_id)
                )
                if cursor.rowcount == 0:
                    return error.error_authorization_fail()
                cursor.close()
        except (errors.DatabaseError, psycopg2.Error) as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def unregister(self, user_id: str, password: str) -> (int, str):
        try:
            code, message = self.check_password(user_id, password)
            if code!= 200:
                return code, message

            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "DELETE FROM \"user\" WHERE user_id = %s",
                    (user_id,)
                )
                if cursor.rowcount == 0:
                    return error.error_authorization_fail()
                cursor.close()
        except (errors.DatabaseError, psycopg2.Error) as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"

    def change_password(self, user_id: str, old_password: str, new_password: str) -> (int, str):
        try:
            # 验证旧密码
            code, message = self.check_password(user_id, old_password)
            if code!= 200:
                return code, message

            terminal = "terminal_{}".format(str(time.time()))
            token = jwt_encode(user_id, terminal)
            with self.conn:
                cursor = self.conn.cursor()
                cursor.execute(
                    "UPDATE \"user\" SET password = %s, token = %s, terminal = %s WHERE user_id = %s",
                    (new_password, token, terminal, user_id)
                )
                if cursor.rowcount == 0:
                    return error.error_authorization_fail()
                cursor.close()
        except (errors.DatabaseError, psycopg2.Error) as e:
            return 528, "{}".format(str(e))
        except Exception as e:
            return 530, "{}".format(str(e))
        return 200, "ok"