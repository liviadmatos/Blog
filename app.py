from flask import Flask, render_template, request, redirect, flash, session #importando a biblioteca, importante!
from db import *
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash
from config import *



#Acessar as variáveis
secret_key = SECRET_KEY
usuario_admin = USUARIO_ADMIN
senha_admin = SENHA_ADMIN

app = Flask(__name__) #informa o tipo do app
app.secret_key = secret_key

#Configurar pata de upload
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'static/uploads')

#criando a ropa páguna inicial
@app.route('/') 
def index():
    
    postagens = listar_post()
    return render_template('index.html', postagens=postagens)

@app.route('/novopost', methods=['GET','POST'])
def novopost():
    if request.method == 'GET':
        return redirect('/')
    if request.method == 'POST':
        titulo = request.form['titulo'].strip()
        conteudo = request.form['conteudo'].strip()
        idUsuario = session['idUsuario']
        
        if not titulo or not conteudo:
            flash("Preencha todos os campos!")
            return redirect('/')
        else:
            post = adicionar_post(titulo, conteudo, idUsuario)
        if post: 
            flash("Post realizado com sucesso!")
            return redirect('/')
        else:
            flash("Falha ao postar!")
            postagens = listar_post()
            return render_template('index.html',postagens=postagens)
    
    return redirect('/')
    
#rota para editar posts
@app.route('/editarpost/<int:idPost>' , methods=['GET','POST'])
def editarpost(idPost):
    if 'user' not in session or 'admin' in session:
        return redirect('/')
    with conectar() as conexao:
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(f'SELECT idUsuario FROM post WHERE idPost = {idPost}')
        autor = cursor.fetchone()
        if not autor or autor['idUsuario'] != session ['idUsuario']:
            print('Tentativa de acessar postagem de outra autoria')
            return redirect('/')
    if request.method == "GET":
        try:
            with conectar() as conexao:
                cursor = conexao.cursor(dictionary=True)
                cursor.execute(f"SELECT * FROM post WHERE idPost = {idPost}")
                post = cursor.fetchone()
                postagens = listar_post()
                return render_template('index.html', postagens=postagens, post=post)
        
        except mysql.connector.Error as erro:
            print(f"ERRO DE BD: {erro}")
            flash ("Houve um erro! Tente mais tarde!")
            return redirect('/')
    #gravar alterações
    if request.method == "POST":
        #pegando as informações do formulario
        titulo = request.form['titulo'].strip()
        conteudo = request.form['conteudo'].strip()
        if not titulo or not conteudo:
            flash("Preencha todos os campos!")
            return redirect(f'/editarpost/{idPost}')
        sucesso = atualizar_post(titulo,conteudo,idPost)
        if sucesso:
            flash("Post alterado com sucesso!")
            return redirect('/')
        else:
            flash("Falha ao alterar o post. Tente novamente mais tarde!")
            return redirect('/')
        
@app.route('/excluirpost/<int:idPost>')
def excluirpost(idPost):
    if not session:
        print("Usuário não autorizado acessando rota excluir.")
        return redirect('/')
    #verificar se o usuário é o autor do post
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            if 'admin' not in session:
                cursor.execute(f"SELECT idUsuario FROM post WHERE idPost = {idPost}")
                autor_post = cursor.fetchone()

                if not autor_post or autor_post['idUsuario'] != session.get('idUsuario'):
                    print("Tentativa de exclusão inválida")
                    return redirect ('/')
                
            cursor.execute(f"DELETE FROM post WHERE idPost = {idPost}")
            conexao.commit()
            flash("Post excluído com sucesso!")
            if 'admin' in session:
                return redirect('/dashboard')
            else:
                return redirect('/')
    except mysql.connector.Error as erro:
        conexao.rollback()
        print(f"ERRO DE BD: {erro}")
        flash ("Houve um erro! Tente mais tarde!")
        return redirect('/')
    
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='GET':
        return render_template('login.html')
    elif request.method=='POST':
        usuario= request.form['user'].lower().strip()
        senha = request.form['senha'].strip()

        if usuario is None or senha is None:
            flash("Preencha todos os campos!")
        #Primeiro verificamos se o usuario é o admin
        if usuario == usuario_admin and senha == senha_admin:
            session['admin'] = True
            return redirect('/dashboard')
        
        #Verificar se é um usuário cadastrado
        resultado, usuario_encontrado = verificar_usuario (usuario,senha)
        if resultado:
            if usuario_encontrado['ativo']==0:
                flash('Usuário bloqueado! Fale com o adm!')
                return redirect('/login')
            #Usuário com senha resetada
            if usuario_encontrado['senha'] == '1234':
                session['idUsuario'] = usuario_encontrado['idUsuario']
                return render_template("nova_senha.html")
            session['idUsuario'] = usuario_encontrado ['idUsuario']
            session['user'] = usuario_encontrado ['user']
            session['foto'] = usuario_encontrado ['foto']
            return redirect ('/')

        #Nenhum usuário ou Admin encontrado
        else:
            flash("Usuário ou senha inválidos!")
            return redirect('/login')
        
@app.route('/dashboard')
def dashboard():
    if not session or "admin" not in session:
        return redirect('/')
    
    usuarios = listar_usuarios()
    posts = listar_post()
    total_posts_ativos, total_usuarios = totais()
    return render_template('dashboard.html', posts=posts, usuarios=usuarios, total_posts_ativos= total_posts_ativos, total_usuarios = total_usuarios)

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

#rota para cadastro de usuarios

@app.route('/cadastro', methods=['GET','POST'])
def cadastro():
    if request.method== 'GET':
        return render_template('cadastro.html')
    elif request.method== 'POST':
        nome = request.form['nome'].strip()
        usuario = request.form['user'].lower().strip()
        senha = request.form['senha'].strip()
        if not nome or not usuario or not senha:
            flash ('Preencha todos os campos corretamente!')
            return redirect('/cadastro')
        
        senha_hash = generate_password_hash(senha)
        
        foto = 'placeholder.png'
        resultado, erro = adicionar_usuario(nome, usuario, senha_hash, foto)

        if resultado:
            flash("Usuário cadastrado com sucesso!")
            return redirect('/login')
        else:
            if erro.errno == 1062:
                flash("Usuário já cadastrado, insira outro.")
            else:
                flash("Erro ao cadastrar. TEnte novamente mais tarde.")
            return redirect('/cadastro')      

@app.route('/usuario/status/<int:idUsuario>')
def status_usuario(idUsuario):
    if not session:
        return redirect('/')   
    sucesso = alterar_status(idUsuario)
    if sucesso:
        flash('Status alterado com sucesso')
    else:
        flash('Erro na alteração do status')
    return redirect('/dashboard')


@app.route('/usuario/excluir/<int:idUsuario>')
def excluir_usuario(idUsuario):
    if 'admin' not in session:
        return redirect('/')
    sucesso= delete_usuario(idUsuario)
    if sucesso:
        flash("Usuário exclído com sucesso.")
    else:
        flash("Erro na exclusão do usuário.")
    return redirect('/dashboard')

#Rota paar resetar senha
@app.route('/usuario/reset/<int:idUsuario>')
def reset(idUsuario):
    if 'admin' not in session:
        return redirect('/')
    sucesso = reset_senha(idUsuario)
    if sucesso:
        flash("Senah resetada com sucesso")
    else: 
        flash("Falha ao resetar a senha")
    return redirect('/dashboard')

#Rota para salvas senha
@app.route('/usuario/novasenha', methods=['GET','POST'])
def novasenha():
    if 'idUsuario' not in session:
        return redirect('/')
    if request.method == 'GET':
        return render_template ('nova_senha.html')
    
    if request.method == 'POST':
        senha = request.form['senha']
        confirmacao = request.form['confirmacao']

        if not senha or not confirmacao:
            flash('Preencha corretamente as senhas!')
            return render_template('nova_senha.html')
        if senha != confirmacao:
            flash('As senhas não coincidem')
            return render_template('nova_senha.html')
        if senha == '1234':
            flash('As senhas não podem ser iguais')

        senha_hash = generate_password_hash(senha)
        idUsuario= session['idUsuario']
        sucesso = alterar_senha(senha_hash, idUsuario)
        if sucesso:
            flash('Senha alterada com sucesso')
            if 'user' in session:
                return redirect ('/perfil')
            else:
                return redirect('/login')
        else:
            flash('Erro no cadastro da nova senha')
            return render_template('nova_senha.html')
        

#Rota de perfil
@app.route('/perfil', methods=['GET','POST'])
def perfil():
    if 'user' not in session:
        return redirect('/')
    if request.method == 'GET':
        lista_usuarios = listar_usuarios()
        usuario = None
        for u in lista_usuarios:
            if u['idUsuario'] == session ['idUsuario']:
                usuario = u
                break 
        return render_template('perfil.html', nome=usuario ['nome'], user=usuario ['user'], foto=usuario['foto'])
    if request.method == 'POST':
        nome = request.form['nome'].strip()
        user = request.form['user'].strip()
        foto = request.files.get('foto')  
        idUsuario = session['idUsuario']
        nome_foto = ""

        if not nome or not user:
            flash('Os campos devem estar preenchidos.')
            return redirect('/perfil')

        if foto:
            if foto.filename == '':
                flash("Arquivo inválido!")
                return redirect('/perfil')    
            extensao = foto.filename.rsplit('.',1)[-1].lower()
            if extensao not in ('png','jpg','webp'):
                flash('Extensão inválida!')
                return redirect('/perfil')
            if len(foto.read()) > 2*1024*1024:
                flash('Arquivo acima de 2MB não é aceito!')
                return redirect('/perfil')

            foto.seek(0)
            nome_foto = f'{idUsuario}.{extensao}'

        sucesso = editar_perfil(nome, user, nome_foto, idUsuario)

        if sucesso:
            if foto and nome_foto:
                print("Salvando foto")
                caminho_completo = os.path.join(app.config['UPLOAD_FOLDER'], nome_foto)
                foto.save(caminho_completo)
            flash("Dados alterados com sucesso")
        else:
            flash("Erro ao alterar os dados")

        return redirect('/perfil')


#Erro 404
@app.errorhandler(404)
def pagina_nao_encontrada(erro):
    return render_template('erro404.html'),404




#sempre no final do arquivo
if __name__ == "__main__":
    app.run(debug=True)

