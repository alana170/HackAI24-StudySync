import json
import os
from time import sleep
from flask import Flask, jsonify, redirect, request
from flask import render_template
from pdfminer.high_level import extract_text
from pdfminer.pdfdocument import PDFDocument
from werkzeug.utils import secure_filename
from haystack.nodes import QuestionGenerator, FARMReader
from haystack.pipelines import QuestionAnswerGenerationPipeline
from haystack.nodes import JsonConverter
from haystack import Document
from haystack.document_stores import ElasticsearchDocumentStore
from tqdm.auto import tqdm
import requests 
from haystack.pipelines import (
    QuestionGenerationPipeline,
    RetrieverQuestionGenerationPipeline,
    QuestionAnswerGenerationPipeline,
)
import spacy
from haystack.utils import launch_es, print_questions
from subprocess import Popen, PIPE, STDOUT
from gensim import corpora, models, similarities
import jieba
from flask_cors import CORS

"""
Google Colabs
Spacy: https://colab.research.google.com/drive/1xqV5d6AyC5k1CEcfxl8UsE4l8cw6sVr_?usp=sharing
Haystack: https://colab.research.google.com/drive/1rrqL1Smyw-efuss3e9HHquQlZBoqrLHG?usp=sharing
"""

app = Flask(__name__)
CORS(app)

if __name__ == '__main__':
    app.run(debug=True)

ALLOWED_EXTENSIONS = {'pdf'}
UPLOAD_FOLDER = 'uploads'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route("/")
def home():
    return render_template('index.html')

@app.route("/upload", methods=['GET','POST'])
def uploaded():

    if 'file' not in request.files:
        return redirect(request.url)

    file = request.files['file']

    if file.filename == '':
        return redirect(request.url)

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filepath = 'uploads/' + filename
        context = extract_text(filepath)

        '''
        url = "http://127.0.0.1:5000/upload"
        response = requests.get(url)
        if response.status_code == 200:
            try:
                # Try to parse the response content as JSON
                json_response = response.json()
                print(json_response)
            except ValueError:
                # Print an error message if parsing as JSON fails
                print("Error: Response content is not valid JSON")
        else:
            # Print an error message if the request was not successful
            print(f"Error: {response.status_code}")
        '''
        # localFilePath = "/Users/alanagorukanti/Desktop/HACK AI 24/uploads"
        # questions = (new_process_text(context, filepath))
        return render_template("content.html", filename = filename, contents = context)
                               
    else:
        error_message = "Invalid file type. Please upload a PDF file."
        return render_template('index.html', error_message=error_message)

'''
def get_questions(text):
    try:
        result = new_process_text(text)
        print(result)
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)})
'''

def process_text(text):
    print("HIIIII ")
    question_generator = QuestionGenerator()
    reader = FARMReader("deepset/roberta-base-squad2")
    qag_pipeline = QuestionAnswerGenerationPipeline(question_generator, reader)
    # Convert text to JSON format
    doc_json = [{"content": text}]
    json_string = json.dumps(doc_json)
    # Convert JSON string to JsonConverter object
    document_obj = JsonConverter().convert(json_string)
    # Run the Q&A pipeline
    result = qag_pipeline.run(documents=[document_obj])
    print("THIS IS RESULT !!!")
    print(result)
    return {'result': print_questions(result)}

def new_process_text(text, filepath):
    #launch_es()
    #sleep(31)

    docs = [{"content": text}]
    question_generator = QuestionGenerator()
    reader = FARMReader("deepset/roberta-base-squad2")
    qag_pipeline = QuestionAnswerGenerationPipeline(question_generator, reader)
    document = Document.from_json(docs)
    result = qag_pipeline.run(documents=[document])
    print(type(print_questions(result)))
    print(print_questions(result))
    #document_store = ElasticsearchDocumentStore()
    print("YAYYYYY")
    return result
    

    '''
    print(f"\n * Generating questions for document: {document.content[:10000000]}...\n")
    result = question_generation_pipeline.run(documents=[document])
    print_questions(result)

    return result 
    '''



    '''
    #es_server = Popen(
    #    ["elasticsearch-7.9.2/bin/elasticsearch"], stdout=PIPE, stderr=STDOUT, preexec_fn=lambda: os.setuid(1)  # as daemon
    #)
    # Initialize document store and write in the documents
    #document_store = ElasticsearchDocumentStore("localhost", 9200)
    #document_store.write_documents(docs)
    document_object = Document.from_json(docs)
    # Initialize Question Generator
    question_generator = QuestionGenerator()
    reader = FARMReader("deepset/roberta-base-squad2")
    qag_pipeline = QuestionAnswerGenerationPipeline(question_generator, reader)
    for idx, document in enumerate(tqdm(document_object)):

        print(f"\n * Generating questions and answers for document {idx}: {document.content[:100]}...\n")
        result = qag_pipeline.run(documents=[document])
        res = print_questions(result)
    
    return res
    # Convert text to JSON format
    #doc_json = [{"content": text}]

    #documents = [Document.from_dict(doc) for doc in doc_json]
    
    #json_string = json.dumps(doc_json)
    # Convert JSON string to JsonConverter objectdocuments = [Document.from_dict(doc) for doc in doc_json]

    # Run the Q&A pipeline
    #result = qag_pipeline.run(documents=[document_obj])
    #print("THIS IS RESULT !!!")
    #print(result)
    #return {'result': print_questions(result)}
    '''

@app.route("/about")
def about():
    return render_template('about.html')


@app.route("/study", methods=['POST'])
def study():
    if request.method == "POST":
        return render_template('study.html')
    return render_template('index.html') 

@app.route("/check_answer", methods=['POST'])
def compare_answers(str1, str2):
  # Load the English NLP model
    
    print("str1 = " , str1)
    print("str2 = " , str2)

    nlp = spacy.load("en_core_web_sm")

  # Define two strings

  # Process the strings with spaCy
    doc1 = nlp(str1)
    doc2 = nlp(str2)

    # Compute semantic similarity
    similarity_score = doc1.similarity(doc2)

    print("SIMILARITY = " , similarity_score)

    if similarity_score < 0.75:
        return jsonify({"result": "success", "message": "Correct answer!"})
    else:
        return jsonify({"result": "failure", "message": "Wrong answer!"})
