from flask import Flask, render_template, request, redirect, flash, session #importando a biblioteca, importante!
from db import *
from dotenv import load_dotenv
import mysql.connector
import os
from werkzeug.security import generate_password_hash, check_password_hash


#carregar esse arquivo para o python
load_dotenv()

#Acessar as variáveis
secret_key = os.getenv("SECRET_KEY")
usuario_admin = os.getenv("USUARIO_ADMIN")
senha_admin= os.getenv("SENHA_ADMIN")


app = Flask(__name__) #informa o tipo do app
app.secret_key = secret_key

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
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        idUsuario = session['idUsuario']
        post = adicionar_post(titulo, conteudo, idUsuario)
        if post: 
            flash("Post realizado com sucesso!")
            return redirect('/')
        else:
            flash("Falha ao postar!")
            postagens = listar_post
            return render_template('index.html',postagens=postagens)
    
    return redirect('/')
    
#rota para editar posts
@app.route('/editarpost/<int:idPost>' , methods=['GET','POST'])
def editarpost(idPost):
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
        titulo = request.form['titulo']
        conteudo = request.form['conteudo']
        try:
            with conectar() as conexao:
                cursor = conexao.cursor()
                cursor.execute(f"UPDATE post SET titulo = '{titulo}', conteudo = '{conteudo}' WHERE idPost = {idPost}")
                conexao.commit()
                return redirect('/')
        except mysql.connector.Error as erro:
            print(f"ERRO DE BD: {erro}")
            flash ("Houve um erro! Tente mais tarde!")
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
            return redirect('/')
    except mysql.connector.Error as erro:
        print(f"ERRO DE BD: {erro}")
        flash ("Houve um erro! Tente mais tarde!")
        return redirect('/')
    
@app.route('/login', methods=['GET','POST'])
def login():
    if request.method=='GET':
        return render_template('login.html')
    elif request.method=='POST':
        usuario= request.form['user'].lower()
        senha = request.form['senha']

        if usuario is None or senha is None:
            flash("Preencha todos os campos!")
        #Primeiro verificamos se o usuario é o admin
        if usuario == usuario_admin and senha == senha_admin:
            session['admin'] = True
            return redirect('/dashboard')
        
        #Verificar se é um usuário cadastrado
        resultado, usuario_encontrado = verificar_usuario (usuario,senha)
        if resultado:
            session['idUsuario'] = usuario_encontrado ['idUsuario']
            session['user'] = usuario_encontrado ['user']
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
    return render_template('dashboard.html', posts=posts, usuarios=usuarios)

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
        nome = request.form['nome']
        usuario = request.form['user'].lower()
        senha = request.form['senha']
        if nome is None or usuario is None or senha is None:
            flash ('Preencha todos os campos!')
            return redirect('/')
        
        senha_hash = generate_password_hash(senha)
        
        resultado, erro = adicionar_usuario(nome, usuario, senha_hash)

        if resultado:
            flash("Usuário cadastrado com sucesso!")
            return redirect('/login')
        else:
            if erro.errno == 1062:
                flash("Usuário já cadastrado, insira outro.")
            else:
                flash("Erro ao cadastrar. TEnte novamente mais tarde.")
            return redirect('/cadastro')
            



#sempre no final do arquivo
if __name__ == "__main__":
    app.run(debug=True)

