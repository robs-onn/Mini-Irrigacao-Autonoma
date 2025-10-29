from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime # Para tipos de data/hora

# Inicializa a extensão SQLAlchemy (ainda sem app específico)
db = SQLAlchemy()

# Pega o diretório ATUAL do arquivo __init__.py (ou seja, .../IrrigacaoAutonoma)
current_dir = os.path.dirname(__file__)
# Define o caminho para a subpasta 'db' DENTRO do diretório atual
db_folder_path = os.path.join(current_dir, 'db')
# Cria a pasta 'db' se ela ainda não existir
os.makedirs(db_folder_path, exist_ok=True)
# Define a URI do SQLite para criar o arquivo dentro da pasta 'db'
DATABASE_URI = 'sqlite:///' + os.path.join(db_folder_path, 'irrigacao_local.db')

# --- Modelos SQLAlchemy (Definição das Tabelas como Classes) ---

class LeiturasSensores(db.Model):
    __tablename__ = 'leituras_sensores' # Nome explícito da tabela
    
    id = db.Column(db.Integer, primary_key=True)
    data_hora = db.Column(db.DateTime, default=datetime.now) # TIMESTAMP
    umidade_solo = db.Column(db.Float)
    luminosidade = db.Column(db.Float)
    estado_bomba = db.Column(db.Boolean) # BOOLEAN (True/False ou 1/0)

    def __repr__(self):
        return f'<Leitura {self.id} - Umid: {self.umidade_solo}%>'

class Configuracao(db.Model):
    __tablename__ = 'configuracao' # Nome explícito da tabela
    
    id = db.Column(db.Integer, primary_key=True) # Geralmente id=1
    # Usaremos String para ENUM, pois SQLAlchemy tem peculiaridades com ENUM nativo
    modo = db.Column(db.String(10), default='AUTOMATICO') # 'AUTOMATICO' ou 'MANUAL'
    setpoint_umidade = db.Column(db.Float, default=60.0)
    comando_manual_bomba = db.Column(db.Boolean, default=False) # BOOLEAN (True/False ou 1/0)

    def __repr__(self):
        return f'<Config ID: {self.id} - Modo: {self.modo}>'

# --- Função Application Factory ---

def create_app(config=None):
    """
    Função 'Application Factory'.
    Cria e configura a instância do aplicativo Flask.
    """
    app = Flask(__name__)
    
    # --- Configuração do SQLAlchemy ---
    app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URI
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False # Desativa avisos desnecessários
    
    # Associa a instância do SQLAlchemy ao app Flask
    db.init_app(app)

    # --- Criar as Tabelas no Banco de Dados (se não existirem) ---
    with app.app_context():
        # Verifica se a tabela 'configuracao' já existe antes de tentar criar

        inspector = db.inspect(db.engine)
        if not inspector.has_table('configuracao'):
            print("Criando tabelas no banco de dados...")
            db.create_all()
            print("Tabelas criadas.")

            config_inicial = Configuracao(id=1, modo='AUTOMATICO', setpoint_umidade=60.0, comando_manual_bomba=False)
            db.session.add(config_inicial)
            db.session.commit()
            print("Configuração inicial inserida.")
        else:
             print("Tabelas já existem.")


    # --- Registrar os Blueprints (Rotas) ---
    from . import routes
    app.register_blueprint(routes.main_bp)

    return app