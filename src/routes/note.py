import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import cast

from dotenv import load_dotenv
from flask import Blueprint, jsonify, request
from openai import APIError, OpenAI
from src.supabase_client import supabase

note_bp = Blueprint('note', __name__)
load_dotenv()

TRANSLATE_PROMPT = Path(__file__).resolve().parents[2] / 'prompts' / 'translate_prompt.md'

def all_notes() -> list[dict[str, object]]:
    notes: list[dict[str, object]] = []
    offset = 0
    while True:
        batch = cast(list[dict[str, object]], (supabase.table('note').select('*')
                .order('updated_at', desc=True).order('id', desc=True)
                .range(offset, offset + 999).execute().data))
        notes.extend(batch)
        if len(batch) < 1000:
            return notes
        offset += 1000

@note_bp.route('/notes/translate', methods=['POST'])
def translate_note():
    data = request.get_json(silent=True)
    content = cast(dict[str, object], data).get('content') if isinstance(data, dict) else None
    if not isinstance(content, str) or not content.strip():
        return jsonify({'error': 'Note content is required'}), 400

    api_key = os.getenv('OPEN_ROUTER_KEY')
    if not api_key:
        return jsonify({'error': 'Translation is not configured'}), 503

    try:
        prompt = TRANSLATE_PROMPT.read_text(encoding='utf-8')
    except OSError:
        return jsonify({'error': 'Translation prompt is unavailable'}), 500

    try:
        response = OpenAI(base_url='https://openrouter.ai/api/v1', api_key=api_key).chat.completions.create(
            model='qwen/qwen3.8-27b:free',
            messages=[
                {'role': 'system', 'content': prompt},
                {'role': 'user', 'content': content},
            ],
            timeout=30,
        )
        result: object = json.loads(response.choices[0].message.content or '')
    except (APIError, ValueError, IndexError, AttributeError, TypeError) as e:
        print(f"Error translating note: {e}")
        return jsonify({'error': 'Translation failed. Please try again.'}), 502

    translation = cast(dict[str, object], result).get('translation') if isinstance(result, dict) else None
    if not isinstance(translation, str) or not translation.strip():
        return jsonify({'error': 'Translation failed. Please try again.'}), 502

    return jsonify({'translation': translation})

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    return jsonify(all_notes())

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.get_json(silent=True)
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400

        note = supabase.table('note').insert({
            'title': data['title'], 'content': data['content']
        }).execute().data[0]
        return jsonify(note), 201
    except Exception as e:
        print(f"Error creating note: {e}")
        return jsonify({'error': 'Database operation failed'}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id: int):
    """Get a specific note by ID"""
    notes = supabase.table('note').select('*').eq('id', note_id).limit(1).execute().data
    if not notes:
        return jsonify({'error': 'Note not found'}), 404
    return jsonify(notes[0])

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id: int):
    """Update a specific note"""
    try:
        data = request.get_json(silent=True)
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        print(f"Updating note with ID {note_id} with data: {data}")
        changes = {field: data[field] for field in ('title', 'content') if field in data}
        if not changes:
            return get_note(note_id)
        changes['updated_at'] = datetime.now(timezone.utc).isoformat()
        notes = supabase.table('note').update(changes).eq('id', note_id).execute().data
        if not notes:
            print(f"Note with ID {note_id} not found for update")
            return jsonify({'error': 'Note not found'}), 404
        return jsonify(notes[0])
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id: int):
    """Delete a specific note"""
    try:
        notes = supabase.table('note').delete().eq('id', note_id).execute().data
        if not notes:
            return jsonify({'error': 'Note not found'}), 404
        return '', 204
    except Exception:
        return jsonify({'error': 'Database operation failed'}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    search = query.casefold()
    return jsonify([note for note in all_notes()
                    if search in cast(str, note['title']).casefold()
                    or search in cast(str, note['content']).casefold()])

