from werkzeug.security import generate_password_hash, check_password_hash

senha = "Lívia"
hash = generate_password_hash(senha)
senha_informada = "Ana"
print(hash)
if check_password_hash(hash, senha_informada):
    print("Senha OK!")
else:
    print("Senha errada!")