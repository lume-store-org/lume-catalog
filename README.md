<p align="center">
  <img src="docs/logo.svg" alt="Lume Store" width="240" />
</p>

<h1 align="center">
  Lume Store · Catalog
</h1>

<p align="center">
  <img src="docs/arch.gif" alt="Arquitetura da Lume Store com o microserviço de catálogo" />
</p>

<p align="center">
  <a href="https://skillicons.dev">
    <img src="https://skillicons.dev/icons?i=python,flask,mysql,docker" alt="Stacks" />
  </a>
</p>

## Qual a finalidade do projeto?

Microserviço de **catálogo** da Lume Store: produtos, categorias e **estoque**. A leitura é pública; criar, editar e remover produtos é só para administradores. É também quem **reserva e devolve estoque** para o serviço de pedidos, sempre numa transação, e quem define o **preço oficial** de cada item vendido.

Tem o próprio banco MySQL (`catalog_db`) e só é acessível pela rede interna, via [lume-gateway](https://github.com/lume-store-org/lume-gateway).

## O que foi construído

### Rotas

| Método e rota | Acesso | O que faz |
|---|---|---|
| `GET /products` | público | Lista produtos (`search`, `category`, `featured`) |
| `GET /products/categories` | público | Categorias com o total de produtos |
| `GET /products/<id>` | público | Detalhe do produto |
| `POST /products` | admin | Cadastra produto |
| `PUT /products/<id>` | admin | Atualiza produto |
| `DELETE /products/<id>` | admin | Remove produto |
| `POST /internal/stock/reserve` | interno | Reserva estoque de vários produtos numa transação e devolve os preços |
| `POST /internal/stock/release` | interno | Devolve estoque (pedido cancelado ou falha ao gravar) |
| `GET /health` | interno | Status do serviço e do banco |

As rotas `/internal/*` ficam fora do prefixo `/products`, então o gateway não as expõe.

### Banco `catalog_db`

| Tabela | Colunas principais |
|---|---|
| `products` | `name`, `description`, `price`, `stock` (com `CHECK stock >= 0`), `category`, `image`, `featured` |

O `database/init.sql` cria a tabela e o catálogo inicial: 17 produtos em 5 categorias.

## Tecnologias utilizadas

- **Python 3.12 + Flask 3 + Gunicorn**;
- **MySQL 8** com `mysql-connector-python`;
- **Docker:** imagem sem root, com healthcheck.

## Estrutura do repositório

```text
lume-catalog/
├── app.py              # App Flask
├── routes.py           # Rotas de produtos e de estoque
├── database.py         # Conexão (credenciais só por variável de ambiente)
├── database/init.sql   # Tabela e catálogo inicial
├── requirements.txt
└── Dockerfile
```

## Fluxo de funcionamento

1. O `lume-orders` envia `{items: [{product_id, quantity}]}` para `/internal/stock/reserve`.
2. Para cada item: `UPDATE products SET stock = stock - q WHERE id = ? AND stock >= q`.
3. Se algum item não tiver estoque, a transação inteira é desfeita e a resposta é `409`.
4. Se tudo der certo, devolve nome, imagem e **preço oficial** de cada item.

## Variáveis de ambiente

`DB_HOST`, `DB_NAME`, `DB_USER` e `DB_PASSWORD`. Não há valor padrão para as credenciais.

## Como rodar

Pelo [lume-infra](https://github.com/lume-store-org/lume-infra), que sobe o serviço com o seu MySQL.

## Como validar a entrega

- `GET /api/products?search=fone` pelo gateway lista os fones;
- pedido com quantidade maior que o estoque é recusado com `409`;
- cancelar um pedido devolve o estoque;
- `POST /api/products` sem ser admin devolve `403`.

## Projeto Lume Store

| Repositório | Camada |
|---|---|
| [lume-front](https://github.com/lume-store-org/lume-front) | Loja (Next.js) |
| [lume-gateway](https://github.com/lume-store-org/lume-gateway) | API Gateway (Flask) |
| [lume-users](https://github.com/lume-store-org/lume-users) | Microserviço de usuários |
| [lume-catalog](https://github.com/lume-store-org/lume-catalog) | Microserviço de catálogo |
| [lume-orders](https://github.com/lume-store-org/lume-orders) | Microserviço de pedidos |
| [lume-infra](https://github.com/lume-store-org/lume-infra) | Docker Compose com a stack completa |

## Autor

**William Alves Coelho** · [@willtechdev](https://github.com/willtechdev)
