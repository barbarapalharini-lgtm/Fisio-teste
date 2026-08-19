from __future__ import annotations

import sys
from pathlib import Path

from app.crud import get_avaliacao, get_paciente
from app.db import SessionLocal, init_db
from app.pdf_generator import gerar_laudo_pdf


def main() -> None:
    if len(sys.argv) < 2:
        print("Uso: python generate_laudo.py <avaliacao_id> [saida.pdf]")
        raise SystemExit(1)

    avaliacao_id = int(sys.argv[1])
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path(f"laudo_avaliacao_{avaliacao_id}.pdf")

    init_db()
    with SessionLocal() as db:
        avaliacao = get_avaliacao(db, avaliacao_id)
        if avaliacao is None:
            print(f"Avaliação {avaliacao_id} não encontrada.")
            raise SystemExit(1)

        paciente = get_paciente(db, avaliacao.paciente_id)
        if paciente is None:
            print(f"Paciente {avaliacao.paciente_id} não encontrado.")
            raise SystemExit(1)

        gerar_laudo_pdf(output_path, paciente, avaliacao.resultado_json)
        print(f"Laudo PDF gerado em: {output_path}")


if __name__ == "__main__":
    main()
