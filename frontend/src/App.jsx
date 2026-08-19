import { useEffect, useState } from 'react';

const API_BASE = 'http://127.0.0.1:8000';

const INITIAL_AVALIACAO_PAYLOAD = {
  data_avaliacao: '',
  forca_quadriceps_isquiotibiais: {
    quadriceps_1rm_d: '',
    quadriceps_1rm_e: '',
    isquiotibiais_1rm_d: '',
    isquiotibiais_1rm_e: '',
  },
  core: {
    extensores_tronco_s: '',
    prancha_lateral_d_s: '',
    prancha_lateral_e_s: '',
  },
  mobilidade_quadril: {
    quadril_d_graus: '',
    quadril_e_graus: '',
  },
  mobilidade_tornozelo: {
    lunge_d_graus: '',
    lunge_e_graus: '',
  },
  adm_passiva_ombro: {
    rotacao_externa_d: '',
    rotacao_interna_d: '',
    rotacao_externa_e: '',
    rotacao_interna_e: '',
    atleta_arremesso: false,
  },
  adm_ativa_ombro: {
    rotacao_interna_d: '',
    rotacao_interna_e: '',
    rotacao_externa_d: '',
    rotacao_externa_e: '',
  },
  single_hop: {
    media_mid_cm: '',
    media_mie_cm: '',
  },
  preensao_palmar: {
    direita_kgf: '',
    esquerda_kgf: '',
  },
  flexo_aducao_ombro: {
    flexao_passiva_d: '',
    flexao_passiva_e: '',
    aducao_horizontal_d: '',
    aducao_horizontal_e: '',
  },
  escala_carga_recuperacao: {
    treino: '',
    estado_fisico: '',
    prontidao_sono: '',
    dor: '',
  },
  y_balance: {
    comprimento_mid_cm: '',
    comprimento_mie_cm: '',
    anterior_mid: '',
    posteromedial_mid: '',
    posterolateral_mid: '',
    anterior_mie: '',
    posteromedial_mie: '',
    posterolateral_mie: '',
  },
};

function App() {
  const [pacientes, setPacientes] = useState([]);
  const [novoPaciente, setNovoPaciente] = useState({
    nome: '',
    data_nascimento: '',
    sexo: '',
    email: '',
    telefone: '',
  });
  const [pacienteSelecionado, setPacienteSelecionado] = useState(null);
  const [avaliacaoPayload, setAvaliacaoPayload] = useState(INITIAL_AVALIACAO_PAYLOAD);
  const [avaliacoes, setAvaliacoes] = useState([]);
  const [resultado, setResultado] = useState(null);
  const [mensagem, setMensagem] = useState('');

  const Section = ({ title, description, children }) => (
    <div className="section-card">
      <div className="section-card-header">
        <h2>{title}</h2>
        {description ? <p className="section-card-description">{description}</p> : null}
      </div>
      {children}
    </div>
  );

  useEffect(() => {
    fetch(`${API_BASE}/pacientes`)
      .then((res) => res.json())
      .then(setPacientes)
      .catch(() => setMensagem('Erro ao carregar pacientes'));
  }, []);

  const criarPaciente = async (event) => {
    event.preventDefault();

    const response = await fetch(`${API_BASE}/pacientes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(novoPaciente),
    });

    if (!response.ok) {
      setMensagem('Falha ao criar paciente');
      return;
    }

    const paciente = await response.json();
    setPacientes((prev) => [...prev, paciente]);
    setNovoPaciente({ nome: '', data_nascimento: '', sexo: '', email: '', telefone: '' });
    setMensagem('Paciente criado com sucesso');
  };

  const buscarAvaliacoes = async (pacienteId) => {
    const response = await fetch(`${API_BASE}/pacientes/${pacienteId}/avaliacoes`);
    if (!response.ok) {
      setMensagem('Falha ao carregar avaliações');
      return;
    }

    const dados = await response.json();
    const paciente = pacientes.find((item) => item.id === pacienteId) || null;
    setAvaliacoes(dados);
    setPacienteSelecionado(paciente);
    setResultado(null);
  };

  const criarAvaliacao = async (event) => {
    event.preventDefault();

    if (!pacienteSelecionado) {
      setMensagem('Selecione um paciente antes de criar a avaliação');
      return;
    }

    const payloadToSend = buildPayload(avaliacaoPayload);

    const response = await fetch(`${API_BASE}/pacientes/${pacienteSelecionado.id}/avaliacoes`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payloadToSend),
    });

    if (!response.ok) {
      setMensagem('Falha ao criar avaliação');
      return;
    }

    const dados = await response.json();
    setResultado(dados);
    setAvaliacaoPayload(INITIAL_AVALIACAO_PAYLOAD);
    buscarAvaliacoes(pacienteSelecionado.id);
    setMensagem('Avaliação criada com sucesso');
  };

  function isValueFilled(value) {
    if (value === null || value === undefined) return false;
    if (typeof value === 'string') return value.trim() !== '';
    if (typeof value === 'number') return true; // 0 is a valid value
    if (typeof value === 'boolean') return value === true; // only true counts as filled
    if (Array.isArray(value)) return value.length > 0;
    if (typeof value === 'object') return Object.values(value).some(isValueFilled);
    return false;
  }

  function buildPayload(full) {
    const out = {};
    // always include date if present
    if (full.data_avaliacao) out.data_avaliacao = full.data_avaliacao;

    Object.keys(full).forEach((k) => {
      if (k === 'data_avaliacao') return;
      const val = full[k];
      if (isValueFilled(val)) {
        out[k] = val;
      }
    });
    return out;
  }

  const baixarLaudo = (avaliacaoId) => {
    window.open(`${API_BASE}/avaliacoes/${avaliacaoId}/laudo`, '_blank');
  };

  const handleNovoPacienteCampo = (campo) => (event) => {
    setNovoPaciente((prev) => ({ ...prev, [campo]: event.target.value }));
  };

  const handleCampo = (grupo, campo) => (event) => {
    setAvaliacaoPayload((prev) => ({
      ...prev,
      [grupo]: {
        ...prev[grupo],
        [campo]: event.target.type === 'number' ? (event.target.value === '' ? '' : Number(event.target.value)) : event.target.value,
      },
    }));
  };

  const handleCheckbox = (grupo, campo) => (event) => {
    setAvaliacaoPayload((prev) => ({
      ...prev,
      [grupo]: {
        ...prev[grupo],
        [campo]: event.target.checked,
      },
    }));
  };

  return (
    <div className="app-container">
      <header className="page-header">
        <div>
          <p className="eyebrow">Funcional.e Fisioterapia Esportiva</p>
          <h1>Avaliação de risco funcional</h1>
          <p className="page-subtitle">
            Gerencie pacientes, registre avaliações parciais e baixe laudos em PDF com facilidade.
          </p>
        </div>
        <div className="header-stats">
          <div>
            <span>{pacientes.length}</span>
            <p>pacientes cadastrados</p>
          </div>
          <div>
            <span>{pacienteSelecionado ? pacienteSelecionado.nome : 'Nenhum selecionado'}</span>
            <p>paciente ativo</p>
          </div>
        </div>
      </header>

      <div className="top-grid">
        <Section title="Cadastro de paciente" description="Inclua novos pacientes antes de registrar avaliações.">
          <form onSubmit={criarPaciente} className="form-grid form-grid-compact">
            <label>
              Nome
              <input value={novoPaciente.nome} onChange={handleNovoPacienteCampo('nome')} required />
            </label>
            <label>
              Data de nascimento
              <input type="datetime-local" value={novoPaciente.data_nascimento} onChange={handleNovoPacienteCampo('data_nascimento')} />
            </label>
            <label>
              Sexo
              <input value={novoPaciente.sexo} onChange={handleNovoPacienteCampo('sexo')} />
            </label>
            <label>
              Email
              <input type="email" value={novoPaciente.email} onChange={handleNovoPacienteCampo('email')} />
            </label>
            <label>
              Telefone
              <input type="tel" value={novoPaciente.telefone} onChange={handleNovoPacienteCampo('telefone')} />
            </label>
            <button type="submit" className="button button-primary">
              Criar paciente
            </button>
          </form>
        </Section>

        <Section title="Lista de pacientes" description="Selecione um paciente para registrar e consultar avaliações">
          <div className="paciente-list">
            {pacientes.map((paciente) => (
              <button
                key={paciente.id}
                type="button"
                className={pacienteSelecionado?.id === paciente.id ? 'active' : 'secondary'}
                onClick={() => buscarAvaliacoes(paciente.id)}
              >
                {paciente.nome}
              </button>
            ))}
          </div>
        </Section>
      </div>

      <Section title="Nova avaliação" description="Preencha apenas os campos disponíveis para esta sessão.">
        <form onSubmit={criarAvaliacao} className="form-grid">
          <div className="field-group-full">
            <label>
              Data da avaliação
              <input
                type="datetime-local"
                value={avaliacaoPayload.data_avaliacao}
                onChange={(event) => setAvaliacaoPayload((prev) => ({ ...prev, data_avaliacao: event.target.value }))}
                required
              />
            </label>
          </div>

          <fieldset>
            <legend>Força QD/IT</legend>
            <div className="form-grid form-grid-compact">
              <label>
                QD 1RM
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.forca_quadriceps_isquiotibiais.quadriceps_1rm_d}
                  onChange={handleCampo('forca_quadriceps_isquiotibiais', 'quadriceps_1rm_d')}
                />
              </label>
              <label>
                QE 1RM
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.forca_quadriceps_isquiotibiais.quadriceps_1rm_e}
                  onChange={handleCampo('forca_quadriceps_isquiotibiais', 'quadriceps_1rm_e')}
                />
              </label>
              <label>
                ITD 1RM
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.forca_quadriceps_isquiotibiais.isquiotibiais_1rm_d}
                  onChange={handleCampo('forca_quadriceps_isquiotibiais', 'isquiotibiais_1rm_d')}
                />
              </label>
              <label>
                ITE 1RM
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.forca_quadriceps_isquiotibiais.isquiotibiais_1rm_e}
                  onChange={handleCampo('forca_quadriceps_isquiotibiais', 'isquiotibiais_1rm_e')}
                />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Core</legend>
            <div className="form-grid form-grid-compact">
              <label>
                Extensores tronco (s)
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.core.extensores_tronco_s}
                  onChange={handleCampo('core', 'extensores_tronco_s')}
                />
              </label>
              <label>
                Prancha lateral D (s)
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.core.prancha_lateral_d_s}
                  onChange={handleCampo('core', 'prancha_lateral_d_s')}
                />
              </label>
              <label>
                Prancha lateral E (s)
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.core.prancha_lateral_e_s}
                  onChange={handleCampo('core', 'prancha_lateral_e_s')}
                />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Mobilidade</legend>
            <div className="form-grid form-grid-compact">
              <label>
                Quadril D (º)
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.mobilidade_quadril.quadril_d_graus}
                  onChange={handleCampo('mobilidade_quadril', 'quadril_d_graus')}
                />
              </label>
              <label>
                Quadril E (º)
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.mobilidade_quadril.quadril_e_graus}
                  onChange={handleCampo('mobilidade_quadril', 'quadril_e_graus')}
                />
              </label>
              <label>
                Lunge D (º)
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.mobilidade_tornozelo.lunge_d_graus}
                  onChange={handleCampo('mobilidade_tornozelo', 'lunge_d_graus')}
                />
              </label>
              <label>
                Lunge E (º)
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.mobilidade_tornozelo.lunge_e_graus}
                  onChange={handleCampo('mobilidade_tornozelo', 'lunge_e_graus')}
                />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Ombro</legend>
            <div className="form-grid form-grid-compact">
              <label>
                Rot. Externa D (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_passiva_ombro.rotacao_externa_d} onChange={handleCampo('adm_passiva_ombro', 'rotacao_externa_d')} />
              </label>
              <label>
                Rot. Interna D (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_passiva_ombro.rotacao_interna_d} onChange={handleCampo('adm_passiva_ombro', 'rotacao_interna_d')} />
              </label>
              <label>
                Rot. Externa E (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_passiva_ombro.rotacao_externa_e} onChange={handleCampo('adm_passiva_ombro', 'rotacao_externa_e')} />
              </label>
              <label>
                Rot. Interna E (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_passiva_ombro.rotacao_interna_e} onChange={handleCampo('adm_passiva_ombro', 'rotacao_interna_e')} />
              </label>
              <label className="checkbox-label">
                <input type="checkbox" checked={avaliacaoPayload.adm_passiva_ombro.atleta_arremesso} onChange={handleCheckbox('adm_passiva_ombro', 'atleta_arremesso')} />
                Atleta de arremesso
              </label>
              <label>
                Rot. Interna D Ativa (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_ativa_ombro.rotacao_interna_d} onChange={handleCampo('adm_ativa_ombro', 'rotacao_interna_d')} />
              </label>
              <label>
                Rot. Interna E Ativa (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_ativa_ombro.rotacao_interna_e} onChange={handleCampo('adm_ativa_ombro', 'rotacao_interna_e')} />
              </label>
              <label>
                Rot. Externa D Ativa (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_ativa_ombro.rotacao_externa_d} onChange={handleCampo('adm_ativa_ombro', 'rotacao_externa_d')} />
              </label>
              <label>
                Rot. Externa E Ativa (º)
                <input type="number" step="any" value={avaliacaoPayload.adm_ativa_ombro.rotacao_externa_e} onChange={handleCampo('adm_ativa_ombro', 'rotacao_externa_e')} />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Função e recuperação</legend>
            <div className="form-grid form-grid-compact">
              <label>
                Direita (kgf)
                <input type="number" step="any" value={avaliacaoPayload.preensao_palmar.direita_kgf} onChange={handleCampo('preensao_palmar', 'direita_kgf')} />
              </label>
              <label>
                Esquerda (kgf)
                <input type="number" step="any" value={avaliacaoPayload.preensao_palmar.esquerda_kgf} onChange={handleCampo('preensao_palmar', 'esquerda_kgf')} />
              </label>
              <label>
                Flexão passiva D (º)
                <input type="number" step="any" value={avaliacaoPayload.flexo_aducao_ombro.flexao_passiva_d} onChange={handleCampo('flexo_aducao_ombro', 'flexao_passiva_d')} />
              </label>
              <label>
                Flexão passiva E (º)
                <input type="number" step="any" value={avaliacaoPayload.flexo_aducao_ombro.flexao_passiva_e} onChange={handleCampo('flexo_aducao_ombro', 'flexao_passiva_e')} />
              </label>
              <label>
                Adução D (º)
                <input type="number" step="any" value={avaliacaoPayload.flexo_aducao_ombro.aducao_horizontal_d} onChange={handleCampo('flexo_aducao_ombro', 'aducao_horizontal_d')} />
              </label>
              <label>
                Adução E (º)
                <input type="number" step="any" value={avaliacaoPayload.flexo_aducao_ombro.aducao_horizontal_e} onChange={handleCampo('flexo_aducao_ombro', 'aducao_horizontal_e')} />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Escala de carga e recuperação</legend>
            <div className="form-grid form-grid-compact">
              <label>
                Treino (0-10)
                <input type="number" min="0" max="10" step="1" value={avaliacaoPayload.escala_carga_recuperacao.treino} onChange={handleCampo('escala_carga_recuperacao', 'treino')} />
              </label>
              <label>
                Estado físico (0-10)
                <input type="number" min="0" max="10" step="1" value={avaliacaoPayload.escala_carga_recuperacao.estado_fisico} onChange={handleCampo('escala_carga_recuperacao', 'estado_fisico')} />
              </label>
              <label>
                Sono (0-10)
                <input type="number" min="0" max="10" step="1" value={avaliacaoPayload.escala_carga_recuperacao.prontidao_sono} onChange={handleCampo('escala_carga_recuperacao', 'prontidao_sono')} />
              </label>
              <label>
                Dor (0-10)
                <input type="number" min="0" max="10" step="1" value={avaliacaoPayload.escala_carga_recuperacao.dor} onChange={handleCampo('escala_carga_recuperacao', 'dor')} />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Performance</legend>
            <div className="form-grid form-grid-compact">
              <label>
                Média MID
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.single_hop.media_mid_cm}
                  onChange={handleCampo('single_hop', 'media_mid_cm')}
                />
              </label>
              <label>
                Média MIE
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.single_hop.media_mie_cm}
                  onChange={handleCampo('single_hop', 'media_mie_cm')}
                />
              </label>
            </div>
          </fieldset>

          <fieldset>
            <legend>Y Balance</legend>
            <div className="form-grid form-grid-compact">
              <label>
                Comprimento MID
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.comprimento_mid_cm}
                  onChange={handleCampo('y_balance', 'comprimento_mid_cm')}
                />
              </label>
              <label>
                Comprimento MIE
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.comprimento_mie_cm}
                  onChange={handleCampo('y_balance', 'comprimento_mie_cm')}
                />
              </label>
              <label>
                Anterior MID
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.anterior_mid}
                  onChange={handleCampo('y_balance', 'anterior_mid')}
                />
              </label>
              <label>
                Posteromedial MID
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.posteromedial_mid}
                  onChange={handleCampo('y_balance', 'posteromedial_mid')}
                />
              </label>
              <label>
                Posterolateral MID
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.posterolateral_mid}
                  onChange={handleCampo('y_balance', 'posterolateral_mid')}
                />
              </label>
              <label>
                Anterior MIE
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.anterior_mie}
                  onChange={handleCampo('y_balance', 'anterior_mie')}
                />
              </label>
              <label>
                Posteromedial MIE
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.posteromedial_mie}
                  onChange={handleCampo('y_balance', 'posteromedial_mie')}
                />
              </label>
              <label>
                Posterolateral MIE
                <input
                  type="number"
                  step="any"
                  value={avaliacaoPayload.y_balance.posterolateral_mie}
                  onChange={handleCampo('y_balance', 'posterolateral_mie')}
                />
              </label>
            </div>
          </fieldset>

          <div className="button-row">
            <button type="submit" className="button button-primary">
              Criar avaliação
            </button>
          </div>
        </form>
      </Section>

      <Section title="Histórico de avaliações" description="Visualize e baixe os laudos dos últimos registros.">
        {pacienteSelecionado ? (
          <div>
            <p className="selected-paciente">Paciente selecionado: {pacienteSelecionado.nome}</p>
            {avaliacoes.length > 0 ? (
              <ul className="avaliacao-list">
                {avaliacoes.map((item) => (
                  <li key={item.avaliacao_id}>
                    <div>
                      <strong>{new Date(item.data_avaliacao).toLocaleString()}</strong>
                      <p>{item.nivel_risco_geral || 'Sem risco'}</p>
                    </div>
                    <button type="button" className="button button-secondary" onClick={() => baixarLaudo(item.avaliacao_id)}>
                      Baixar PDF
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <p>Nenhuma avaliação encontrada para este paciente.</p>
            )}
          </div>
        ) : (
          <p>Selecione um paciente para ver o histórico.</p>
        )}
      </Section>

      {resultado && (
        <Section title="Resultado da última avaliação">
          <pre>{JSON.stringify(resultado, null, 2)}</pre>
        </Section>
      )}

      {mensagem && <div className="toast">{mensagem}</div>}
    </div>
  );
}

export default App;
