from flask import (
    Blueprint, render_template, request, jsonify
)
import json
from sqlalchemy import desc

# Importa o objeto 'db' e os Models
from . import db, LeiturasSensores, Configuracao 

main_bp = Blueprint('main', __name__)

# --- FUNÇÃO AUXILIAR PARA PEGAR DADOS ---
def _get_dashboard_data():
    """Busca os dados mais recentes do banco para o dashboard."""
    # 1. Buscar os últimos 100 registros para gráficos e tabela
    ultimas_leituras = LeiturasSensores.query.order_by(
        LeiturasSensores.data_hora.desc()
    ).limit(100).all()

    # 2. Buscar a configuração atual (a linha com id=1)
    config_atual = Configuracao.query.get(1) 
    # Se config_atual for None (ex: tabela vazia), criamos um objeto padrão temporário
    if not config_atual:
        config_atual = Configuracao(id=1, modo='AUTOMATICO', setpoint_umidade=60.0, comando_manual_bomba=False)
        print("AVISO: Tabela 'configuracao' vazia ou sem id=1. Usando valores padrão.")

    return ultimas_leituras, config_atual

# --- ROTAS PRINCIPAIS (PÁGINAS) ---

@main_bp.route('/')
def dashboard():
    """ Rota principal que exibe o painel de controle (index.html) """
    try:
        ultimas_leituras, config_atual = _get_dashboard_data()
        
        # 3. Preparar dados para os gráficos (invertendo a ordem)
        leituras_invertidas = ultimas_leituras[::-1]
        lista_umid_solo = [float(r.umidade_solo) for r in leituras_invertidas]
        lista_luz = [float(r.luminosidade) for r in leituras_invertidas]

        vl_umid_solo = json.dumps(lista_umid_solo)
        vl_luz = json.dumps(lista_luz)

        # Convertendo objetos para dicionários para o template
        resultados_dict = [
            {'id': r.id, 'umidade_solo': r.umidade_solo, 'luminosidade': r.luminosidade, 
             'estado_bomba': r.estado_bomba, 'data_hora': r.data_hora} 
            for r in ultimas_leituras
        ]
        config_dict = {
            'id': config_atual.id, 'modo': config_atual.modo, 
            'setpoint_umidade': config_atual.setpoint_umidade, 
            'comando_manual_bomba': config_atual.comando_manual_bomba
        }

        return render_template(
            'index.html',
            resultados=resultados_dict,
            config=config_dict,
            vl_umid_solo=vl_umid_solo,
            vl_luz=vl_luz
        )
    except Exception as e:
        print(f"Erro na rota dashboard: {e}")
        return f"Ocorreu um erro ao carregar o dashboard: {e}", 500


@main_bp.route('/grupo/')
def grupo():
    """ Rota para a página de contatos/grupo """
    return render_template('grupo.html')


# --- ROTAS DE API (PARA JAVASCRIPT E ESP8266) ---

# --- (NOVO!) ROTA PARA ATUALIZAÇÃO DO DASHBOARD ---
@main_bp.route('/api/dashboard-data')
def get_dashboard_data_api():
    """
    API para o JavaScript do frontend (AJAX Polling) buscar 
    os dados mais recentes em formato JSON.
    """
    try:
        ultimas_leituras, config_atual = _get_dashboard_data()

        # Prepara dados para os gráficos
        leituras_invertidas = ultimas_leituras[::-1]
        lista_umid_solo = [float(r.umidade_solo) for r in leituras_invertidas]
        lista_luz = [float(r.luminosidade) for r in leituras_invertidas]

        # Prepara dados para os cards de status (a leitura MAIS recente)
        status_recente = {}
        if ultimas_leituras:
            leitura_recente = ultimas_leituras[0] # O primeiro é o mais recente
            status_recente = {
                'umidade_solo': "%.1f" % leitura_recente.umidade_solo,
                'luminosidade': "%.0f" % leitura_recente.luminosidade,
                'data_hora': leitura_recente.data_hora.strftime('%d/%m/%Y %H:%M:%S')
            }
        
        # Prepara dados de configuração (para sincronizar os botões)
        config_dict = {
            'modo': config_atual.modo,
            'setpoint_umidade': config_atual.setpoint_umidade,
            'comando_manual_bomba': config_atual.comando_manual_bomba
        }

        # Retorna tudo em um grande JSON
        return jsonify(
            status="ok",
            grafico_umidade=lista_umid_solo,
            grafico_luz=lista_luz,
            status_recente=status_recente,
            configuracao=config_dict
        )
    except Exception as e:
        print(f"Erro na API /api/dashboard-data: {e}")
        return jsonify(status="erro", mensagem=str(e)), 500


@main_bp.route('/api/dados', methods=['POST'])
def receber_dados_esp32():
    """
    API para o ESP8266 enviar dados dos sensores.
    Responde com a configuração atual.
    """
    try:
        dados = request.json
        nova_leitura = LeiturasSensores(
            umidade_solo=dados.get('umidade'),
            luminosidade=dados.get('luz'),
            estado_bomba=bool(dados.get('bomba_ligada'))
        )
        db.session.add(nova_leitura)
        db.session.commit()

        config = Configuracao.query.get(1)
        if config:
            config_dict = {
                "modo": config.modo,
                "setpoint": float(config.setpoint_umidade),
                "comando_manual": int(config.comando_manual_bomba) 
            }
            return jsonify(config_dict)
        else:
            return jsonify({"status": "erro", "mensagem": "Config not found"}), 404
    except Exception as e:
        db.session.rollback()
        print(f"Erro na API /api/dados: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500


@main_bp.route('/api/config', methods=['POST'])
def atualizar_config_site():
    """
    API para o site (Javascript) enviar atualizações de controle.
    """
    try:
        dados = request.json
        chave = dados.get('chave')
        valor = dados.get('valor')

        config = Configuracao.query.get(1)
        if not config:
            return jsonify({"status": "erro", "mensagem": "Configuração não encontrada"}), 404

        if chave == 'modo':
            config.modo = valor
        elif chave == 'setpoint':
            config.setpoint_umidade = float(valor)
        elif chave == 'comando_manual':
            config.comando_manual_bomba = bool(int(valor))
        else:
            return jsonify({"status": "erro", "mensagem": "Chave inválida"}), 400
            
        db.session.commit()
        return jsonify({"status": "ok", "mensagem": f"{chave} atualizado para {valor}"})
    except Exception as e:
        db.session.rollback()
        print(f"Erro na API /api/config: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500