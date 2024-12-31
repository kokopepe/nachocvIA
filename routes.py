from flask import render_template, request, jsonify
from app import app, db
from models import Message
from utils.rag_utils import load_interview_content, find_best_match

# Load interview content at startup
interview_content = load_interview_content()

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
    query = request.json.get('query', '').lower()

    # Find best matching Q&A using RAG
    match = find_best_match(query, interview_content)

    return jsonify({"response": match["answer"]})