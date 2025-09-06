from flask import Blueprint, jsonify, request
from src.models.note import Note, db
from src import llm

note_bp = Blueprint('note', __name__)

@note_bp.route('/notes', methods=['GET'])
def get_notes():
    """Get all notes, ordered by most recently updated"""
    notes = Note.query.order_by(Note.updated_at.desc()).all()
    return jsonify([note.to_dict() for note in notes])

@note_bp.route('/notes', methods=['POST'])
def create_note():
    """Create a new note"""
    try:
        data = request.json
        if not data or 'title' not in data or 'content' not in data:
            return jsonify({'error': 'Title and content are required'}), 400

        note = Note(title=data['title'], content=data['content'])

        # optional fields
        tags = data.get('tags')
        if tags is not None:
            note.set_tags_list(tags)

        note.event_date = data.get('event_date')
        note.event_time = data.get('event_time')
        db.session.add(note)
        db.session.commit()
        return jsonify(note.to_dict()), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['GET'])
def get_note(note_id):
    """Get a specific note by ID"""
    note = Note.query.get_or_404(note_id)
    return jsonify(note.to_dict())

@note_bp.route('/notes/<int:note_id>', methods=['PUT'])
def update_note(note_id):
    """Update a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        data = request.json
        
        if not data:
            return jsonify({'error': 'No data provided'}), 400
        
        note.title = data.get('title', note.title)
        note.content = data.get('content', note.content)

        # optional fields
        if 'tags' in data:
            note.set_tags_list(data.get('tags'))

        if 'event_date' in data:
            note.event_date = data.get('event_date')

        if 'event_time' in data:
            note.event_time = data.get('event_time')
        db.session.commit()
        return jsonify(note.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/<int:note_id>', methods=['DELETE'])
def delete_note(note_id):
    """Delete a specific note"""
    try:
        note = Note.query.get_or_404(note_id)
        db.session.delete(note)
        db.session.commit()
        return '', 204
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@note_bp.route('/notes/search', methods=['GET'])
def search_notes():
    """Search notes by title or content"""
    query = request.args.get('q', '')
    if not query:
        return jsonify([])
    
    # Basic search: title, content, and tags (tags stored as JSON text)
    notes = Note.query.filter(
        (Note.title.contains(query)) |
        (Note.content.contains(query)) |
        (Note.tags.contains(query))
    ).order_by(Note.updated_at.desc()).all()
    
    return jsonify([note.to_dict() for note in notes])


@note_bp.route('/notes/<int:note_id>/translate', methods=['POST'])
def translate_note(note_id):
    """Translate a note's title and content to a target language using src.llm.translate

    Request JSON: { "language": "Chinese" | "English" | "Japanese" }
    """
    note = Note.query.get_or_404(note_id)
    data = request.json or {}
    language = data.get('language')

    allowed = {'Chinese', 'English', 'Japanese'}
    if language not in allowed:
        return jsonify({'error': f'Unsupported language. Allowed: {sorted(list(allowed))}'}), 400

    try:
        # Use llm.translate for title and content
        translated_title = llm.translate(language, note.title or '')
        translated_content = llm.translate(language, note.content or '')

        return jsonify({
            'id': note.id,
            'title': translated_title,
            'content': translated_content,
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@note_bp.route('/notes/generate', methods=['POST'])
def generate_note():
    """Generate a new note from natural language input using src.llm.process_user_notes

    Request JSON: { "input": "natural language text", "language": "English" | "Chinese" | "Japanese" }
    """
    data = request.json or {}
    user_input = data.get('input', '').strip()
    language = data.get('language', 'English')

    if not user_input:
        return jsonify({'error': 'Input text is required'}), 400

    allowed_languages = {'Chinese', 'English', 'Japanese'}
    if language not in allowed_languages:
        return jsonify({'error': f'Unsupported language. Allowed: {sorted(list(allowed_languages))}'}), 400

    try:
        # Use llm.process_user_notes to generate structured note
        response_content = llm.process_user_notes(language, user_input)
        
        # Parse the JSON response
        import json
        try:
            note_data = json.loads(response_content)
        except json.JSONDecodeError:
            # If JSON parsing fails, try to extract JSON from the response
            import re
            json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
            if json_match:
                note_data = json.loads(json_match.group())
            else:
                raise ValueError("Could not parse JSON from LLM response")

        # Validate required fields
        if 'Title' not in note_data or 'Notes' not in note_data:
            return jsonify({'error': 'Generated note is missing required fields'}), 500

        # Return the generated note data (not saved to database yet)
        return jsonify({
            'title': note_data.get('Title', ''),
            'content': note_data.get('Notes', ''),
            'tags': note_data.get('Tags', []),
            'original_input': user_input
        })

    except Exception as e:
        return jsonify({'error': f'Failed to generate note: {str(e)}'}), 500

