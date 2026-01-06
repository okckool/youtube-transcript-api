from flask import Flask, request, jsonify
from youtube_transcript_api import YouTubeTranscriptApi
from youtube_transcript_api._errors import TranscriptsDisabled, NoTranscriptFound
import re

app = Flask(__name__)

def extract_video_id(url):
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/)([^&\n?#]+)',
        r'youtube\.com\/shorts\/([^&\n?#]+)'
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

@app.route('/transcript', methods=['POST'])
def get_transcript():
    try:
        data = request.get_json()
        youtube_url = data.get('youtube_url')
        
        if not youtube_url:
            return jsonify({'error': 'youtube_url manquant'}), 400
        
        video_id = extract_video_id(youtube_url)
        if not video_id:
            return jsonify({'error': 'URL YouTube invalide'}), 400
        
        try:
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            # 1. Cherche français ou anglais
            try:
                transcript = transcript_list.find_transcript(['fr', 'en'])
            except:
                # 2. Prend n'importe quelle transcription
                transcript = next(iter(transcript_list))
            
            # 3. Traduit en français si nécessaire
            if transcript.language_code != 'fr':
                transcript = transcript.translate('fr')
            
            # 🔧 CORRECTION ICI : Récupère le texte complet
            full_text = ' '.join([entry['text'] for entry in transcript.fetch()])
            
            return jsonify({
                'success': True,
                'video_id': video_id,
                'transcript': full_text,
                'language': transcript.language_code
            })
            
        except TranscriptsDisabled:
            return jsonify({'error': 'Transcription désactivée'}), 404
        except NoTranscriptFound:
            return jsonify({'error': 'Aucune transcription disponible'}), 404
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000)
