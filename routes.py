from flask import jsonify, request

from database import get_db_connection

CAMPOS = 'id, nome, descricao, preco, estoque, categoria, imagem, destaque'


def row_to_item(row):
    return {
        'id': row[0],
        'nome': row[1],
        'descricao': row[2],
        'preco': float(row[3]),
        'estoque': row[4],
        'categoria': row[5],
        'imagem': row[6],
        'destaque': bool(row[7]),
    }


def is_admin():
    """Papel do usuário, repassado pelo API Gateway."""
    return request.headers.get('X-Usuario-Admin') == '1'


def buscar_item(cur, id):
    cur.execute(f'SELECT {CAMPOS} FROM itens WHERE id = %s', (id,))
    row = cur.fetchone()
    return row_to_item(row) if row else None


def dados_do_item(dados, atual=None):
    atual = atual or {}
    campos = {}
    for campo in ('nome', 'descricao', 'categoria', 'imagem'):
        campos[campo] = dados.get(campo, atual.get(campo))
    campos['preco'] = dados.get('preco', atual.get('preco'))
    campos['estoque'] = dados.get('estoque', atual.get('estoque', 0))
    campos['destaque'] = bool(dados.get('destaque', atual.get('destaque', False)))

    if not campos['nome'] or campos['preco'] is None:
        return None, "Nome e preço são obrigatórios"
    try:
        campos['preco'] = float(campos['preco'])
        campos['estoque'] = int(campos['estoque'])
    except (TypeError, ValueError):
        return None, "Preço e estoque devem ser numéricos"
    if campos['preco'] <= 0 or campos['estoque'] < 0:
        return None, "Preço deve ser positivo e estoque não pode ser negativo"
    return campos, None


def register_routes(app):
    @app.route('/itens', methods=['GET'])
    def listar_itens():
        filtros, params = [], []
        if request.args.get('categoria'):
            filtros.append('categoria = %s')
            params.append(request.args['categoria'])
        if request.args.get('busca'):
            filtros.append('(nome LIKE %s OR descricao LIKE %s)')
            params += [f"%{request.args['busca']}%"] * 2
        if request.args.get('destaque') == 'true':
            filtros.append('destaque = TRUE')
        where = f"WHERE {' AND '.join(filtros)}" if filtros else ''

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f'SELECT {CAMPOS} FROM itens {where} ORDER BY destaque DESC, nome', params)
        itens = [row_to_item(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"itens": itens})

    @app.route('/itens/categorias', methods=['GET'])
    def listar_categorias():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT categoria, COUNT(*) FROM itens WHERE categoria IS NOT NULL GROUP BY categoria ORDER BY categoria')
        categorias = [{'nome': r[0], 'total': r[1]} for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({"categorias": categorias})

    @app.route('/itens/<int:id>', methods=['GET'])
    def obter_item(id):
        conn = get_db_connection()
        cur = conn.cursor()
        item = buscar_item(cur, id)
        cur.close()
        conn.close()
        if item is None:
            return jsonify({"erro": "Item não encontrado"}), 404
        return jsonify(item)

    @app.route('/itens', methods=['POST'])
    def adicionar_item():
        if not is_admin():
            return jsonify({"erro": "Apenas administradores"}), 403
        campos, erro = dados_do_item(request.get_json(silent=True) or {})
        if erro:
            return jsonify({"erro": erro}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO itens (nome, descricao, preco, estoque, categoria, imagem, destaque) '
            'VALUES (%(nome)s, %(descricao)s, %(preco)s, %(estoque)s, %(categoria)s, %(imagem)s, %(destaque)s)',
            campos,
        )
        conn.commit()
        item = buscar_item(cur, cur.lastrowid)
        cur.close()
        conn.close()
        return jsonify(item), 201

    @app.route('/itens/<int:id>', methods=['PUT'])
    def atualizar_item(id):
        if not is_admin():
            return jsonify({"erro": "Apenas administradores"}), 403
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            atual = buscar_item(cur, id)
            if atual is None:
                return jsonify({"erro": "Item não encontrado"}), 404
            campos, erro = dados_do_item(request.get_json(silent=True) or {}, atual)
            if erro:
                return jsonify({"erro": erro}), 400
            cur.execute(
                'UPDATE itens SET nome = %(nome)s, descricao = %(descricao)s, preco = %(preco)s, estoque = %(estoque)s, '
                'categoria = %(categoria)s, imagem = %(imagem)s, destaque = %(destaque)s WHERE id = %(id)s',
                {**campos, 'id': id},
            )
            conn.commit()
            return jsonify(buscar_item(cur, id))
        finally:
            cur.close()
            conn.close()

    @app.route('/itens/<int:id>', methods=['DELETE'])
    def remover_item(id):
        if not is_admin():
            return jsonify({"erro": "Apenas administradores"}), 403
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM itens WHERE id = %s', (id,))
        conn.commit()
        removidos = cur.rowcount
        cur.close()
        conn.close()
        if removidos == 0:
            return jsonify({"erro": "Item não encontrado"}), 404
        return jsonify({"mensagem": f"Item {id} removido com sucesso"})

    # Rotas internas (fora de /itens, então o API Gateway não as expõe):
    # o serviço de pedidos reserva e devolve estoque numa única transação.
    @app.route('/interno/estoque/reservar', methods=['POST'])
    def reservar_estoque():
        pedido = (request.get_json(silent=True) or {}).get('itens', [])
        if not pedido:
            return jsonify({"erro": "Nenhum item informado"}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            reservados = []
            for linha in pedido:
                item_id, quantidade = int(linha['item_id']), int(linha['quantidade'])
                if quantidade <= 0:
                    raise ValueError(f"Quantidade inválida para o item {item_id}")
                cur.execute(
                    'UPDATE itens SET estoque = estoque - %s WHERE id = %s AND estoque >= %s',
                    (quantidade, item_id, quantidade),
                )
                if cur.rowcount == 0:
                    item = buscar_item(cur, item_id)
                    motivo = "não encontrado" if item is None else f"sem estoque suficiente (disponível: {item['estoque']})"
                    raise ValueError(f"Item {item_id} {motivo}")
                item = buscar_item(cur, item_id)
                reservados.append({
                    'item_id': item_id,
                    'nome': item['nome'],
                    'imagem': item['imagem'],
                    'quantidade': quantidade,
                    'preco_unitario': item['preco'],
                })
            conn.commit()
            return jsonify({"itens": reservados})
        except (KeyError, TypeError, ValueError) as e:
            conn.rollback()
            return jsonify({"erro": str(e) if isinstance(e, ValueError) else "Itens inválidos"}), 409
        finally:
            cur.close()
            conn.close()

    @app.route('/interno/estoque/devolver', methods=['POST'])
    def devolver_estoque():
        conn = get_db_connection()
        cur = conn.cursor()
        for linha in (request.get_json(silent=True) or {}).get('itens', []):
            cur.execute('UPDATE itens SET estoque = estoque + %s WHERE id = %s', (int(linha['quantidade']), int(linha['item_id'])))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"mensagem": "Estoque devolvido"})

    @app.route('/health', methods=['GET'])
    def health():
        try:
            conn = get_db_connection()
            conn.close()
            return jsonify({"status": "ok", "database": "connected"}), 200
        except Exception:
            return jsonify({"status": "erro", "database": "disconnected"}), 500
