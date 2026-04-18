from src.nlp.pipeline import lematizar
from typing import Optional

LEMAS_HUMOR = {
    "animado":   [lematizar(p) for p in ["animado","empolgado","energia","agitado","feliz","bem","otimo","ótimo"]],
    "calmo":     [lematizar(p) for p in ["calmo","relaxado","tranquilo","sossegado","descansando"]],
    "entediado": [lematizar(p) for p in ["entediado","tedio","chato","sem","fazer","enfadado"]],
    "assustado": [lematizar(p) for p in ["assustado","medo","nervoso","tenso","ansioso"]],
    "romantico": [lematizar(p) for p in ["romantico","apaixonado","amor","namorado","namorada","sentimental"]],
    "curioso":   [lematizar(p) for p in ["curioso","pensativo","refletindo","interessado","intrigado"]],
    "triste":    [lematizar(p) for p in ["triste","melancólico","melancolico","mal","deprimido","chateado"]],
}

LEMAS_ACOMPANHADO = {
    "sozinho": [lematizar(p) for p in ["sozinho","solo","so"]],
    "amigos":  [lematizar(p) for p in ["amigos","amigo","galera","turma","pessoal","amiga"]],
    "casal":   [lematizar(p) for p in ["casal","namorado","namorada","esposo","esposa","parceiro","parceira"]],
    "familia": [lematizar(p) for p in ["familia","filho","filha","pai","mae","crianca","filhos","família"]],
}

LEMAS_DURACAO = {
    "curto": [lematizar(p) for p in ["curto","rapido","rápido","pequeno","pouco","curtinho","90"]],
    "medio": [lematizar(p) for p in ["medio","médio","normal","moderado","tanto"]],
    "longo": [lematizar(p) for p in ["longo","longa","demorado","grande","muito","comprido","2h","3h"]],
}

LEMAS_DISPOSICAO = {
    "pensar": [lematizar(p) for p in ["pensar","refletir","profundo","inteligente","complexo","denso","cerebral"]],
    "curtir": [lematizar(p) for p in ["curtir","desligar","relaxar","entretenimento","leve","divertir","besteira"]],
}

_MAPA_CAMPOS = {
    "humor":             LEMAS_HUMOR,
    "acompanhado":       LEMAS_ACOMPANHADO,
    "duracao_preferida": LEMAS_DURACAO,
    "disposicao":        LEMAS_DISPOSICAO,
}

def detectar_valor_campo(campo: str, tokens, lemas) -> Optional[str]:
    for valor, lemas_valor in _MAPA_CAMPOS.get(campo, {}).items():
        for lema in lemas:
            if lema in lemas_valor:
                return valor
    return None