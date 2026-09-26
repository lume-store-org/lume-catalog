from flask import jsonify, request
from database import get_db_connection

def register_routes(app):
    @app.route('/itens', methods=['GET'])
    def listar_itens():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, nome, descricao, preco, estoque, categoria, imagem FROM itens')
        rows = cur.fetchall()
        
        itens = []
        for row in rows:
            item = {
                'id': row[0],
                'nome': row[1],
                'descricao': row[2],
                'preco': float(row[3]),
                'estoque': row[4],
                'categoria': row[5],
                'imagem': row[6]
            }
            itens.append(item)
            
        cur.close()
        conn.close()
        
        return jsonify({"itens": itens})

    @app.route('/itens/<int:id>', methods=['GET'])
    def obter_item(id):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT id, nome, descricao, preco, estoque, categoria, imagem FROM itens WHERE id = %s', (id,))
        row = cur.fetchone()
        
        if row is None:
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404
        
        item = {
            'id': row[0],
            'nome': row[1],
            'descricao': row[2],
            'preco': float(row[3]),
            'estoque': row[4],
            'categoria': row[5],
            'imagem': row[6]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(item)

    @app.route('/itens', methods=['POST'])
    def adicionar_item():
        novo_item = request.json
        nome = novo_item.get('nome')
        descricao = novo_item.get('descricao')
        preco = novo_item.get('preco')
        estoque = novo_item.get('estoque', 0)
        categoria = novo_item.get('categoria')
        imagem = novo_item.get('imagem')
        
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO itens (nome, descricao, preco, estoque, categoria, imagem) VALUES (%s, %s, %s, %s, %s, %s)',
            (nome, descricao, preco, estoque, categoria, imagem)
        )
        # Obter o ID do item inserido usando lastrowid (método do MySQL)
        id = cur.lastrowid
        conn.commit()
        
        # Recuperar o item completo
        cur.execute('SELECT id, nome, descricao, preco, estoque, categoria, imagem FROM itens WHERE id = %s', (id,))
        row = cur.fetchone()
        
        item = {
            'id': row[0],
            'nome': row[1],
            'descricao': row[2],
            'preco': float(row[3]),
            'estoque': row[4],
            'categoria': row[5],
            'imagem': row[6]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(item), 201

    @app.route('/itens/<int:id>', methods=['PUT'])
    def atualizar_item(id):
        item_atualizado = request.json
        nome = item_atualizado.get('nome')
        descricao = item_atualizado.get('descricao')
        preco = item_atualizado.get('preco')
        estoque = item_atualizado.get('estoque')
        categoria = item_atualizado.get('categoria')
        imagem = item_atualizado.get('imagem')
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar se o item existe
        cur.execute('SELECT id FROM itens WHERE id = %s', (id,))
        if cur.fetchone() is None:
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404
            
        # Atualizar o item
        cur.execute(
            'UPDATE itens SET nome = %s, descricao = %s, preco = %s, estoque = %s, categoria = %s, imagem = %s WHERE id = %s',
            (nome, descricao, preco, estoque, categoria, imagem, id)
        )
        conn.commit()
        
        # Recuperar o item atualizado
        cur.execute('SELECT id, nome, descricao, preco, estoque, categoria, imagem FROM itens WHERE id = %s', (id,))
        row = cur.fetchone()
        
        item = {
            'id': row[0],
            'nome': row[1],
            'descricao': row[2],
            'preco': float(row[3]),
            'estoque': row[4],
            'categoria': row[5],
            'imagem': row[6]
        }
        
        cur.close()
        conn.close()
        
        return jsonify(item)

    @app.route('/itens/<int:id>', methods=['DELETE'])
    def remover_item(id):
        conn = get_db_connection()
        cur = conn.cursor()
        
        # Verificar se o item existe
        cur.execute('SELECT id FROM itens WHERE id = %s', (id,))
        if cur.fetchone() is None:
            cur.close()
            conn.close()
            return jsonify({"erro": "Item não encontrado"}), 404
            
        # Remover o item
        cur.execute('DELETE FROM itens WHERE id = %s', (id,))
        conn.commit()
        
        cur.close()
        conn.close()
        
        return jsonify({"mensagem": f"Item {id} removido com sucesso"})

    @app.route('/health', methods=['GET'])
    def health():
        try:
            conn = get_db_connection()
            cur = conn.cursor()
            cur.execute('SELECT 1')
            cur.close()
            conn.close()
            return jsonify({"status": "ok", "database": "connected"}), 200
        except Exception as e:
            return jsonify({"status": "erro", "database": "disconnected", "detalhes": str(e)}), 500