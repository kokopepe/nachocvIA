from flask import render_template, request, jsonify
from app import app, db
from models import Message
from utils.rag_utils import load_content_from_file, find_relevant_context, get_chat_response

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

@app.route('/chatbot', methods=['POST'])
def chatbot():
    query = request.json.get('query', '').strip()
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
    return jsonify({"response": response})