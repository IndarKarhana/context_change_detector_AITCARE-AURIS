from flask import Flask, request, render_template, redirect, url_for, session, jsonify
import os
import io
from werkzeug.utils import secure_filename
import google.generativeai as gen_ai
import time
import soundfile
from google.cloud import speech
import random
import string

app = Flask(__name__)
app.secret_key = "Test"  # Change this to a real secret key in production

speech_to_text_client = None

def create_speech_to_text_client():
    global speech_to_text_client
    speech_to_text_client = speech.SpeechClient.from_service_account_json(os.path.join(os.getcwd(), "speech_to_text_credentials.json"))

def extract_pdf_pages(pathname: str) -> list[str]:
    parts = [f"--- START OF PDF ${pathname} ---"]
    with open(pathname,'r') as f:
        for index, page in enumerate(f.readlines()):
            parts.append(f"--- PAGE {index} ---")
            parts.append(page)
    return parts

def convert_audio_to_text(audio_file_path, sample_rate = None):
    if not speech_to_text_client:
        create_speech_to_text_client()
    config = speech.RecognitionConfig(
        encoding="LINEAR16",
        sample_rate_hertz=sample_rate if sample_rate else 16000,
        language_code="en-US",
    )
    # Set the audio source.
    with io.open(audio_file_path, "rb") as f:
        content = f.read()
    audio = speech.RecognitionAudio(content=content)
    # Send the request and get the response.
    response = speech_to_text_client.recognize(config=config, audio=audio)
    print(response.results)
    try:
        text = ""
        for result in response.results:
            text += result.alternatives[0].transcript
        return text
    except:
        return "Could not understand audio"

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in {'wav'}

generation_config = {
    "temperature": 0.1,
    "top_p": 0.95,
    "top_k": 0,
    "max_output_tokens": 8192,
}

system_instruction = "Don't include names from the conversation and try to be very precise with your answers and give very similar answers to examples given in the file. Don't go on adding details about the answer, just understand the questions and answers from examples in the file, and when answering for question in prompt use your understanding from examples from the file to answer the prompt question accurately like answers in examples and  follow this main prompt for every question- \"Detect where the context changed in the sentence and return that short part of the conversation like examples in file. If you don't find any change in the context then return \"No change\""

safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
]

@app.route('/', methods=['GET', 'POST'])
def index():
    if session.get('sid') == None:
        # Generate 12 random alphanumeric characters
        session['sid'] = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
    if request.method == 'POST':
        # <input type="hidden" name="action" value="save_google_speech_to_text_credential_json">
        if request.form.get('action') == 'save_google_speech_to_text_credential_json':
            session['google_speech_to_text_client_credential_json'] = request.form.get('google_speech_to_text_client_credential_json')
            # Create a file with the name key.json and write the content of the API key to it
            with open("speech_to_text_credentials.json", "w") as f:
                f.write(session['google_speech_to_text_client_credential_json'])
            return jsonify({'message': 'Google Speech to Text API Key stored successfully'})
        if request.form.get('action') == 'save_api_key':
            # Assuming a form field for the API key is named 'api_key'
            session['api_key'] = request.form.get('api_key')
            gen_ai.configure(api_key=session['api_key'])
            return jsonify({'message': 'API Key stored successfully'})
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    api_key = session.get('api_key', None)
    google_speech_to_text_client_credential_json = session.get('google_speech_to_text_client_credential_json', None)
    if not api_key:
        return jsonify({'error': 'API key is not set'})
    if google_speech_to_text_client_credential_json == None:
        return jsonify({'error': 'Google Speech to Text API Key is not set'})

    if request.method == 'GET':
        return render_template('index.html')

    if request.method == 'POST':
        # Check if the post request has the file part
        if 'audio_file' not in request.files:
            return redirect(request.url)
        audio_file = request.files['audio_file']

        if audio_file.filename == '':
            return redirect(request.url)

        if audio_file and allowed_file(audio_file.filename):
            # Make uploads folder if it doesn't exist
            if not os.path.exists('uploads'):
                os.makedirs('uploads')
            # Save audio file with name as the original filename+timestamp
            file_name = audio_file.filename.split('.wav')[0]+'_'+str(int(time.time()))+'.wav'
            audio_path = os.path.join('uploads', secure_filename(file_name))
            audio_file.save(audio_path)
            data, sample_rate = soundfile.read(audio_path)
            soundfile.write(audio_path, data, sample_rate, subtype='PCM_16')

            text_result = "could not understand"
            # Convert audio to text
            if google_speech_to_text_client_credential_json:
                text_result = convert_audio_to_text(audio_path, sample_rate)
            else:
                return jsonify({'error': 'Google Speech to Text API Key is not set'})
            print("*********************", text_result)
            #need to delete audio path
            if os.path.exists(audio_path):
                os.remove(audio_path)

            if api_key:
                model = gen_ai.GenerativeModel(model_name="gemini-1.5-pro-latest", generation_config=generation_config, system_instruction=system_instruction, safety_settings=safety_settings)

                conversation = model.start_chat(history=[
                    {"role": "user", "parts": extract_pdf_pages("/home/IndarKarhana/mysite/sample_data.txt")}
                ])
                conversation.send_message(text_result)

                last_response = conversation.last.candidates[0].content.parts[0].text
                #need to save response
                # Specify the file path where you want to append the text
                file_path = f"/home/IndarKarhana/mysite/response_output_{session['sid']}.txt"

                # Check if the file exists
                if not os.path.exists(file_path):
                    # If the file doesn't exist, create it and append the text
                    with open(file_path, 'w') as file:
                        file.write(last_response)
                else:
                    # If the file exists, append the text to its existing contents
                    with open(file_path, 'a') as file:
                        file.write(last_response)

                return jsonify({"transcription": text_result, "response": last_response})

            else:
                return jsonify({'error': 'API key is not set'})
    if request.method == 'GET':
        return render_template('index.html')

if __name__ == '__main__':
    app.run(debug=True)