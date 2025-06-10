from utils.db_models import *
import requests


def event_to_dict(evento):
    return {
        "id_evento": evento.id_evento,
        "titulo": evento.titulo,
        "descricao": evento.descricao,
        "local": evento.local,
        "data_inicio": evento.data_inicio.strftime('%Y-%m-%d'),
        "data_fim": evento.data_fim.strftime('%Y-%m-%d'),
        "vagas": evento.vagas,
        "online": evento.online,  # Add this line
        "organizador": evento.organizador.nome if evento.organizador else None,
        "atividades": [
            {
                "titulo": at.titulo,
                "descricao": at.descricao,
                "duracao_minutos": at.duracao_minutos,
                "tipo": at.tipo.nome if at.tipo else None,
                "data_hora": at.data_hora.strftime('%d/%m/%YT%H:%M') if at.data_hora else None
            }
            for at in Atividade.query.filter_by(id_evento=evento.id_evento).all()
        ]
    }


def upload_image_to_imgbb(image_file):
    API_KEY = 'c47a70773b3c1c0ea59b33d6d65add83'
    url = "https://api.imgbb.com/1/upload"

    payload = {
        "key": API_KEY
    }

    files = {
        "image": (image_file.filename, image_file.stream, image_file.mimetype)
    }

    response = requests.post(url, data=payload, files=files)

    if response.status_code == 200:
        print(response.json()['data']['url'])
        return response.json()['data']['url']
    else:
        print("Upload failed:", response.text)
        return None


