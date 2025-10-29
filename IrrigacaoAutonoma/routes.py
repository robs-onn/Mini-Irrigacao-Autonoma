from flask import (
    Blueprint, render_template, request, jsonify
)
import json
from sqlalchemy import desc # Para ordenar de forma decrescente

# Importa o objeto 'db' e os Models do __init__.py
from . import db, LeiturasSensores, Configuracao

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def dashboard():
    """ Rota principal que exibe o painel de controle (index.html) """
    try:
        # 1. Buscar os últimos 100 registros usando SQLAlchemy ORM
        #    Ordenando por data_hora decrescente
        ultimas_leituras = LeiturasSensores.query.order_by(
            LeiturasSensores.data_hora.desc() 
        ).limit(100).all()

        # 2. Buscar a configuração atual (a linha com id=1)
        #    .first_or_404() é útil: retorna a config ou erro 404 se não achar
        config_atual = Configuracao.query.get_or_404(1) 
        
        # 3. Preparar dados para os gráficos (invertendo a ordem)
        leituras_invertidas = ultimas_leituras[::-1]
        lista_umid_solo = [float(r.umidade_solo) for r in leituras_invertidas]
        lista_luz = [float(r.luminosidade) for r in leituras_invertidas]

        vl_umid_solo = json.dumps(lista_umid_solo)
        vl_luz = json.dumps(lista_luz)

        # Convertendo objetos SQLAlchemy para dicionários para o template
        resultados_dict = [
            {
                'id': r.id, 
                'umidade_solo': r.umidade_solo, 
                'luminosidade': r.luminosidade, 
                'estado_bomba': r.estado_bomba, 
                'data_hora': r.data_hora
            } 
            for r in ultimas_leituras # Usamos as leituras na ordem original (mais recentes primeiro) para a tabela
        ]
        config_dict = {
            'id': config_atual.id,
            'modo': config_atual.modo,
            'setpoint_umidade': config_atual.setpoint_umidade,
            'comando_manual_bomba': config_atual.comando_manual_bomba
        }


        return render_template(
            'index.html',
            resultados=resultados_dict, # Lista de dicionários para a tabela
            config=config_dict,         # Dicionário para os controles
            vl_umid_solo=vl_umid_solo,
            vl_luz=vl_luz
        )

    except Exception as e:
        # Captura genérica de erros (inclui falha no banco)
        print(f"Erro na rota dashboard: {e}")
        # Poderíamos ter uma página de erro mais amigável aqui
        return f"Ocorreu um erro ao carregar o dashboard: {e}", 500


@main_bp.route('/grupo/')
def grupo():
    """ Rota para a página de contatos/grupo """
    return render_template('grupo.html')


# --- API PARA O ESP32 E PARA O FRONTEND ---

@main_bp.route('/api/dados', methods=['POST'])
def receber_dados_esp32():
    """
    API para o ESP32 enviar dados dos sensores.
    Responde com a configuração atual.
    """
    try:
        dados = request.json
        umidade = dados.get('umidade')
        luz = dados.get('luz')
        bomba_ligada = dados.get('bomba_ligada')

        # Cria um novo objeto LeituraSensores
        nova_leitura = LeiturasSensores(
            umidade_solo=umidade,
            luminosidade=luz,
            estado_bomba=bool(bomba_ligada) # Garante que seja Boolean
        )
        
        # Adiciona à sessão e salva no banco
        db.session.add(nova_leitura)
        db.session.commit()

        # Busca a configuração atual para responder
        config = Configuracao.query.get(1)
        if config:
            config_dict = {
                "modo": config.modo,
                "setpoint": float(config.setpoint_umidade),
                # Converte Boolean para int (0 ou 1) para o ESP32
                "comando_manual": int(config.comando_manual_bomba) 
            }
            return jsonify(config_dict)
        else:
            return jsonify({"status": "erro", "mensagem": "Config not found"}), 404

    except Exception as e:
        db.session.rollback() # Desfaz a inserção em caso de erro
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

        # Busca a linha de configuração (id=1)
        config = Configuracao.query.get(1)
        if not config:
            return jsonify({"status": "erro", "mensagem": "Configuração não encontrada"}), 404

        # Atualiza o campo correto no objeto de configuração
        if chave == 'modo' and valor in ['AUTOMATICO', 'MANUAL']:
            config.modo = valor
        elif chave == 'setpoint':
            config.setpoint_umidade = float(valor)
        elif chave == 'comando_manual':
            config.comando_manual_bomba = bool(int(valor)) # Converte 0/1 para False/True
        else:
            return jsonify({"status": "erro", "mensagem": "Chave inválida"}), 400
            
        # Salva as alterações no banco de dados
        db.session.commit()
        
        return jsonify({"status": "ok", "mensagem": f"{chave} atualizado para {valor}"})

    except Exception as e:
        db.session.rollback() # Desfaz a atualização em caso de erro
        print(f"Erro na API /api/config: {e}")
        return jsonify({"status": "erro", "mensagem": str(e)}), 500