# Sistema de Avaliação de Risco de Lesões — Backend (cálculo de risco)

Esta é a primeira etapa do sistema: o "cérebro" que calcula assimetrias,
classifica riscos e sugere condutas fisioterapêuticas, replicando a lógica
que a fisioterapeuta já usa na planilha e no laudo da clínica funcional.e.

## Estrutura

```
app/
  calculations/
    reference_values.py   # valores de referência/normalidade de cada teste
    schemas.py             # modelos de entrada/saída (Pydantic)
    risk_calculator.py      # lógica de cálculo e classificação de risco
  tests/
    test_risk_calculator.py # testes validados com dados reais da Regiane
```

## Como rodar os testes

```bash
pip install -r requirements.txt
pytest app/tests/ -v
```

(Testes já foram validados manualmente neste ambiente e batem com os
valores do laudo em PDF fornecido — ex.: assimetria de quadríceps 42,05%,
razão QD/IT de 24,40%/15,26%, Single Hop ~12,9% etc.)

## API

A aplicação expõe uma API FastAPI em `app.main`.

Para rodar o servidor:

```bash
python -m uvicorn app.main:app --reload
```

### Endpoints principais

- `POST /pacientes` — cria paciente
- `GET /pacientes` — lista pacientes
- `GET /pacientes/{paciente_id}` — recupera um paciente
- `POST /pacientes/{paciente_id}/avaliacoes` — cria avaliação calculada
- `GET /pacientes/{paciente_id}/avaliacoes` — lista avaliações do paciente
- `GET /avaliacoes/{avaliacao_id}` — recupera avaliação específica

### Exemplo de payload para criar paciente

```json
{
  "nome": "Regiane Zaparoli",
  "data_nascimento": "1990-01-01T00:00:00",
  "sexo": "F",
  "email": "regiane@example.com",
  "telefone": "+55 11 99999-9999"
}
```

### Exemplo de payload para criar avaliação

```json
{
  "data_avaliacao": "2026-08-05T10:00:00",
  "forca_quadriceps_isquiotibiais": {
    "quadriceps_1rm_d": 20.16,
    "quadriceps_1rm_e": 34.79,
    "isquiotibiais_1rm_d": 4.92,
    "isquiotibiais_1rm_e": 5.31
  },
  "core": {
    "extensores_tronco_s": 135,
    "prancha_lateral_d_s": 60,
    "prancha_lateral_e_s": 60
  },
  "mobilidade_quadril": {
    "quadril_d_graus": 25,
    "quadril_e_graus": 30
  },
  "mobilidade_tornozelo": {
    "lunge_d_graus": 35,
    "lunge_e_graus": 30
  },
  "single_hop": {
    "media_mid_cm": 120,
    "media_mie_cm": 104.5
  },
  "y_balance": {
    "comprimento_mid_cm": 100,
    "comprimento_mie_cm": 100,
    "anterior_mid": 56,
    "posteromedial_mid": 77,
    "posterolateral_mid": 66,
    "anterior_mie": 53,
    "posteromedial_mie": 90,
    "posterolateral_mie": 74
  }
}
```

### Exemplo de comando curl

```bash
curl -X POST "http://127.0.0.1:8000/pacientes/1/avaliacoes" \
  -H "Content-Type: application/json" \
  -d @avaliacao.json
```

### Gerar laudo em PDF a partir de uma avaliação salva

- CLI: `python generate_laudo.py <avaliacao_id> [saida.pdf]`
- Endpoint: `GET /avaliacoes/{avaliacao_id}/laudo`

O endpoint retorna um arquivo PDF com o laudo gerado a partir do `resultado_json` da avaliação.

O laudo agora inclui:
- logo da `functional.e` no cabeçalho
- gráfico de barras com o risco de cada teste

## Frontend React/Vite

Dentro de `frontend/` há uma SPA que consome a API e permite:
- criar pacientes
- selecionar um paciente
- criar avaliações de risco
- listar avaliações do paciente
- baixar o PDF do laudo para cada avaliação

Para rodar o frontend:

```bash
cd frontend
npm install
npm run dev
```

O frontend deve ser acessível em `http://127.0.0.1:5173` e falar com o backend em `http://127.0.0.1:8000`.

## O que já está pronto

- Cálculo de assimetria entre lados (mesma fórmula da planilha:
  `100 - (menor/maior × 100)`)
- Classificação de risco (normal / moderado / alto) para:
  - Força de quadríceps e isquiotibiais + Razão QD/IT
  - Resistência do CORE (extensores de tronco, prancha lateral)
  - Mobilidade de quadril e tornozelo (Lunge test)
  - ADM passiva e ativa de rotação de ombro (GIRD)
  - Y Balance Test
  - Força simétrica genérica (dinamômetro isométrico — qualquer grupo
    muscular: glúteo médio, glúteo máximo, adutores etc.)
  - Single Hop Test
  - Força de preensão palmar
  - Flexão passiva / adução horizontal de ombro
  - Escala de carga e recuperação
- Texto de conduta fisioterapêutica sugerido automaticamente, no mesmo
  estilo do laudo, indicando o lado/grupo muscular a trabalhar.

## ⚠️ Pendência importante: índice de risco geral (o "medidor" do laudo)

O laudo da funcional.e mostra um índice final único, ex. **"50,9 ua — risco
moderado"**, que resume todos os testes num só medidor (vermelho/amarelo/
verde). **Não encontrei a fórmula desse índice na planilha** — ele parece
ser calculado à parte (talvez manualmente ou em outra ferramenta).

Implementei uma fórmula **provisória** (`_calcular_indice_risco_geral_provisorio`
em `risk_calculator.py`): cada teste NORMAL = 0 pontos, MODERADO = 50,
ALTO = 100, e o índice final é a média simples. Isso é só um placeholder —
precisa ser validado (ou substituído) com a fisioterapeuta, porque ela pode
querer dar pesos diferentes a testes diferentes (ex. testes de joelho podem
pesar mais que testes de ombro, dependendo da queixa do paciente).

## Próximos passos sugeridos

1. Validar com a fisioterapeuta a fórmula do índice de risco geral.
2. Modelo de dados / banco (paciente, histórico de avaliações ao longo do
   tempo).
3. API (FastAPI) expondo esses cálculos.
4. Geração automática do laudo em PDF (layout da funcional.e).
5. Frontend (formulário de entrada de dados, replicando a aba "Perfil de
   Risco" da planilha).
