from types import SimpleNamespace
from pathlib import Path
import sys, os

# garantir que o diretório do projeto esteja no sys.path quando executado a partir de scripts/
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.pdf_generator import gerar_laudo_pdf

Path("output").mkdir(exist_ok=True)

paciente = SimpleNamespace(nome="Fulano de Tal")

resultado_json = {
    "data_avaliacao": "2026-08-08",
    "indice_risco_geral": 42,
    "nivel_risco_geral": "moderado",
    "resultados": [
        {"nome_teste": "Mobilidade quadril - flexão", "valor_direito": 78, "valor_esquerdo": 72, "nivel_risco": "moderado", "conduta_fisioterapeutica": "Exercícios de flexibilidade"},
        {"nome_teste": "Mobilidade tornozelo - dorsiflexão", "valor_direito": 55, "valor_esquerdo": 50, "nivel_risco": "moderado", "conduta_fisioterapeutica": "Mobilização articular"},
        {"nome_teste": "Força quadríceps", "valor_direito": 88, "valor_esquerdo": 85, "nivel_risco": "baixo", "conduta_fisioterapeutica": "Treino de resistência"},
        {"nome_teste": "Y Balance Anterior", "valor_direito": 64, "valor_esquerdo": 62, "nivel_risco": "moderado", "conduta_fisioterapeutica": "Treino de equilíbrio"},
        {"nome_teste": "Salto unilateral", "valor_direito": 95, "valor_esquerdo": 93, "nivel_risco": "baixo"},
        {"nome_teste": "Core - prancha", "valor_direito": None, "valor_esquerdo": None, "assimetria_pct": 5, "nivel_risco": "baixo"}
    ],
}

out = Path("output") / "test_laudo.pdf"
gerar_laudo_pdf(out, paciente, resultado_json)
print(f"PDF gerado: {out}")
