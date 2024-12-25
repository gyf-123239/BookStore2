import psycopg2
from be.model import error
from be.model import db_conn


class Search(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    # 在商铺进行书籍搜索
    def search_in_store(self, store_id, title, author, publisher, isbn, content, tags, book_intro, page=1, per_page=10):
        try:
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            with self.conn.cursor() as cursor:
                # 获取指定店铺内的书籍ID列表
                cursor.execute("""
                    SELECT book_id
                    FROM store
                    WHERE store_id = %s
                """, (store_id,))
                ids = [row[0] for row in cursor.fetchall()]

                qs_dict = {
                    'title': title,
                    'author': author,
                    'publisher': publisher,
                    'isbn': isbn,
                    'content': content,
                    'tags': tags,
                    'book_intro': book_intro
                }
                qs_dict1 = {}
                for key, value in qs_dict.items():
                    if len(value)!= 0:
                        qs_dict1[key] = value
                qs_dict = qs_dict1

                qs_list = []
                for key, value in qs_dict.items():
                    qs_list.append(f"{key} LIKE '%{value}%'")

                condition = " AND ".join(qs_list) if qs_list else "1=1"
                condition = f"book_id IN ({','.join(['%s'] * len(ids))}) AND {condition}" if ids else condition

                query = f"""
                    SELECT *
                    FROM book
                    WHERE {condition}
                    LIMIT %s OFFSET %s
                """
                params = ids + [per_page, (page - 1) * per_page]

                cursor.execute(query, params)
                result = []
                for row in cursor.fetchall():
                    book = {
                        'id': row[0],
                        'title': row[1],
                        'author': row[2],
                        'publisher': row[3],
                        'original_title': row[4],
                        'translator': row[5],
                        'pub_year': row[6],
                        'pages': row[7],
                        'price': row[8],
                        'currency_unit': row[9],
                        'binding': row[10],
                        'isbn': row[11],
                        'author_intro': row[12],
                        'book_intro': row[13],
                        'content': row[14],
                        'tags': row[15]
                    }
                    result.append(book)

        except (Exception, psycopg2.Error) as e:
            return 530, "{}".format(str(e))

        return 200, result

    # 全站搜索书籍
    def search_all(self, title, author, publisher, isbn, content, tags, book_intro, page=1, per_page=10):
        try:
            with self.conn.cursor() as cursor:
                qs_dict = {
                    'title': title,
                    'author': author,
                    'publisher': publisher,
                    'isbn': isbn,
                    'content': content,
                    'tags': tags,
                    'book_intro': book_intro
                }
                qs_dict1 = {}
                for key, value in qs_dict.items():
                    if len(value)!= 0:
                        qs_dict1[key] = value
                qs_dict = qs_dict1

                qs_list = []
                for key, value in qs_dict.items():
                    qs_list.append(f"{key} LIKE '%{value}%'")

                condition = " AND ".join(qs_list) if qs_list else "1=1"

                query = f"""
                    SELECT *
                    FROM book
                    WHERE {condition}
                    LIMIT %s OFFSET %s
                """
                params = [per_page, (page - 1) * per_page]

                cursor.execute(query, params)
                result = []
                for row in cursor.fetchall():
                    book = {
                        'id': row[0],
                        'title': row[1],
                        'author': row[2],
                        'publisher': row[3],
                        'original_title': row[4],
                        'translator': row[5],
                        'pub_year': row[6],
                        'pages': row[7],
                        'price': row[8],
                        'currency_unit': row[9],
                        'binding': row[10],
                        'isbn': row[11],
                        'author_intro': row[12],
                        'book_intro': row[13],
                        'content': row[14],
                        'tags': row[15]
                    }
                    result.append(book)

        except (Exception, psycopg2.Error) as e:
            return 530, "{}".format(str(e))

        return 200, result