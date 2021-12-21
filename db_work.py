import sqlite3


class DBWork:
    def __init__(self, user_id):
        self.user_id = user_id
        self.conn = sqlite3.connect(f'data_base.db')
        self.cur = self.conn.cursor()
        self.cur.execute("""CREATE TABLE IF NOT EXISTS transacts(
           transact_id INTEGER PRIMARY KEY AUTOINCREMENT,
           sum real,
           category TEXT,
           date TEXT,
           description TEXT,
           user_id int);""")
        self.conn.commit()

    def insert(self, *data):
        data = list(data)
        data.append(self.user_id)
        self.cur.execute(f'INSERT INTO transacts(sum, category, date, description, user_id) '
                         f'VALUES({", ".join("?" * (len(data)))});', data)
        self.conn.commit()

    def update(self, field_name, new_value, transact_id):
        self.cur.execute(f'UPDATE transacts '
                         f'SET {field_name} = {new_value} '
                         f'WHERE user_id = {self.user_id} and transact_id = {transact_id};')
        self.conn.commit()

    def delete(self, transact_id):
        self.cur.execute(f'DELETE FROM transacts '
                         f'WHERE user_id = {self.user_id} and transact_id = {transact_id};')
        self.conn.commit()

    def select(self, fields='*'):
        self.cur.execute(f"SELECT {fields} FROM transacts "
                         f"where user_id = {self.user_id}; ")
        return self.cur.fetchall()

    def select_distinct(self, fields='*'):
        self.cur.execute(f"SELECT DISTINCT {fields} FROM transacts "
                         f"where user_id = {self.user_id}; ")
        return self.cur.fetchall()

    def select_where(self, field_name, field_value, fields='*'):
        self.cur.execute(f"SELECT {fields} FROM transacts "
                         f"WHERE user_id = {self.user_id} and {field_name} = {field_value};")
        return self.cur.fetchall()

    def select_where_max(self, field_name, field_value, fields='*'):
        self.cur.execute(
            f"SELECT {fields} FROM transacts WHERE user_id = {self.user_id} and "
            f"{field_name} = (SELECT MAX({field_value}) FROM transacts); ")
        return self.cur.fetchall()

    def select_order_by(self, order_by_field, fields='*'):
        self.cur.execute(f"SELECT {fields} FROM transacts "
                         f"where user_id = {self.user_id} "
                         f"order by {order_by_field}; ")
        return self.cur.fetchall()

    def select_for_category_statistics_expense(self):
        self.cur.execute(f"SELECT sum(sum), category "
                         f"FROM transacts "
                         f"where user_id = {self.user_id} and sum<0 "
                         f"group by category; ")
        return self.cur.fetchall()
