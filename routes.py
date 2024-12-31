import os
from flask import render_template, request, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Message, Appointment # Added Appointment model import
from utils.rag_utils import load_content_from_file, find_relevant_context, get_chat_response
from datetime import datetime # Added datetime import

# Load content at startup
knowledge_base = load_content_from_file()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cv')
def cv():
    return render_template('cv.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        message = Message(
            name=request.form['name'],
            email=request.form['email'],
            message=request.form['message']
        )
        db.session.add(message)
        db.session.commit()
        return jsonify({"success": True})
    return render_template('contact.html')

@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        try:
            data = request.json
            appointment = Appointment(
                name=data['name'],
                email=data['email'],
                user_type=data['user_type'],
                company=data.get('company', ''),
                date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
                notes=data.get('notes', '')
            )
            db.session.add(appointment)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            return jsonify({"success": False, "error": str(e)})
    return render_template('appointment.html')

@app.route('/chatbot', methods=['POST'])
def chatbot():
    data = request.json
    query = data.get('query', '').strip()
    user_type = data.get('user_type', 'other')

    if not query:
        return jsonify({"response": "Please ask a question."})

    # Get relevant context using RAG
    context = find_relevant_context(query, knowledge_base)

    # If no context found, return a default message
    if not context:
        return jsonify({
            "response": "I apologize, but I don't have enough information to answer that question accurately."
        })

    # Get response using the context
    response = get_chat_response(query, context)

    # Check if we should suggest booking a meeting based on user type and query content
    suggest_meeting = False
    if user_type in ['recruiter', 'employer']:
        meeting_keywords = ['interview', 'meet', 'discuss', 'talk', 'available', 'schedule', 'when']
        if any(keyword in query.lower() for keyword in meeting_keywords):
            suggest_meeting = True

    return jsonify({
        "response": response,
        "suggest_meeting": suggest_meeting
    })

# Admin routes
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin/upload', methods=['POST'])
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file provided"})

        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"})

        if not file.filename.endswith('.txt'):
            return jsonify({"success": False, "error": "Only .txt files are allowed"})

        filename = secure_filename(file.filename)
        file.save('content/knowledge_base.txt')

        # Reload the knowledge base
        global knowledge_base
        knowledge_base = load_content_from_file()

        return jsonify({"success": True})

    except Exception as e:
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/content')
def get_content():
    try:
        with open('content/knowledge_base.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "No content available"
    except Exception as e:
        return f"Error reading content: {str(e)}"