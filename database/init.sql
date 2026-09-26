SET NAMES utf8mb4;

CREATE TABLE IF NOT EXISTS products (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    price DECIMAL(10, 2) NOT NULL,
    stock INT NOT NULL DEFAULT 0,
    category VARCHAR(100),
    image TEXT,
    featured BOOLEAN NOT NULL DEFAULT FALSE,
    CONSTRAINT stock_not_negative CHECK (stock >= 0)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Sample catalog (Unsplash photos, served by the front at /produtos)
INSERT INTO products (name, description, price, stock, category, image, featured) VALUES
    ('Smartphone Pro 128 GB', 'Tela OLED de 6,1", câmera dupla de 48 MP e bateria para o dia inteiro.', 4999.90, 25, 'Eletrônicos', '/produtos/smartphone.jpg', TRUE),
    ('Notebook Ultrafino 14"', 'Processador de 8 núcleos, 16 GB de RAM, SSD de 512 GB e só 1,2 kg.', 3899.99, 15, 'Informática', '/produtos/notebook-ultrafino.jpg', TRUE),
    ('Notebook Pro 16"', 'Tela de alta resolução, 32 GB de RAM e SSD de 1 TB para quem cria conteúdo.', 12499.00, 6, 'Informática', '/produtos/notebook-pro.jpg', FALSE),
    ('Smart TV 55" 4K', 'Painel 4K HDR, apps de streaming integrados e controle por voz.', 2799.90, 10, 'Eletrônicos', '/produtos/smart-tv.jpg', TRUE),
    ('Tablet 11" com caneta', 'Tela de 120 Hz, caneta de precisão inclusa e 256 GB de armazenamento.', 5299.00, 12, 'Eletrônicos', '/produtos/tablet.jpg', FALSE),
    ('Câmera instantânea', 'Fotos impressas na hora, flash automático e lente com foco fixo.', 699.90, 18, 'Eletrônicos', '/produtos/camera-instantanea.jpg', FALSE),
    ('Fone over-ear Bluetooth', 'Graves reforçados, 40 horas de bateria e dobrável para viagem.', 449.90, 40, 'Áudio', '/produtos/fone-over-ear.jpg', TRUE),
    ('Headphone com cancelamento de ruído', 'Cancelamento ativo de ruído, modo ambiente e áudio em alta resolução.', 1899.00, 14, 'Áudio', '/produtos/headphone-anc.jpg', FALSE),
    ('Fone sem fio com estojo', 'Encaixe leve, estojo com carregamento e até 24 horas de uso.', 899.00, 30, 'Áudio', '/produtos/fone-sem-fio.jpg', TRUE),
    ('Caixa de som portátil', 'Resistente à água, 12 horas de bateria e som 360°.', 599.90, 22, 'Áudio', '/produtos/caixa-de-som.jpg', FALSE),
    ('Teclado sem fio slim', 'Perfil baixo, teclas silenciosas e bateria recarregável.', 349.90, 35, 'Informática', '/produtos/teclado.jpg', FALSE),
    ('Mouse sem fio', 'Sensor de alta precisão, design ergonômico e receptor USB.', 129.90, 50, 'Informática', '/produtos/mouse.jpg', FALSE),
    ('Smartwatch esportivo', 'GPS, monitor cardíaco, mais de 100 modos de treino e 7 dias de bateria.', 1299.00, 20, 'Acessórios', '/produtos/smartwatch.jpg', TRUE),
    ('Óculos de sol clássico', 'Armação em acetato e lentes polarizadas com proteção UV400.', 399.90, 28, 'Acessórios', '/produtos/oculos.jpg', FALSE),
    ('Tênis de corrida', 'Cabedal em malha respirável e entressola com amortecimento responsivo.', 599.90, 24, 'Moda', '/produtos/tenis-corrida.jpg', TRUE),
    ('Tênis casual preto', 'Visual minimalista, solado leve e palmilha acolchoada.', 449.90, 20, 'Moda', '/produtos/tenis-casual.jpg', FALSE),
    ('Sapato oxford em camurça', 'Camurça legítima, costura aparente e solado de borracha.', 389.90, 12, 'Moda', '/produtos/sapato-oxford.jpg', FALSE);
