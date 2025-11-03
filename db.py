import mysql.connector
from werkzeug.security import check_password_hash
#funcao para conectar ao banco de dados SQL
def conectar():
    conexao = mysql.connector.connect(
    host= "localhost",
    user= "root",
    password= "senai",
    database= "blog_livia"
)

    if conexao.is_connected():
        print("Conexão com BD ok!")

    return conexao

#funcao para listar todas as postagnes
def listar_post():
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT p.*, u.user, u.foto FROM post p INNER JOIN usuario u ON u.idUsuario = p.idUsuario ORDER BY idPost DESC")
            return cursor.fetchall()
    

    except mysql.connector.Error as erro:
        print(f"ERRO DE BD: {erro}")
        return []
    

def listar_usuarios():
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            cursor.execute("SELECT * FROM usuario")
            return cursor.fetchall()
    

    except mysql.connector.Error as erro:
        print(f"ERRO DE BD: {erro}")
        return []

    

def adicionar_post(titulo, conteudo, idUsuario):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            sql = "INSERT INTO post (titulo, conteudo, idUsuario) VALUES (%s, %s, %s)"
            cursor.execute(sql, (titulo, conteudo, idUsuario))
            conexao.commit()
            return True
    except mysql.connector.Error as erro:
        print(f"ERRO DE BD: {erro}")
        return False
    
    



def adicionar_usuario(nome, usuario, senha):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor()
            sql = "INSERT INTO usuario (nome, user, senha) VALUES (%s, %s, %s)"
            cursor.execute(sql, (nome, usuario, senha))
            conexao.commit()
            return True, "ok"
    except mysql.connector.Error as erro:
        print(f"ERRO DE BD: {erro}")
        return False, erro

def verificar_usuario(usuario, senha):
    try:
        with conectar() as conexao:
            cursor = conexao.cursor(dictionary=True)
            sql = "SELECT * FROM usuario WHERE user = %s;"
            cursor.execute(sql, (usuario,))
            usuario_encontrado = cursor.fetchone()
            if usuario_encontrado:
                if check_password_hash(usuario_encontrado['senha'], senha):
                    return True, usuario_encontrado
                return False, None
    except mysql.connector.Error as erro:
        print(f"Erro de BD! Erro: {erro}")
        return False, None