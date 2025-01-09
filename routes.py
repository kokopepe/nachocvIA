import os
from flask import render_template, request, jsonify
from werkzeug.utils import secure_filename
from app import app, db
from models import Message, Appointment, ChatMessage
from utils.rag_utils import load_content_from_file, find_relevant_context, get_chat_response
from utils.linkedin_scraper import save_linkedin_data
from datetime import datetime, timedelta
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Ensure content directories exist
os.makedirs('content/interviews', exist_ok=True)

# Load content at startup
knowledge_base = load_content_from_file()

@app.route('/appointment/slots', methods=['GET'])
def get_appointment_slots():
    try:
        # Get start and end dates from query parameters with default values
        start_date = request.args.get('start', type=str, default=datetime.utcnow().isoformat())
        end_date = request.args.get('end', type=str, default=(datetime.utcnow() + timedelta(days=30)).isoformat())

        # Convert string dates to datetime objects for comparison
        start_datetime = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_datetime = datetime.fromisoformat(end_date.replace('Z', '+00:00'))

        # Query appointments within the date range
        appointments = Appointment.query.filter(
            Appointment.date >= start_datetime,
            Appointment.date <= end_datetime,
            Appointment.status != 'cancelled'
        ).all()

        # Return appointments as JSON
        return jsonify({
            'success': True,
            'appointments': [{
                'date': apt.date.isoformat(),
                'duration': apt.duration
            } for apt in appointments]
        })
    except Exception as e:
        logger.error(f"Error fetching appointment slots: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e),
            'appointments': []  # Return empty list on error
        }), 500

# Update the appointment route to handle timezone
@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        try:
            data = request.json
            appointment = Appointment(
                name=data['name'],
                email=data['email'],
                user_type=data['user_type'],
                company=data['company'],
                date=datetime.fromisoformat(data['date'].replace('Z', '+00:00')),
                timezone=data['timezone'],
                notes=data['notes']
            )
            db.session.add(appointment)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error saving appointment: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    return render_template('appointment.html')

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/cv')
def cv():
    return render_template('cv.html')

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        try:
            message = Message(
                name=request.form['name'],
                email=request.form['email'],
                message=request.form['message']
            )
            db.session.add(message)
            db.session.commit()
            return jsonify({"success": True})
        except Exception as e:
            logger.error(f"Error saving contact message: {str(e)}")
            return jsonify({"success": False, "error": str(e)})
    return render_template('contact.html')


@app.route('/chatbot', methods=['POST'])
def chatbot():
    try:
        data = request.json
        query = data.get('query', '').strip()
        user_type = data.get('user_type', 'other')

        if not query:
            return jsonify({"response": "Please ask a question."})

        # Get response using RAG
        context = find_relevant_context(query, knowledge_base)
        response = get_chat_response(query, context) if context else "I apologize, but I don't have enough information to answer that question accurately."

        # Save chat message
        chat_message = ChatMessage(
            user_type=user_type,
            message=query,
            response=response
        )
        db.session.add(chat_message)
        db.session.commit()

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
    except Exception as e:
        logger.error(f"Error in chatbot: {str(e)}")
        return jsonify({
            "response": "I apologize, but I encountered an error processing your question.",
            "suggest_meeting": False
        })

# Admin routes
@app.route('/admin')
def admin():
    return render_template('admin.html')

@app.route('/admin/import-linkedin', methods=['POST'])
def import_linkedin():
    try:
        data = request.json
        linkedin_url = data.get('url')

        if not linkedin_url:
            return jsonify({"success": False, "error": "LinkedIn URL is required"})

        if not linkedin_url.startswith(('http://', 'https://')):
            return jsonify({"success": False, "error": "Invalid LinkedIn URL format"})

        if 'linkedin.com/in/' not in linkedin_url.lower():
            return jsonify({"success": False, "error": "Invalid LinkedIn profile URL"})

        # Save LinkedIn data to JSON file in content/interviews directory
        success = save_linkedin_data(linkedin_url)

        if success:
            # Reload knowledge base after successful import
            global knowledge_base
            knowledge_base = load_content_from_file()
            logger.info(f"Successfully imported LinkedIn profile from {linkedin_url}")
            return jsonify({"success": True})
        else:
            logger.error(f"Failed to import LinkedIn profile from {linkedin_url}")
            return jsonify({"success": False, "error": "Failed to import LinkedIn profile"})

    except Exception as e:
        logger.error(f"Error importing LinkedIn profile: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

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
        logger.error(f"Error uploading file: {str(e)}")
        return jsonify({"success": False, "error": str(e)})

@app.route('/admin/content')
def get_content():
    try:
        with open('content/knowledge_base.txt', 'r') as f:
            return f.read()
    except FileNotFoundError:
        return "No content available"
    except Exception as e:
        logger.error(f"Error reading content: {str(e)}")
        return f"Error reading content: {str(e)}"