
# Mapeamentos de colunas para importação de CSV
# Normaliza nomes variados para um padrão interno

COLUMN_MAPPINGS = {
    # SKU (Código do Produto)
    'sku': ['codigo', 'código', 'cod', 'sku', 'cod.', 'referencia', 'referência', 'ref'],
    
    # Nome/Descrição
    'name': ['descricao', 'descrição', 'desc', 'produto', 'name', 'nome', 'item'],
    
    # Preço
    'price': ['preco', 'preço', 'valor', 'price', 'preco_venda', 'preço_venda', 'vl_venda'],
    
    # Estoque
    'stock': ['estoque', 'qtd', 'quantidade', 'stock', 'saldo', 'qtde', 'qt'],
    
    # Marca
    'brand': ['marca', 'fabricante', 'brand'],
    
    # Aplicação/Veículo
    'application': ['aplicacao', 'aplicação', 'veiculo', 'veículo', 'modelo', 'carro']
}

# Configurações de Importação
IMPORT_BATCH_SIZE = 1000  # Quantidade de registros por transação
DEFAULT_BRAND_NAME = 'Sem Marca'
