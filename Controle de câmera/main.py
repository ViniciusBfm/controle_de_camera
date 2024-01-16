from flask import Flask, render_template, request, redirect, session, url_for, make_response
from flask_sqlalchemy import SQLAlchemy
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import io
from reportlab.pdfgen import canvas
import json
import numpy as np
from bs4 import BeautifulSoup
from io import BytesIO
from reportlab.lib.units import inch



app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///meu_banco_de_dados.db'
db = SQLAlchemy(app)

def usuario_autenticado():
    return 'usuario_id' in session  # Exemplo: verifica se o ID do usuário está na sessão

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ip = db.Column(db.String(50))
    nome = db.Column(db.String(50))
    dvr = db.Column(db.String(50))
    posicao = db.Column(db.String(50))

# Rota para exibir o formulário de login
@app.route("/", methods=["GET"])
@app.route("/login", methods=["GET"])
def exibir_login():
    db.create_all()
    return render_template('login.html')

# Rota para processar os dados do formulário de login
@app.route("/", methods=["POST"])
@app.route("/login", methods=["POST"])
def login():
    if request.method == "POST":
        nome = request.form.get('usuario')
        senha = request.form.get('senha')

        if nome == 'admin' and senha == 'acbeubv20':
            # Armazenar o nome do usuário na sessão
            session['username'] = nome
            # Redirecionar para a rota '/home' após o login bem-sucedido
            return redirect("/home")
        else:
            mensagem = "Senha ou usuário incorreto. Tente novamente."

        return render_template("login.html", mensagem=mensagem)

    return render_template('login.html')

# Rota para a página inicial
# Rota para a página inicial
@app.route('/home', methods=['GET', 'POST'])
def home():
    # Verificar se o usuário está logado
    if 'username' in session:
        # Obter o nome do usuário da sessão
        nome_usuario = session['username']

        # Lógica para lidar com a adição de um novo usuário
        if request.method == 'POST':
            ip = request.form['ip']
            nome = request.form['nome']
            dvr = request.form['dvr']
            posicao = request.form['posicao']

            user = User(ip=ip, nome=nome, dvr=dvr, posicao=posicao)
            db.session.add(user)
            db.session.commit()

            # Redirecionar após a adição bem-sucedida
            return redirect("/home")

        # Obter a lista de usuários
        users = User.query.all()

        # Geração de dados dinâmicos para o gráfico de barras
        x_bar = ["Toddler", "Nursery", "Sk", "Jk", "Year 1", "Year 2", "Year 3", "Year 4", "Pens. Comp"]
        y_bar = [1, 1, 1, 1, 1, 1, 1, 0, 6]
        cores_bar = ["red", "blue", "green", "yellow", "orange", "pink", "purple", "cyan", "brown"]

        # Criação do objeto JSON para o gráfico de barras
        bar_chart_data = {
            "data": {
                "labels": x_bar,
                "datasets": [{
                    "label": "Notebook por Sala",
                    "data": y_bar,
                    "backgroundColor": cores_bar,
                }]
            },
            "layout": {
                "scales": {
                    "xAxes": [{"type": "category", "position": "bottom"}],
                    "yAxes": [{"type": "linear", "position": "left"}]
                }
            }
        }

        # Geração de dados dinâmicos para o segundo gráfico linear
        x_linear = ["Year 2", "Year 3", "Year 4"]
        y_linear = [1, 4, 2]
        cores_linear = ["#1cc88a", "#36b9cc", "#4e73df"]

        # Criação do objeto JSON para o segundo gráfico linear
        linear_chart_data = {
            "data": {
                "labels": x_linear,
                "datasets": [{
                    "label": "Chromebook por sala",
                    "data": y_linear,
                    "backgroundColor": cores_linear,
                    "borderColor": cores_linear,
                    "fill": False,
                }]
            },
            "layout": {
                "scales": {
                    "xAxes": [{
                        "type": "category",
                        "position": "bottom"
                    }],
                    "yAxes": [{
                        "type": "linear",
                        "position": "left"
                    }]
                }
            }
        }

        # Gere uma lista de valores de progresso fictícios (de 0 a 100)
        teclado = 19
        teclado_usando = 12 #ALTERAR
        mouse = 29
        mouse_usando = 21 #ALTERAR
        webcam = 2
        webcam_usando = 0 #ALTERAR
        fone = 6
        fone_usando = 2  #ALTERAR
        chromebooks = 6
        chromebooks_usando = 1

        teclado_disponivel = teclado - teclado_usando
        mouse_disponivel = mouse - mouse_usando
        webcam_disponivel = webcam - webcam_usando
        fone_disponivel = fone - fone_usando
        chromebook_disponivel = chromebooks - chromebooks_usando

        valores_de_progresso = [((teclado_usando/teclado)*100), ((mouse_usando/mouse)*100), ((webcam_usando/webcam)*100), ((fone_usando/fone)*100)]

        # Renderizar a página home com ambos os gráficos
        return render_template("home.html", nome=nome_usuario, users=users, bar_chart_json=json.dumps(bar_chart_data), linear_chart_json=json.dumps(linear_chart_data), valores_de_progresso=valores_de_progresso, teclado_disponivel = teclado_disponivel, mouse_disponivel = mouse_disponivel, webcam_disponivel = webcam_disponivel, fone_disponivel = fone_disponivel, chromebook_disponivel = chromebook_disponivel, chromebooks=chromebooks, chromebooks_usando=chromebooks_usando)

    else:
        # Se não estiver logado, redirecionar para a página de login
        return redirect("/login")

# Rota para excluir um usuário
@app.route("/delete_user/<int:user_id>", methods=['GET'])
def delete_user(user_id):
    # Verificar se o usuário está logado
    if 'username' in session:
        # Obter o usuário pelo ID
        user = User.query.get(user_id)

        # Verificar se o usuário existe
        if user:
            # Remover o usuário do banco de dados
            db.session.delete(user)
            db.session.commit()

    # Redirecionar de volta para a página home
    return redirect("/home")
# Rota para gerar o PDF
@app.route('/gerar_pdf', methods=['GET'])
def gerar_pdf():
    # Lógica para obter dados do banco de dados ordenados por IP
    users = User.query.order_by(db.cast(User.ip, db.Integer)).all()

    # Configurações do PDF
    buffer = io.BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)

    # Organizar dados em uma tabela
    data = [['IP', 'Nome', 'DVR', 'Posição']]
    for user in users:
        data.append([user.ip, user.nome, user.dvr, user.posicao])

    # Criar a tabela
    table = Table(data, colWidths=[1.0*inch, 3.5*inch, 0.5*inch, 1.0*inch])  # Ajuste as larguras conforme necessário
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#e6e6e6'),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
    ]))

    # Adicionar a tabela ao PDF
    pdf.build([table])

    buffer.seek(0)

    # Crie uma resposta Flask com o PDF
    response = make_response(buffer.read())
    response.mimetype = 'application/pdf'
    
    # Defina o nome do arquivo PDF
    response.headers['Content-Disposition'] = 'inline; filename=relatorio_usuarios.pdf'

    return response
@app.route('/gerar_pdf_tabela_computadores', methods=['GET'])
def gerar_pdf_tabela_computadores():
    # Simule dados da tabela HTML (substitua isso pelo conteúdo real da sua tabela HTML)
    tabela_html = """
    <table id="computadores-table" >
        <tbody>   
            <tr>
                <td>Ideapad 320</td>
                <td>Toddler</td>
                <td>Sim</td>
                <td>BV-TODDLER</td>
                <td>6570</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Nursery</td>
                <td>Sim</td>
                <td>BV-NURSA-01</td>
                <td>6560</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>SK</td>
                <td>Sim</td>
                <td>BV-JK-PROF</td>
                <td>6558</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>SK</td>
                <td>Sim</td>
                <td>BV-SK-PROF</td>
                <td>6559</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Year 1</td>
                <td>Sim</td>
                <td>BV-YEAR1</td>
                <td>6909</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Year 2</td>
                <td>Sim</td>
                <td>BV-YEAR2</td>
                <td>6567</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Year 3</td>
                <td>Sim</td>
                <td>BV-YEAR3</td>
                <td>6576</td>
            </tr>
            <tr>
                <td>NADA</td>
                <td>Year 4</td>
                <td>Sim</td>
                <td>BV-YEAR4</td>
                <td>NADA</td>
            </tr>
            <tr>
                <td>Dell</td>
                <td>Pens. Comput.</td>
                <td>Sim</td>
                <td>VERFICAR</td>
                <td>NADA</td>
            </tr>
            <tr>
                <td>Dell</td>
                <td>Pens. Comput.</td>
                <td>Sim</td>
                <td>VERFICAR</td>
                <td>NADA</td>
            </tr>
            <tr>
                <td>Dell</td>
                <td>Pens. Comput.</td>
                <td>Sim</td>
                <td>VERFICAR</td>
                <td>NADA</td>
            </tr>
            <tr>
                <td>Ideapad B320</td>
                <td>Pens. Comput.</td>
                <td>Sim</td>
                <td>BV-ALUNO2</td>
                <td>6477</td>
            </tr>
            <tr>
                <td>Ideapad B320</td>
                <td>Pens. Comput.</td>
                <td>Sim</td>
                <td>BV-ALUNO1</td>
                <td>6573</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Pens. Comput.</td>
                <td>Sim</td>
                <td></td>
                <td>6980</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Auditório</td>
                <td>Sim</td>
                <td>BV-EVENTO-02</td>
                <td>6568</td>
            </tr>
    
            <tr>
                <td>Ideapad 320</td>
                <td>Juliana</td>
                <td>Sim</td>
                <td>BV-COORD-01</td>
                <td>6564</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Tessa</td>
                <td>Sim</td>
                <td>BV-PSICO-01</td>
                <td>6575</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Fernanda</td>
                <td>Sim</td>
                <td>BV-CORD-FERNANDA</td>
                <td>6574</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Biblioteca</td>
                <td>Sim</td>
                <td>BV-BIBLIO-01</td>
                <td>6566</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Monique</td>
                <td>Sim</td>
                <td>BV-COM-0-NOVO</td>
                <td>6563</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Direção</td>
                <td>Sim</td>
                <td>BV-DIRECAO</td>
                <td>6569</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>TI</td>
                <td>Sim</td>
                <td>BV-TI-01</td>
                <td>6911</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Recepção - Alaine</td>
                <td>Sim</td>
                <td>BV-RECEP-01</td>
                <td>6561</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Recepção - Aluciane</td>
                <td>Sim</td>
                <td>BV-RECEP-03</td>
                <td>6557</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Karina</td>
                <td>Sim</td>
                <td>BV-ADM-02</td>
                <td>6562</td>
            </tr>
            <tr>
                <td>Ideapad 320</td>
                <td>Silvoney</td>
                <td>Sim</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Ivan</td>
                <td>Sim</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Almoxarifado</td>
                <td>Sim</td>
                <td>BV-ALMOX-PC</td>
                <td>6350</td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Enfermaria</td>
                <td>Sim</td>
                <td>BV-ENFERMARIA-DESK</td>
                <td>2762</td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Portaria</td>
                <td>Não</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Ti</td>
                <td>Não</td>
                <td></td>
                <td>7068</td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Ti</td>
                <td>Não</td>
                <td></td>
                <td></td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Marketing</td>
                <td>Sim</td>
                <td>BV-MARK-01</td>
                <td>2350</td>
            </tr>
            <tr>
                <td>Desktop</td>
                <td>Sala dos Professores</td>
                <td>Sim</td>
                <td>BV-SALAPROF</td>
                <td>2425</td>
            </tr>
            
            
        </tbody>
    </table>
    """
    
     # Use o BeautifulSoup para extrair os dados da tabela HTML
    
    soup = BeautifulSoup(tabela_html, 'html.parser')
    dados_tabela = []
    for linha in soup.find_all('tr'):
        dados_linha = [coluna.get_text(strip=True) for coluna in linha.find_all('td')]
        if dados_linha:
            dados_tabela.append(dados_linha)

    # Configurações do PDF
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)

    # Organizar dados em uma tabela
    data = [['Modelo', 'Local', 'SSD', 'Nome', 'Tombo']] + dados_tabela

    # Criar a tabela
    tabela = Table(data, colWidths=[1.5*inch, 2.1*inch, 0.5*inch, 2.1*inch, 1.0*inch])  # Ajuste as larguras conforme necessário


    # Adicionar estilo à tabela
    estilo_tabela = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#e6e6e6'),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
    ])
    tabela.setStyle(estilo_tabela)

    # Adicionar a tabela ao PDF
    elementos = [tabela]
    pdf.build(elementos)

    buffer.seek(0)

    # Crie uma resposta Flask com o PDF
    response = make_response(buffer.read())
    response.mimetype = 'application/pdf'

    # Defina o nome do arquivo PDF
    response.headers['Content-Disposition'] = 'inline; filename=relatorio_tabela.pdf'

    return response

@app.route('/gerar_pdf_tabela_chomebooks', methods=['GET'])
def gerar_pdf_tabela_chomebooks():
    # Simule dados da tabela HTML (substitua isso pelo conteúdo real da sua tabela HTML)
    tabela_html = """
    <table id="chromebook-table" >
        <thead>
            <tr>
                <th style="width: 40%;">Modelo</th>
                <th style="width: 40%;">Local</th>
                <th style="width: 20%;">Tombo</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Chromebook</td>
                <td></td>
                <td>7941</td>
            </tr>
            <tr>
                <td>Chromebook</td>
                <td></td>
                <td>7922</td>
            </tr>
            <tr>
                <td>Chromebook</td>
                <td></td>
                <td>7942</td>
            </tr>
            <tr>
                <td>Chromebook</td>
                <td></td>
                <td>7937</td>
            </tr>
            <tr>
                <td>Chromebook</td>
                <td></td>
                <td>7923</td>
            </tr>
            <tr>
                <td>Chromebook</td>
                <td>Fernanda</td>
                <td>7943</td>
            </tr>
        </tbody>
    </table>
    """
    
     # Use o BeautifulSoup para extrair os dados da tabela HTML
    
    soup = BeautifulSoup(tabela_html, 'html.parser')
    dados_tabela = []
    for linha in soup.find_all('tr'):
        dados_linha = [coluna.get_text(strip=True) for coluna in linha.find_all('td')]
        if dados_linha:
            dados_tabela.append(dados_linha)

    # Configurações do PDF
    buffer = BytesIO()
    pdf = SimpleDocTemplate(buffer, pagesize=letter)

    # Organizar dados em uma tabela
    data = [['Modelo', 'Local', 'Tombo']] + dados_tabela

    # Criar a tabela
    tabela = Table(data, colWidths=[2.5*inch, 2.5*inch, 1.3*inch])  # Ajuste as larguras conforme necessário

    # Adicionar estilo à tabela
    estilo_tabela = TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), '#e6e6e6'),
        ('GRID', (0, 0), (-1, -1), 1, 'black'),
        ('ALIGN', (1, 1), (-1, -1), 'LEFT'),
    ])
    tabela.setStyle(estilo_tabela)

    # Adicionar a tabela ao PDF
    elementos = [tabela]
    pdf.build(elementos)

    buffer.seek(0)

    # Crie uma resposta Flask com o PDF
    response = make_response(buffer.read())
    response.mimetype = 'application/pdf'

    return response
# Logica para fazer logout
@app.route('/logout')
def logout():
    # Lógica de logout aqui (se necessário)
    # Limpar a sessão e redirecionar para a página de login
    session.clear()
    return redirect(url_for('logout_redirect'))

# Rota para redirecionar automaticamente para a página de login após fazer logout
@app.route('/logout_redirect')
def logout_redirect():
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='192.168.8.47', port=5000, debug=True)
