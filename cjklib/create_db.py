# -- coding: utf-8 --
# from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String

# # Create an engine that represents the core interface to the database
# engine = create_engine('sqlite:///the_database.db')

# # Create a metadata instance
# metadata = MetaData()

# # Define a table with the appropriate schema
# table = Table('your_table_name', metadata,
#               Column('id', Integer, primary_key=True),
#               Column('name', String),
#               Column('age', Integer),
#               Column('email', String))

# # Create the table in the database
# metadata.create_all(engine)

import sqlite3

#データベースを新規作成 or 読み込み
conn = sqlite3.connect(
    "created_database.db",              #ファイル名
    isolation_level=None,
)

from glob import glob
import pandas as pd
all_sql_files = glob("data/*.sql")
#フィールド作成用SQL文
for sql_file in all_sql_files:
    fd = open(sql_file, 'r')
    sql = fd.read()
    fd.close()
    table_name = sql.split(" ")[2].strip('"')
    # db.execute(sql)     #sql文を実行
    cursor = conn.execute(f'select * from {table_name}')
    columns = [row[0] for row in cursor.description]
    with open(f"{sql_file.split('.')[0]}.csv", encoding="utf-8") as f:
        lines = f.readlines()
    table_data = []
    print(table_name)
    for line in lines:
        if line.startswith("#"):
            continue
        if table_name == "CharacterShanghaineseIPA":
            after_split = line.strip().split()
        else:
            after_split = line.strip().split(",")
        assert len(after_split) == len(columns), f"table: {table_name}, line:{line}, {len(after_split)}, {len(columns)}, {after_split}"
        table_data.append(after_split)
    table_data = pd.DataFrame(table_data, columns=columns)
    table_data.to_sql(table_name, conn, if_exists='replace', index=False) # writes to file

# conn.execute('CREATE TABLE Glyph AS SELECT glyph FROM localecharacterglyph')
# conn.execute(f'SELECT id, glyphs FROM LocaleCharacterGlyph')
conn.close()      
