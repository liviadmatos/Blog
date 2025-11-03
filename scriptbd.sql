CREATE DATABASE blog_livia;

USE blog_livia;

CREATE TABLE usuario(
    idUsuario INT PRIMARY KEY AUTO_INCREMENT,
    nome VARCHAR(50) NOT NULL,
    user VARCHAR(15) NOT NULL UNIQUE,
    senha VARCHAR(255) NOT NULL, 
    dataCadastro TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    foto VARCHAR(100)
    )

CREATE TABLE post (
    idPost INT PRIMARY KEY AUTO_INCREMENT,
    titulo VARCHAR(50) NOT NULL,
    conteudo TEXT NOT NULL,
    idUsuario INT,
    dataPost TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (idUsuario) REFERENCES usuario(idUsuario)

);

