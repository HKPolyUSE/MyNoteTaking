from flask import Blueprint, jsonify, request
from src.supabase_client import supabase

user_bp = Blueprint('user', __name__)

@user_bp.route('/users', methods=['GET'])
def get_users():
    users = []
    offset = 0
    while True:
        batch = supabase.table('user').select('*').order('id').range(offset, offset + 999).execute().data
        users.extend(batch)
        if len(batch) < 1000:
            return jsonify(users)
        offset += 1000

@user_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json(silent=True)
    if not data or 'username' not in data or 'email' not in data:
        return jsonify({'error': 'Username and email are required'}), 400
    try:
        user = supabase.table('user').insert({
            'username': data['username'], 'email': data['email']
        }).execute().data[0]
        return jsonify(user), 201
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 500

@user_bp.route('/users/<int:user_id>', methods=['GET'])
def get_user(user_id):
    users = supabase.table('user').select('*').eq('id', user_id).limit(1).execute().data
    if not users:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(users[0])

@user_bp.route('/users/<int:user_id>', methods=['PUT'])
def update_user(user_id):
    data = request.get_json(silent=True)
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    changes = {field: data[field] for field in ('username', 'email') if field in data}
    if not changes:
        return get_user(user_id)
    try:
        users = supabase.table('user').update(changes).eq('id', user_id).execute().data
        if not users:
            return jsonify({'error': 'User not found'}), 404
        return jsonify(users[0])
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 500

@user_bp.route('/users/<int:user_id>', methods=['DELETE'])
def delete_user(user_id):
    try:
        users = supabase.table('user').delete().eq('id', user_id).execute().data
        if not users:
            return jsonify({'error': 'User not found'}), 404
        return '', 204
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 500
