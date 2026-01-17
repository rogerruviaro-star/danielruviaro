
import sqlite3
import os

DB_PATH = 'ruviaro_agent/database/inventory.db'
SCHEMA_PATH = 'ruviaro_agent/database/schema.sql'

def create_database():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = f.read()
        cursor.executescript(schema)
    
    print("Banco de dados V3 criado com sucesso.")
    return conn

def seed_data(conn):
    cursor = conn.cursor()
    
    print("Inserindo dados com Lados (LD/LE)...")

    # 1. Marcas
    brands = [
        ('Original VW', 'Peça genuína.', 'Caro.', 1),
        ('Retov', 'Melhor custo-benefício, plástico flexível.', 'Ajuste simples.', 0),
        ('Cojen', 'Acabamento ok.', 'Plástico seco.', 0),
        ('Importado', 'Preço imbatível.', 'Lente pode amarelar com o tempo.', 0),
        ('Metagal', 'Linha de montagem (OEM).', 'Mesma qualidade do original.', 0)
    ]
    cursor.executemany("INSERT INTO brands (name, quality_pitch, warning_pitch, is_original) VALUES (?, ?, ?, ?)", brands)
    
    # 2. Produtos (Peças)
    products = [
        # Lataria Pesada
        ('CAPO-G5-IMP', 'Capo Dianteiro (Preto p/ Pintura)', 4, 450.00, 5),
        ('PAINEL-G5-RET', 'Painel Frontal (Mini Frente)', 2, 220.00, 8),
        
        # Peças com Lado (Retrovisores)
        ('RET-G5-E-META', 'Retrovisor Manual LE (Motorista)', 5, 120.00, 15), # Metagal
        ('RET-G5-D-META', 'Retrovisor Manual LD (Passageiro)', 5, 120.00, 12),
        
        # Faróis
        ('FAROL-G5-E-IMP', 'Farol Foco Simples LE', 4, 180.00, 20),
        ('FAROL-G5-D-IMP', 'Farol Foco Simples LD', 4, 180.00, 18),
        
        # Parachoques (Mantendo anterior)
        ('PC-G5-D-RETOV', 'Parachoque Dianteiro (Prime)', 2, 180.00, 10),
    ]
    cursor.executemany("INSERT INTO products (sku, name, brand_id, price, stock_quantity) VALUES (?, ?, ?, ?, ?)", products)
    
    # 4. Veículos
    vehicles = [
        ('Volkswagen', 'Gol', 'G5', 'Todos', 2008, 2012)
    ]
    cursor.executemany("INSERT INTO vehicles (maker, model, version, engine, year_start, year_end) VALUES (?, ?, ?, ?, ?, ?)", vehicles)

    # 5. Aplicação (Tudo para Gol G5 para facilitar teste)
    apps = []
    # Loop para aplicar produtos 1 a 6 no veiculo 1
    for i in range(1, 8):
        apps.append((i, 1, ''))
        
    cursor.executemany("INSERT INTO parts_application (product_id, vehicle_id, notes) VALUES (?, ?, ?)", apps)

    # 6. Sinônimos
    syns = [
        (1, 'capô'), (1, 'tampa motor'),
        (2, 'frente'), (2, 'suporte radiador'),
        (3, 'espelho'), (4, 'espelho')
    ]
    cursor.executemany("INSERT INTO product_synonyms (product_id, term) VALUES (?, ?)", syns)

    conn.commit()
    print("Dados inseridos!")

if __name__ == '__main__':
    conn = create_database()
    seed_data(conn)
    conn.close()
