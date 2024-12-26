import psycopg2
from be.model import error
from be.model import db_conn
import logging

class Search(db_conn.DBConn):
    def __init__(self):
        db_conn.DBConn.__init__(self)

    # 在商铺进行书籍搜索
    def search_in_store(self, keyword, search_scope, store_id):
        try:
            if not self.store_id_exist(store_id):
                return error.error_non_exist_store_id(store_id)

            with self.conn.cursor() as cursor:
                search_field = search_scope.lower()
                if search_field in ['title', 'author', 'tags']:
                    cursor.execute(
                        f"""
                        SELECT b.* 
                        FROM book b
                        JOIN store s ON b.id = s.book_id
                        WHERE s.store_id = %s 
                        AND b.{search_field} ILIKE %s
                        """,
                        (store_id, '%' + keyword + '%')
                    )
                elif search_field == 'content':
                    cursor.execute(
                        """
                        SELECT b.* 
                        FROM book b
                        JOIN store s ON b.id = s.book_id
                        WHERE s.store_id = %s 
                        AND to_tsvector('english', b.content) @@ to_tsquery('english', %s)
                        """,
                        (store_id, keyword)
                    )
                results = cursor.fetchall()
                if not results:
                    return error.error_book_not_found_in_the_store(keyword, store_id)

        except Exception as e:
            logging.error(f"Store search error: {e}")
            return 530, "店铺内搜索失败"
        return 200, results

    # 全站搜索书籍
    def search_all(self, keyword, search_scope):
        try:
            with self.conn.cursor() as cursor:
                search_field = search_scope.lower()
                if search_field == 'content':
                    cursor.execute(
                        """
                        SELECT * 
                        FROM book
                        WHERE to_tsvector('english', content) @@ to_tsquery('english', %s)
                        """,
                        (keyword,)
                    )
                elif search_field in ['title', 'author', 'tags']:
                    cursor.execute(
                        f"""
                        SELECT * 
                        FROM book
                        WHERE {search_field} ILIKE %s
                        """,
                        ('%' + keyword + '%',)
                    )
                results = cursor.fetchall()
                if not results:
                    return error.error_book_not_found(keyword)

        except (Exception, psycopg2.Error) as e:
            logging.error(f"Global search error: {e}")
            return 530, "{}".format(str(e))
        return 200, results
    
    def search_books(self, keyword, search_scope="all", search_in_store=False, store_id=None):
        try:
            if search_in_store:
                return self.search_in_store(keyword, search_scope, store_id)
            else:
                return self.search_all(keyword, search_scope)
        except Exception as e:   
            logging.error(f"Search error: {e}")
            return 530, "搜索失败"