# context_change_detector_AITCARE-AURIS

### Description

This Flask-based application utilizes Google's speech-to-text service and a generative AI model to transcribe audio files and generate conversational responses respectively. Users can upload audio files, which are then transcribed to text using Google's Speech-to-Text API. The transcribed text is then used as a prompt for the generative AI model, which generates a response based on the provided context.

### Prerequisites

Before running the application, ensure the following prerequisites are met:

- Python 3.x installed on your system
- Google Cloud Platform account with Speech-to-Text API enabled
- API key for Google Speech-to-Text service
- Generative AI API key

### Installation

1. Clone this repository to your local machine:

   ```
   git clone https://github.com/your_username/your_repository.git
   ```

2. Install the required dependencies:

   ```
   pip install -r requirements.txt
   ```

### Configuration

1. Obtain a Google Cloud Platform service account JSON file for the Speech-to-Text API and save it as `speech_to_text_credentials.json`.
2. Set up your Generative AI API key from Google AI studio.

### Demo

1. Access the application in your web browser at `https://indarkarhana.pythonanywhere.com/`.

### Usage Instructions

1. Set the Google Speech-to-Text API key and Generative AI API key via the web interface.
2. Upload an audio file in WAV format.
3. Wait for the transcription and AI-generated response.
4. The transcription and response will be displayed on the web interface.

### File Structure

- `app.py`: Main Flask application file.
- `index.html`: HTML template for the web interface.
- `requirements.txt`: List of Python dependencies.

### Notes

- Ensure that sensitive information such as API keys are stored securely.
- This application is for demonstration purposes and may require additional configuration for production use.
- The application is currently configured to run in debug mode. Ensure to disable debug mode in production environments.


### License

[MIT License](LICENSE)
