import sqlite3
from pymongo import MongoClient
from bson.binary import Binary
import psycopg2

# 连接到SQLite数据库
sqlite_conn = sqlite3.connect('./fe/data/book.db')
sqlite_cursor = sqlite_conn.cursor()

# 连接到MongoDB数据库
mongo_client = MongoClient('mongodb://localhost:27017/')
mongo_db = mongo_client['bookstore'] 
mongo_collection = mongo_db['book']

# 连接到PostgreSQL数据库
try:
    postgres_conn = psycopg2.connect(
        host="localhost",
        user="postgres",
        password="040829",
        database="bookstore"
    )
    postgres_cursor = postgres_conn.cursor()
except (Exception, psycopg2.Error) as error:
    print("连接PostgreSQL数据库时出错:", error)
    raise

# 在PostgreSQL数据库中创建Book表
postgres_cursor.execute("""
    CREATE TABLE IF NOT EXISTS book(
        id TEXT PRIMARY KEY,
        title TEXT,
        author TEXT,
        publisher TEXT,
        original_title TEXT,
        translator TEXT,
        pub_year TEXT,
        pages INTEGER,
        price INTEGER,
        currency_unit TEXT,
        binding TEXT,
        isbn TEXT,
        author_intro TEXT,
        book_intro TEXT,
        content TEXT,
        tags TEXT
    )
""")
postgres_conn.commit()
# 在 book 表的 title 列上创建普通索引
postgres_cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_book_title ON book(title);
""")
postgres_conn.commit()
# 在 book 表的 author 列上创建普通索引
postgres_cursor.execute("""
    CREATE INDEX IF NOT EXISTS idx_book_author ON book(author);
""")
postgres_conn.commit()
# 在 book 表的 tag 列上创建普通索引
postgres_cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_book_tag ON book(tags);
""")
postgres_conn.commit()
# 在 book 表的 content 列上创建全文索引
postgres_cursor.execute("""
CREATE INDEX IF NOT EXISTS idx_book_content ON book USING gin(to_tsvector('simple', content));
""")
postgres_conn.commit()

# 查询SQLite数据库中的书籍信息
sqlite_cursor.execute("SELECT * FROM book")
book_records = sqlite_cursor.fetchall()

# 遍历每一行并插入到MongoDB和PostgreSQL中
for record in book_records:
    # 插入到MongoDB中
    mongo_data = {
        'id': record[0],
        'picture': Binary(record[16]) 
    }
    mongo_collection.insert_one(mongo_data)

    # 插入到PostgreSQL中
    postgres_cursor.execute("""
            INSERT INTO Book (id, title, author, publisher, original_title, translator, pub_year, pages, price, currency_unit, binding, isbn, author_intro, book_intro, content, tags)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
        record[0], record[1], record[2], record[3], record[4], record[5], record[6], record[7], int(record[8]), record[9], record[10], record[11], record[12], record[13], record[14], record[15]
    ))
    postgres_conn.commit()

# 关闭游标和连接
postgres_cursor.close()
postgres_conn.close()
sqlite_cursor.close()
sqlite_conn.close()