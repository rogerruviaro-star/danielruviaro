
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'inventory.db')

def setup_database():
    print(f"🔌 Conectando ao banco de dados: {DB_PATH}")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tabela Clientes (CRM)
    # trust_level: 0 (novo), 1 (confiável), 2 (vip), -1 (bloqueado)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        phone TEXT UNIQUE NOT NULL,
        name TEXT,
        vehicle_info TEXT, 
        total_spent REAL DEFAULT 0,
        trust_level INTEGER DEFAULT 0,
        last_interaction DATETIME DEFAULT CURRENT_TIMESTAMP,
        notes TEXT
    )
    """)
    
    # Tabela Interações (Memória Completa)
    # type: 'user', 'bot', 'system' (notas internas)
    # file_metadata: JSON com url de fotos/notas fiscais enviadas
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        type TEXT NOT NULL,
        message TEXT,
        file_metadata TEXT,
        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """)
    
    # Tabela Vendas (Histórico simplificado para o Bot lembrar)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sales_history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER,
        items_summary TEXT,
        total_value REAL,
        payment_method TEXT,
        invoice_url TEXT,
        date DATETIME DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY(customer_id) REFERENCES customers(id)
    )
    """)

    # Tabelas de Produto (Garantia de que existem)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE,
        name TEXT,
        brand_id INTEGER,
        price REAL,
        stock_quantity INTEGER
    )
    """)
    
    conn.commit()
    conn.close()
    print("✅ Banco de dados atualizado com sucesso (Tabelas CRM + Inventário).")

if __name__ == '__main__':
    # Garante diretórios
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    setup_database()
