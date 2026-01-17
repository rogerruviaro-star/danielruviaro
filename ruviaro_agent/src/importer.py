import csv
import sqlite3
import os
import sys
import logging
import time

# Configuração de Logs
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("importer.log"),
        logging.StreamHandler()
    ]
)

# Adiciona path do projeto para imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

try:
    from ruviaro_agent.src.config_mappings import COLUMN_MAPPINGS, IMPORT_BATCH_SIZE, DEFAULT_BRAND_NAME
except ImportError:
    # Fallback caso rode diretamente na pasta src
    sys.path.append(os.path.dirname(__file__))
    from config_mappings import COLUMN_MAPPINGS, IMPORT_BATCH_SIZE, DEFAULT_BRAND_NAME

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'database', 'inventory.db')

def get_db():
    return sqlite3.connect(DB_PATH)

def cache_auxiliary_data(cursor):
    """Carrega marcas e veículos em memória para evitar SELECTs repetitivos."""
    caches = {
        'brands': {},
        'vehicles': {}
    }
    
    # Cache Marcas
    try:
        cursor.execute("SELECT id, name FROM brands")
        for row in cursor.fetchall():
            caches['brands'][row[1].lower()] = row[0]
    except sqlite3.OperationalError:
        logging.warning("Tabela brands não encontrada. O DB será inicializado?")
        
    return caches

def get_or_create_brand(cursor, brand_name, cache):
    brand_key = brand_name.lower().strip()
    if not brand_key:
        brand_key = DEFAULT_BRAND_NAME.lower()
        brand_name = DEFAULT_BRAND_NAME
        
    if brand_key in cache:
        return cache[brand_key]
    
    cursor.execute(
        "INSERT INTO brands (name, quality_pitch, warning_pitch, is_original) VALUES (?, ?, ?, ?)",
        (brand_name, 'Marca padrão de mercado.', '', 0)
    )
    new_id = cursor.lastrowid
    cache[brand_key] = new_id
    return new_id

def process_batch(cursor, batch, cache):
    """Processa um lote de linhas e prepara dados para inserção/atualização."""
    
    for row in batch:
        sku = row.get('sku')
        name = row.get('name')
        
        if not sku or not name:
            continue
            
        # Tratamento de Preço
        try:
            price_raw = str(row.get('price', '0')).replace('R$', '').replace('.', '').replace(',', '.').strip()
            price = float(price_raw)
        except:
            price = 0.0
            
        # Tratamento de Estoque
        try:
            stock = int(float(str(row.get('stock', '0')).strip()))
        except:
            stock = 0
            
        # Marca
        brand_name = row.get('brand', DEFAULT_BRAND_NAME)
        brand_id = get_or_create_brand(cursor, brand_name, cache['brands'])
        
        # Upsert Logic
        cursor.execute("""
            UPDATE products 
            SET name=?, brand_id=?, price=?, stock_quantity=? 
            WHERE sku=?
        """, (name, brand_id, price, stock, sku))
        
        if cursor.rowcount == 0:
            cursor.execute("""
                INSERT INTO products (sku, name, brand_id, price, stock_quantity)
                VALUES (?, ?, ?, ?, ?)
            """, (sku, name, brand_id, price, stock))

def detect_format(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            sample = f.read(2048)
            delimiter = ';' if ';' in sample else ','
            return {'encoding': 'utf-8', 'delimiter': delimiter}
    except:
        return {'encoding': 'latin-1', 'delimiter': ';'}

def import_csv(filepath):
    if not os.path.exists(filepath):
        logging.error(f"Arquivo não encontrado: {filepath}")
        print(f"❌ Arquivo não encontrado: {filepath}")
        return

    start_time = time.time()
    conn = get_db()
    cursor = conn.cursor()
    
    # Cria tabelas se não existirem (básico)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS brands (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE,
        quality_pitch TEXT,
        warning_pitch TEXT,
        is_original INTEGER
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sku TEXT UNIQUE,
        name TEXT,
        brand_id INTEGER,
        price REAL,
        stock_quantity INTEGER,
        FOREIGN KEY(brand_id) REFERENCES brands(id)
    )
    """)
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS vehicles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        maker TEXT,
        model TEXT,
        version TEXT,
        engine TEXT,
        year_start INTEGER,
        year_end INTEGER
    )
    """)
    
    logging.info("Carregando cache...")
    caches = cache_auxiliary_data(cursor)
    
    fmt = detect_format(filepath)
    print(f"📊 Formato: {fmt['encoding']} | Delimitador: '{fmt['delimiter']}'")
    
    lines_processed = 0
    batch = []
    
    try:
        with open(filepath, 'r', encoding=fmt['encoding']) as f:
            reader = csv.DictReader(f, delimiter=fmt['delimiter'])
            
            # Identify columns
            header = reader.fieldnames
            col_map = {} # csv_col -> internal_col
            
            for h in header:
                h_clean = h.lower().strip()
                for endpoint, variants in COLUMN_MAPPINGS.items():
                    if h_clean in variants:
                        col_map[h] = endpoint
                        break
            
            print(f"📋 Colunas Identificadas: {col_map}")
            
            for row in reader:
                clean_row = {}
                for csv_col, val in row.items():
                    if csv_col in col_map:
                        clean_row[col_map[csv_col]] = val
                
                batch.append(clean_row)
                
                if len(batch) >= IMPORT_BATCH_SIZE:
                    process_batch(cursor, batch, caches)
                    conn.commit()
                    lines_processed += len(batch)
                    print(f"\r🚀 Processados: {lines_processed}...", end='')
                    batch = []
            
            if batch:
                process_batch(cursor, batch, caches)
                conn.commit()
                lines_processed += len(batch)

    except Exception as e:
        logging.error(f"Erro fatal: {e}")
        print(f"\n❌ Erro: {e}")
    finally:
        conn.close()
        
    duration = time.time() - start_time
    print(f"\n✅ Concluído em {duration:.2f}s! Total: {lines_processed} itens.")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        import_csv(sys.argv[1])
    else:
        print("Uso: python importer.py <caminho_do_csv>")
