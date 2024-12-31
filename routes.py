from flask import render_template, request, jsonify
from app import app, db
from models import InterviewQuestion, Message

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
    question = InterviewQuestion.query.filter(
        InterviewQuestion.question.ilike(f'%{query}%')
    ).first()
    
    if question:
        return jsonify({"response": question.answer})
    return jsonify({"response": "I apologize, but I don't have specific information about that. Please try asking another question about my professional experience or qualifications."})
