from flask import Flask, render_template, request, send_file, url_for, flash, redirect, jsonify
import numpy as np
import os
from tensorflow.keras.utils import load_img
from tensorflow.keras.preprocessing.image import img_to_array
from tensorflow.keras.models import load_model
import docx
import logging
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types
from dotenv import load_dotenv

# Load environment variables
load_dotenv(os.path.join(os.path.dirname(__file__), '../environment/.env'))

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configure Gemini
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    logger.error("GEMINI_API_KEY not found in environment variables.")
    raise ValueError("GEMINI_API_KEY is required.")

# Initialize the new-style client
try:
    gemini_client = genai.Client(api_key=GEMINI_API_KEY)
    chat_history = []
    logger.info('Gemini client initialized successfully')
except Exception as e:
    logger.error(f'Error initializing Gemini client: {str(e)}')
    raise

# Load image classification model
try:
    image_model = load_model(os.path.join(os.path.dirname(__file__), "../model/Rhamnus_model.h5"))
    logger.info('@@ Model loaded successfully')
except Exception as e:
    logger.error(f'Error loading model: {str(e)}')
    raise

# Set upload folder path
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '../frontend/static/user_uploaded')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Create Flask instance
app = Flask(__name__, template_folder='../frontend/templates', static_folder='../frontend/static')
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
app.secret_key = '8f507b86c6df4216b68f147eac952b91'

# Add document mapping
class_docs = {
    "Healthy": os.path.join('../frontend/static/docs', 'Healthy_Doc.docx'),
    "Powdery": os.path.join('../frontend/static/docs', 'Powdery_Doc.docx'),
    "Rust": os.path.join('../frontend/static/docs', 'Rust_Doc.docx'),
    "error": None
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def pred_the_detection(detection):
    try:
        test_image = load_img(detection, target_size=(225, 225))
        logger.info("@@ Got Image for prediction")

        test_image = img_to_array(test_image) / 255
        test_image = np.expand_dims(test_image, axis=0)

        result = image_model.predict(test_image).round(3)
        logger.info(f'@@ Raw result = {result}')

        pred = np.argmax(result)

        if pred == 0:
            return "Healthy", "Healthy_Doc.docx"
        elif pred == 1:
            return "Powdery", "Powdery_Doc.docx"
        elif pred == 2:
            return "Rust", "Rust_Doc.docx"
        else:
            return "error", None
    except Exception as e:
        logger.error(f'Error in prediction: {str(e)}')
        return "error", None

@app.route("/")
def home():
    return render_template('index.html')

@app.route("/predict", methods=['POST'])
def predict():
    logger.info(f"Request files: {request.files}")
    logger.info(f"Request form data: {request.form}")
    
    if 'image' not in request.files:
        logger.error("No image file in request")
        flash('No file part')
        return redirect(request.url)

    file = request.files['image']
    logger.info(f"Filename: {file.filename}")
    
    if file.filename == '':
        logger.error("Empty filename")
        flash('No selected file')
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)

        try:
            file.save(file_path)
            logger.info(f"@@ Saved file path: {file_path}")

            pred_label, doc_file = pred_the_detection(detection=file_path)
            logger.info(f"Prediction result: {pred_label}, doc: {doc_file}")

            if pred_label == "error":
                logger.error("Error in prediction result")
                flash('Error processing the image. Please try again.')
                return redirect('/')

            return render_template('predict.html',
                                pred_output=pred_label,
                                doc_file=doc_file,
                                user_image=f'user_uploaded/{filename}',
                                chat_history=chat_history)  # Pass chat history to template

        except Exception as e:
            logger.error(f'Error saving or processing file: {str(e)}')
            flash('Error processing the image. Please try again.')
            return redirect('/')

    logger.error(f"Invalid file type: {file.filename}")
    flash('Invalid file type. Please upload a PNG, JPG, or JPEG image.')
    return redirect('/')

# Add document download route
@app.route("/download/<filename>")
def download(filename):
    try:
        doc_path = os.path.join(os.path.dirname(__file__), '../frontend/static/docs', secure_filename(filename))
        if os.path.exists(doc_path):
            return send_file(doc_path, as_attachment=True)
        else:
            flash('Report not found')
            return redirect('/')
    except Exception as e:
        logger.error(f'Error downloading file: {str(e)}')
        flash('Error downloading report')
        return redirect('/')

# Add document view route
@app.route("/view_document")
def view_document():
    doc_file = request.args.get('doc_file')
    if not doc_file:
        logger.error("No document file specified")
        return render_template('view_document.html', doc_content=["No report available"])

    try:
        # Print the exact filenames in the docs directory
        docs_dir = os.path.join(os.path.dirname(__file__), '../frontend/static/docs')
        logger.info(f"Files in docs directory: {os.listdir(docs_dir)}")

        doc_path = os.path.join(os.path.dirname(__file__), '../frontend/static/docs', secure_filename(doc_file))
        logger.info(f"Looking for document at: {doc_path}")

        if not os.path.exists(doc_path):
            logger.error(f"Document not found: {doc_path}")
            return render_template('view_document.html',
                                doc_content=[f"Report not found. Looking for: {doc_file}"])

        doc = docx.Document(doc_path)
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]

        if not paragraphs:
            logger.warning(f"Document is empty: {doc_path}")
            return render_template('view_document.html',
                                doc_content=["No content available in the report."])

        return render_template('view_document.html', doc_content=paragraphs)

    except Exception as e:
        logger.error(f'Error reading document: {str(e)}')
        return render_template('view_document.html',
                            doc_content=[f"Error viewing report: {str(e)}"])

@app.route("/chat", methods=['GET', 'POST'])
def chat_endpoint():
    if request.method == 'POST':
        try:
            user_message = request.json.get('message')

            if not user_message:
                return jsonify({"error": "No message provided"}), 400

            logger.info(f"Received message: {user_message}")
            
            # Detect language request in the message
            language = 'en'  # Default to English
            
            # Check for explicit language requests
            lower_message = user_message.lower()
            if any(term in lower_message for term in ['hindi', 'in hindi']):
                language = 'hi'
                logger.info("Language detected: Hindi")
            elif any(term in lower_message for term in ['marathi', 'in marathi']):
                language = 'mr'
                logger.info("Language detected: Marathi")
            
            # Determine question type for better formatting
            question_type = "general"
            if any(term in lower_message for term in ['what is', 'what are', 'meaning', 'definition', 'define']):
                question_type = "definition"
                logger.info("Question type: Definition")
            elif any(term in lower_message for term in ['treatment', 'cure', 'fix', 'heal', 'remedy', 'pesticide', 'fungicide', 'solution', 'prevent', 'control']):
                question_type = "treatment"
                logger.info("Question type: Treatment")
            elif any(term in lower_message for term in ['symptom', 'identify', 'diagnose', 'sign', 'look like', 'appear']):
                question_type = "symptoms"
                logger.info("Question type: Symptoms")
            
            # Build context with previous messages if available
            context = ""
            if chat_history:
                for entry in chat_history[-2:]:  # Last 2 messages for context
                    context += f"User: {entry['user']}\nAssistant: {entry['bot']}\n\n"
            
            # Create prompt with context and formatting instructions based on question type
            format_instructions = ""
            if question_type == "definition":
                format_instructions = """
                Answer in 2-3 concise sentences ONLY. Be brief but informative and simple to understand.
                DO NOT provide a lengthy explanation. 
                """
            elif question_type == "treatment":
                format_instructions = """
                Provide a numbered list of 4-5 specific treatments or preventive measures.
                For each item, include the name of the product or method followed by a brief explanation.
                Format as:
                1. [Product/Method]: Brief 1-2 line explanation
                2. [Product/Method]: Brief 1-2 line explanation
                ...
                """
            elif question_type == "symptoms":
                format_instructions = """
                List 3-5 key symptoms in bullet points.
                Be specific about appearance, location, and progression.
                Format as:
                • Symptom 1
                • Symptom 2
                ...
                """
            else:
                format_instructions = """
                Be concise and simple to understand the point. 
                Provide a direct answer in 2-3 sentences maximum.
                """
            
            # Create prompt with context, language instruction, and formatting instructions
            prompt = f"""
            {context}
            
            You are an agricultural expert specializing in plant diseases and crop health.
            Answer the following question about farming.
            
            {format_instructions}
            
            Respond in the {'English' if language == 'en' else 'Hindi' if language == 'hi' else 'Marathi'} language.
            
            Question: {user_message}
            """
            
            # Send prompt to Gemini API
            response = gemini_client.models.generate_content(
                model="gemini-3-flash-preview", 
                contents=prompt
            )
            response_text = response.text
            
            logger.info(f"Generated response in {language} (first 100 chars): {response_text[:100]}...")
            
            # Add to chat history
            chat_history.append({
                "user": user_message,
                "bot": response_text
            })

            return jsonify({
                'response': response_text,
                'status': 'success'
            })

        except Exception as e:
            logger.error(f"Chat error: {str(e)}")
            return jsonify({
                'response': 'I apologize for the technical difficulty. Please try asking your question again.',
                'status': 'partial'
            })

    return render_template('predict.html', chat_history=chat_history)

if __name__ == "__main__":
    app.run(threaded=False, debug=True)

