-- Configurar o banco de dados para usar UTF-8
ALTER DATABASE itens_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Configurar a conexão para usar UTF-8
SET NAMES utf8mb4;
SET CHARACTER SET utf8mb4;

CREATE TABLE IF NOT EXISTS itens (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(255) NOT NULL,
    descricao TEXT,
    preco DECIMAL(10, 2) NOT NULL,
    estoque INTEGER DEFAULT 0,
    categoria VARCHAR(100),
    imagem TEXT
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Inserir dados iniciais para testes
INSERT INTO itens (nome, descricao, preco, estoque, categoria)
VALUES
    ('Smartphone Galaxy S22', 'Smartphone Samsung Galaxy S22 128GB', 4999.90, 50, 'Eletrônicos'),
    ('Notebook Dell Inspiron', 'Notebook Dell Inspiron 15 8GB RAM 512GB SSD', 3899.99, 30, 'Informática'),
    ('Smart TV LG 55''', 'Smart TV LG 55 polegadas 4K', 2799.90, 20, 'Eletrônicos');