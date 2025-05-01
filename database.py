import os
import mysql.connector
from mysql.connector import Error

def get_db_connection():
    """Estabelece e retorna uma conexão com o banco de dados MySQL"""
    db_host = os.environ.get('DB_HOST', 'mysql-itens')
    db_name = os.environ.get('DB_NAME', 'itens_db')
    db_user = os.environ.get('DB_USER', 'root')
    db_password = os.environ.get('DB_PASSWORD', 'root')
    
    try:
        conn = mysql.connector.connect(
            host=db_host,
            database=db_name,
            user=db_user,
            password=db_password,
            charset='utf8mb4',
            use_unicode=True,
            collation='utf8mb4_unicode_ci'
        )
        
        # Configurações para garantir UTF-8 na conexão
        cursor = conn.cursor()
        cursor.execute('SET NAMES utf8mb4')
        cursor.execute('SET CHARACTER SET utf8mb4')
        cursor.execute('SET character_set_connection=utf8mb4')
        cursor.close()
        
        return conn
        
    except Error as err:
        print(f"Erro ao conectar ao banco de dados: {err}")
        raise