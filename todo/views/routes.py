from flask import Blueprint, jsonify, request
from todo.models import db
from todo.models.todo import Todo
from datetime import datetime, timedelta

 
api = Blueprint('api', __name__, url_prefix='/api/v1') 

TEST_ITEM = {
    "id": 1,
    "title": "Watch CSSE6400 Lecture",
    "description": "Watch the CSSE6400 lecture on ECHO360 for week 1",
    "completed": True,
    "deadline_at": "2023-02-27T00:00:00",
    "created_at": "2023-02-20T00:00:00",
    "updated_at": "2023-02-20T00:00:00"
}
 
@api.route('/health') 
def health():
    """Return a status of 'ok' if the server is running and listening to request"""
    return jsonify({"status": "ok"})

@api.route('/todos', methods=['GET'])
def get_todos():
     # Get the 'completed' query parameter from the request
    completed_param = request.args.get('completed', None)
     # Convert the string parameter to a boolean if it exists
    completed_filter = None
    if completed_param is not None:
        completed_filter = completed_param.lower() == 'true'

    # Filter todos based on the 'completed' parameter
    if completed_filter is not None:
        todos = Todo.query.filter_by(completed=completed_filter).all()
    else:
        todos = Todo.query.all()

    # Get the 'window' query parameter from the request
    window_param = request.args.get('window', None)
    # Convert the string parameter to an integer if it exists
    window_filter = None
    if window_param is not None:
        try:
            window_filter = int(window_param)
        except ValueError:
            # Handle invalid integer input (e.g., non-integer value)
            return jsonify({'error': 'Invalid window parameter'}), 400

    # Filter todos based on the 'window' parameter
    if window_filter is not None:
        current_date = datetime.now()
        deadline_limit = current_date + timedelta(days=window_filter)
        todos = [todo for todo in todos if datetime.fromisoformat(todo.deadline_at) <= deadline_limit]


    result = []
    for todo in todos:
        result.append(todo.to_dict())
    return jsonify(result)

@api.route('/todos/<int:todo_id>', methods=['GET'])
def get_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    return jsonify(todo.to_dict())

@api.route('/todos', methods=['POST'])
def create_todo():
    if 'title' not in request.json:
        return jsonify({'error': 'Missing required field: title'}), 400
    
    # Check for unexpected fields in the JSON payload
    allowed_fields = ['title', 'description', 'completed', 'deadline_at']
    unexpected_fields = set(request.json.keys()) - set(allowed_fields)

    if unexpected_fields:
        return jsonify({'error': f'Unexpected field(s): {", ".join(unexpected_fields)}'}), 400

    todo = Todo(
        title=request.json.get('title'),
        description=request.json.get('description'),
        completed=request.json.get('completed', False),
    )
    if 'deadline_at' in request.json:
        todo.deadline_at = datetime.fromisoformat(request.json.get('deadline_at'))
    # Adds a new record to the database or will update an existing record
    db.session.add(todo)
    # Commits the changes to the database, this must be called for the changes to be saved
    db.session.commit()
    return jsonify(todo.to_dict()), 201

@api.route('/todos/<int:todo_id>', methods=['PUT'])
def update_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({'error': 'Todo not found'}), 404
    
    # Check if the ID in the URL matches the ID in the JSON payload
    new_todo_id = request.json.get('id')
    if new_todo_id is not None and new_todo_id != todo_id:
        return jsonify({'error': 'Cannot change the ID of an existing todo'}), 400

    allowed_fields = ['title', 'description', 'completed', 'deadline_at']
    unexpected_fields = set(request.json.keys()) - set(allowed_fields)

    if unexpected_fields:
        return jsonify({'error': f'Unexpected field(s): {", ".join(unexpected_fields)}'}), 400

    todo.title = request.json.get('title', todo.title)
    todo.description = request.json.get('description', todo.description)
    todo.completed = request.json.get('completed', todo.completed)
    todo.deadline_at = request.json.get('deadline_at', todo.deadline_at)
    db.session.commit()

    return jsonify(todo.to_dict())

@api.route('/todos/<int:todo_id>', methods=['DELETE'])
def delete_todo(todo_id):
    todo = Todo.query.get(todo_id)
    if todo is None:
        return jsonify({}), 200
    
    db.session.delete(todo)
    db.session.commit()
    return jsonify(todo.to_dict()), 200
 
