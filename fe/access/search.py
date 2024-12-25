import os
import psycopg2
import simplejson as json
import requests
import base64
from urllib.parse import urljoin
from pymongo import MongoClient
from fe import conf

class Book:
    id: str
    title: str
    author: str
    publisher: str
    original_title: str
    translator: str
    pub_year: str
    pages: int
    price: int
    currency_unit: str
    binding: str
    isbn: str
    author_intro: str
    book_intro: str
    content: str
    tags: str
    pictures: list

    def __init__(self):
        self.tags = []
        self.pictures = []

class BookDB:
    def __init__(self, large: bool = False):
        # 连接到MongoDB
        self.mongo_client = MongoClient('mongodb://localhost:27017/')
        self.mongo_db = self.mongo_client['bookstore']
        self.mongo_collection = self.mongo_db['book']

        # 连接到PostgreSQL
        self.conn = psycopg2.connect(
            dbname="bookstore",
            user="postgres",
            password="040829",
            host="localhost",
            port="5432"
        )
        self.cursor = self.conn.cursor()

    def get_book_count(self):
        query = "SELECT COUNT(*) FROM book"
        self.cursor.execute(query)
        count = self.cursor.fetchone()[0]
        return count

    def get_book_info(self, start, size):
        books = []
        # 从PostgreSQL中获取书籍信息
        self.cursor.execute("""
            SELECT id, title, author, publisher, original_title, translator, pub_year, pages, price, currency_unit, binding, isbn, author_intro, book_intro, content, tags
            FROM book
            ORDER BY id
            OFFSET %s LIMIT %s
        """, (start, size))
        rows = self.cursor.fetchall()

        for row in rows:
            book = Book()
            book.id = row[0]
            book.title = row[1]
            book.author = row[2]
            book.publisher = row[3]
            book.original_title = row[4]
            book.translator = row[5]
            book.pub_year = row[6]
            book.pages = row[7]
            book.price = row[8]
            book.currency_unit = row[9]
            book.binding = row[10]
            book.isbn = row[11]
            book.author_intro = row[12]
            book.book_intro = row[13]
            book.content = row[14]
            book.tags = row[15]

            # 从MongoDB中获取图片数据
            mongo_row = self.mongo_collection.find_one({"id": book.id})
            if mongo_row:
                picture_binary = mongo_row.get('picture')
                picture_base64 = base64.b64encode(picture_binary).decode('utf-8')
                book.pictures.append(picture_base64)

            books.append(book)

        return books


def search_in_store(store_id, title, author, publisher, isbn, content, tags, book_intro, page=1, per_page=10):
    json_data = {
        'store_id': store_id,
        'title': title,
        'author': author,
        'publisher': publisher,
        'isbn': isbn,
        'content': content,
        'tags': tags,
        'book_intro': book_intro,
        'page': page,
        "per_page": per_page
    }
    url = urljoin(urljoin(conf.URL, "search/"), "search_in_store")
    r = requests.post(url, json=json_data)
    return r.status_code, r.json()


def search_all(title, author, publisher, isbn, content, tags, book_intro, page=1, per_page=10):
    json_data = {
        'title': title,
        'author': author,
        'publisher': publisher,
        'isbn': isbn,
        'content': content,
        'tags': tags,
        'book_intro': book_intro,
        'page': page,
        "per_page": per_page
    }
    url = urljoin(urljoin(conf.URL, "search/"), "search_all")
    r = requests.post(url, json=json_data)
    return r.status_code, r.json()