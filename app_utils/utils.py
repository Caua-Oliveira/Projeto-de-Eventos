
from app_utils.db_models import *

# --- SERIALIZERS ---
def evento_to_dict(evento):
    return {
        "id": evento.id_evento,
        "titulo": evento.titulo,
        "descricao": evento.descricao,
        "local": evento.local,
        "data_inicio": evento.data_inicio.strftime('%Y-%m-%d'),
        "data_fim": evento.data_fim.strftime('%Y-%m-%d'),
        "vagas": evento.vagas,
        "organizador": evento.organizador.nome if evento.organizador else None,
        "atividades": [
            {
                "id": at.id_atividade,
                "titulo": at.titulo,
                "data_hora": at.data_hora.strftime('%Y-%m-%dT%H:%M') if at.data_hora else None
            }
            for at in Atividade.query.filter_by(id_evento=evento.id_evento).all()
        ]
    }

