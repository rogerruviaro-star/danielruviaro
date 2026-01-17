
-- Schema V2 para o Banco de Dados do Agente Ruviaro

-- Tabela de Marcas (Inteligência de Venda)
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL, -- Ex: "Cojen", "Retov", "Original VW"
    quality_pitch TEXT, -- Argumento positivo: "Encaixe perfeito, similar ao original"
    warning_pitch TEXT, -- Aviso/Defeito: "Plástico mais rígido, exige ajuste no funileiro"
    is_original BOOLEAN DEFAULT 0 -- 1 se for peça Genuína/Original de Montadora
);

-- Tabela de Produtos (As Peças no Estoque)
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    brand_id INTEGER NOT NULL, -- Link com a tabela de marcas
    price DECIMAL(10, 2) NOT NULL,
    stock_quantity INTEGER NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id)
);

-- Tabela de Códigos Originais (Cross-Reference)
-- Permite buscar pelo código da peça velha (OEM) e achar a nossa paralela
CREATE TABLE IF NOT EXISTS oem_codes (
    product_id INTEGER NOT NULL,
    oem_code TEXT NOT NULL, -- Ex: "5U0807217"
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabela de Sinônimos (Gírias)
CREATE TABLE IF NOT EXISTS product_synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    term TEXT NOT NULL,
    FOREIGN KEY (product_id) REFERENCES products(id)
);

-- Tabela de Veículos
CREATE TABLE IF NOT EXISTS vehicles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    maker TEXT NOT NULL,
    model TEXT NOT NULL,
    version TEXT,
    engine TEXT,
    year_start INTEGER NOT NULL,
    year_end INTEGER
);

-- Tabela de Aplicação
CREATE TABLE IF NOT EXISTS parts_application (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    vehicle_id INTEGER NOT NULL,
    notes TEXT,
    FOREIGN KEY (product_id) REFERENCES products(id),
    FOREIGN KEY (vehicle_id) REFERENCES vehicles(id)
);
