import os
from flask import Flask, request, send_file
from flask_cors import CORS
from groq import Groq
import ffmpeg

app = Flask(__name__)
CORS(app) # Permite que o seu site converse com este servidor

# Conecta na IA gratuita da Groq
client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

@app.route('/processar-video', methods=['POST'])
def processar_video():
    if 'video' not in request.files:
        return "Nenhum vídeo enviado", 400
        
    video = request.files['video']
    video.save("original.mp4")

    try:
        # Passo 1: Extrair o áudio do vídeo para a IA escutar
        ffmpeg.input("original.mp4").output("audio.mp3").run(overwrite_output=True)

        # Passo 2: Enviar para o Whisper (Groq) e pedir formato SRT
        with open("audio.mp3", "rb") as file:
            transcricao = client.audio.transcriptions.create(
              file=("audio.mp3", file.read()),
              model="whisper-large-v3",
              response_format="srt", # Pede o tempo exato das palavras
            )

        # Salva o texto sincronizado
        with open("legenda.srt", "w") as srt_file:
            srt_file.write(transcricao)

        # Passo 3: Juntar o vídeo original com a legenda SRT
        ffmpeg.input("original.mp4").output(
            "video_legendado.mp4", 
            vf="subtitles=legenda.srt:force_style='Fontname=Arial,Fontsize=24,PrimaryColour=&H00FFFF,Bold=1'"
        ).run(overwrite_output=True)

        return send_file("video_legendado.mp4", as_attachment=True)

    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)
          
