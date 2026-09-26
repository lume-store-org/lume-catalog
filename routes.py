from flask import jsonify, request

from database import get_db_connection

FIELDS = 'id, name, description, price, stock, category, image, featured'


def row_to_product(row):
    return {
        'id': row[0],
        'name': row[1],
        'description': row[2],
        'price': float(row[3]),
        'stock': row[4],
        'category': row[5],
        'image': row[6],
        'featured': bool(row[7]),
    }


def is_admin():
    """User role, forwarded by the API Gateway."""
    return request.headers.get('X-User-Admin') == '1'


def find_product(cur, product_id):
    cur.execute(f'SELECT {FIELDS} FROM products WHERE id = %s', (product_id,))
    row = cur.fetchone()
    return row_to_product(row) if row else None


def product_fields(data, current=None):
    current = current or {}
    fields = {key: data.get(key, current.get(key)) for key in ('name', 'description', 'category', 'image')}
    fields['price'] = data.get('price', current.get('price'))
    fields['stock'] = data.get('stock', current.get('stock', 0))
    fields['featured'] = bool(data.get('featured', current.get('featured', False)))

    if not fields['name'] or fields['price'] is None:
        return None, 'Nome e preço são obrigatórios'
    try:
        fields['price'] = float(fields['price'])
        fields['stock'] = int(fields['stock'])
    except (TypeError, ValueError):
        return None, 'Preço e estoque devem ser numéricos'
    if fields['price'] <= 0 or fields['stock'] < 0:
        return None, 'Preço deve ser positivo e estoque não pode ser negativo'
    return fields, None


def register_routes(app):
    @app.route('/products', methods=['GET'])
    def list_products():
        filters, params = [], []
        if request.args.get('category'):
            filters.append('category = %s')
            params.append(request.args['category'])
        if request.args.get('search'):
            filters.append('(name LIKE %s OR description LIKE %s)')
            params += [f"%{request.args['search']}%"] * 2
        if request.args.get('featured') == 'true':
            filters.append('featured = TRUE')
        where = f"WHERE {' AND '.join(filters)}" if filters else ''

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(f'SELECT {FIELDS} FROM products {where} ORDER BY featured DESC, name', params)
        products = [row_to_product(r) for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({'products': products})

    @app.route('/products/categories', methods=['GET'])
    def list_categories():
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('SELECT category, COUNT(*) FROM products WHERE category IS NOT NULL GROUP BY category ORDER BY category')
        categories = [{'name': r[0], 'total': r[1]} for r in cur.fetchall()]
        cur.close()
        conn.close()
        return jsonify({'categories': categories})

    @app.route('/products/<int:product_id>', methods=['GET'])
    def get_product(product_id):
        conn = get_db_connection()
        cur = conn.cursor()
        product = find_product(cur, product_id)
        cur.close()
        conn.close()
        if product is None:
            return jsonify({'error': 'Produto não encontrado'}), 404
        return jsonify(product)

    @app.route('/products', methods=['POST'])
    def create_product():
        if not is_admin():
            return jsonify({'error': 'Apenas administradores'}), 403
        fields, error = product_fields(request.get_json(silent=True) or {})
        if error:
            return jsonify({'error': error}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            'INSERT INTO products (name, description, price, stock, category, image, featured) '
            'VALUES (%(name)s, %(description)s, %(price)s, %(stock)s, %(category)s, %(image)s, %(featured)s)',
            fields,
        )
        conn.commit()
        product = find_product(cur, cur.lastrowid)
        cur.close()
        conn.close()
        return jsonify(product), 201

    @app.route('/products/<int:product_id>', methods=['PUT'])
    def update_product(product_id):
        if not is_admin():
            return jsonify({'error': 'Apenas administradores'}), 403
        conn = get_db_connection()
        cur = conn.cursor()
        try:
            current = find_product(cur, product_id)
            if current is None:
                return jsonify({'error': 'Produto não encontrado'}), 404
            fields, error = product_fields(request.get_json(silent=True) or {}, current)
            if error:
                return jsonify({'error': error}), 400
            cur.execute(
                'UPDATE products SET name = %(name)s, description = %(description)s, price = %(price)s, stock = %(stock)s, '
                'category = %(category)s, image = %(image)s, featured = %(featured)s WHERE id = %(id)s',
                {**fields, 'id': product_id},
            )
            conn.commit()
            return jsonify(find_product(cur, product_id))
        finally:
            cur.close()
            conn.close()

    @app.route('/products/<int:product_id>', methods=['DELETE'])
    def delete_product(product_id):
        if not is_admin():
            return jsonify({'error': 'Apenas administradores'}), 403
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute('DELETE FROM products WHERE id = %s', (product_id,))
        conn.commit()
        deleted = cur.rowcount
        cur.close()
        conn.close()
        if deleted == 0:
            return jsonify({'error': 'Produto não encontrado'}), 404
        return jsonify({'message': f'Produto {product_id} removido'})

    # Internal routes (outside /products, so the API Gateway does not expose them):
    # the orders service reserves and releases stock in a single transaction.
    @app.route('/internal/stock/reserve', methods=['POST'])
    def reserve_stock():
        lines = (request.get_json(silent=True) or {}).get('items', [])
        if not lines:
            return jsonify({'error': 'Nenhum produto informado'}), 400

        conn = get_db_connection()
        cur = conn.cursor()
        try:
            reserved = []
            for line in lines:
                product_id, quantity = int(line['product_id']), int(line['quantity'])
                if quantity <= 0:
                    raise ValueError(f'Quantidade inválida para o produto {product_id}')
                cur.execute(
                    'UPDATE products SET stock = stock - %s WHERE id = %s AND stock >= %s',
                    (quantity, product_id, quantity),
                )
                if cur.rowcount == 0:
                    product = find_product(cur, product_id)
                    reason = 'não encontrado' if product is None else f"sem estoque suficiente (disponível: {product['stock']})"
                    raise ValueError(f'Produto {product_id} {reason}')
                product = find_product(cur, product_id)
                reserved.append({
                    'product_id': product_id,
                    'name': product['name'],
                    'image': product['image'],
                    'quantity': quantity,
                    'unit_price': product['price'],
                })
            conn.commit()
            return jsonify({'items': reserved})
        except (KeyError, TypeError, ValueError) as e:
            conn.rollback()
            return jsonify({'error': str(e) if isinstance(e, ValueError) else 'Itens inválidos'}), 409
        finally:
            cur.close()
            conn.close()

    @app.route('/internal/stock/release', methods=['POST'])
    def release_stock():
        conn = get_db_connection()
        cur = conn.cursor()
        for line in (request.get_json(silent=True) or {}).get('items', []):
            cur.execute('UPDATE products SET stock = stock + %s WHERE id = %s', (int(line['quantity']), int(line['product_id'])))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({'message': 'Estoque devolvido'})

    @app.route('/health', methods=['GET'])
    def health():
        try:
            conn = get_db_connection()
            conn.close()
            return jsonify({'status': 'ok', 'database': 'connected'}), 200
        except Exception:
            return jsonify({'status': 'error', 'database': 'disconnected'}), 500
