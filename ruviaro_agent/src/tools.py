
import sqlite3
import os

DB_PATH = 'ruviaro_agent/database/inventory.db'
CATALOGS_PATH = 'ruviaro_agent/data_import/catalogs_list.md'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def search_web_info(query):
    """
    Simula uma busca na web consultando a Base de Conhecimento Local (Loma).
    Retorna trechos relevantes dos catálogos mapeados.
    """
    if not os.path.exists(CATALOGS_PATH):
        return "Não encontrei minha lista de catálogos offline."
    
    with open(CATALOGS_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Busca simples por palavra chave no markdown
    # Ex: se query="monroe", retorna o bloco da Monroe
    query = query.lower()
    if "catalogo" in query or "manual" in query or "site" in query:
         return f"🔎 **Loma Web Search (Base Conhecimento)**:\n\n{content}"
    
    # Se for busca especifica, tenta filtrar
    results = []
    lines = content.split('\n')
    capture = False
    for line in lines:
        if any(term in line.lower() for term in query.split()):
            results.append(line)
            # Pega as 2 proximas linhas de contexto
            capture = True
            count = 0
            continue
        if capture and count < 2:
            results.append(line)
            count += 1
        else:
            capture = False
            
    if results:
        return "🔎 **Informação Encontrada na Web (Simulado)**:\n" + "\n".join(results)
    
    return "Busquei na base de catálogos mas não achei nada específico sobre isso. Tente buscar no Google: " + query

def search_products(query_term, vehicle_model=None):
    """
    Busca por Nome, Sinônimo ou Código OEM.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    clean_term = query_term.strip()
    like_term = f"%{clean_term}%"
    
    # Query Monstruosa para trazer tudo
    # Prioridade de Ordenação:
    # 1. Tem Estoque (stock > 0) DESC
    # 2. Não é Original (is_original = 0) DESC -> Prioriza paralelos (nossa margem e foco)
    
    sql = """
    SELECT DISTINCT
        p.sku,
        p.name as part_name, 
        p.price, 
        p.stock_quantity,
        b.name as brand_name,
        b.quality_pitch,
        b.warning_pitch,
        b.is_original,
        v.model,
        group_concat(o.oem_code, ', ') as oem_refs
    FROM products p
    JOIN brands b ON p.brand_id = b.id
    LEFT JOIN parts_application pa ON p.id = pa.product_id
    LEFT JOIN vehicles v ON pa.vehicle_id = v.id
    LEFT JOIN product_synonyms ps ON p.id = ps.product_id
    LEFT JOIN oem_codes o ON p.id = o.product_id
    WHERE 
        (p.name LIKE ? OR ps.term LIKE ? OR p.sku LIKE ? OR o.oem_code LIKE ?)
    """
    
    params = [like_term, like_term, like_term, like_term]
    
    if vehicle_model:
        sql += " AND v.model LIKE ?"
        params.append(f"%{vehicle_model}%")
        
    sql += """
    GROUP BY p.id
    ORDER BY 
        (p.stock_quantity > 0) DESC, -- Primeiro o que tem estoque
        b.is_original ASC,           -- Primeiro os paralelos (0 vem antes de 1? ASC 0->1. Sim.)
        p.price ASC
    """

    cursor.execute(sql, params)
    rows = cursor.fetchall()
    conn.close()
    
    results = []
    for row in rows:
        results.append(dict(row))
    return results

def format_stock_response(results):
    if not results:
        return "Putz patrão, procurei aqui por código original, nome e gíria, mas não achei nada no sistema."
    
    response = "🔎 **Resultado da Busca:**\n"
    
    for item in results:
        status_icon = "🟢" if item['stock_quantity'] > 0 else "🔴"
        stock_msg = f"{item['stock_quantity']} peças" if item['stock_quantity'] > 0 else "ZERADO (Sob Encomenda)"
        
        # Lógica de Pitch de Venda
        pitch = ""
        if item['is_original']:
             pitch = f"⚠️ *Peça Genuína*: {item['quality_pitch']} (Só recomendo se você for chato com originalidade, pq é caro!)"
        else:
             pitch = f"✅ *Recomendação*: {item['quality_pitch']}"
             if item['warning_pitch']:
                 pitch += f"\n   ⚠️ *Dica técnica*: {item['warning_pitch']}"

        response += f"\n{status_icon} **{item['part_name']}** - {item['brand_name']}\n"
        if item['oem_refs']:
             response += f"   (Substitui OEM: {item['oem_refs']})\n"
        response += f"   Aplicação: {item['model'] or 'Universal'}\n"
        response += f"   💲 **R$ {item['price']:.2f}** | Estoque: {stock_msg}\n"
        response += f"   {pitch}\n"
        response += "-"*30
    
    return response

if __name__ == "__main__":
    # Teste: Buscando por código OEM da VW
    print(format_stock_response(search_products("5U0807217")))
