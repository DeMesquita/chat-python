import sqlite3
from datetime import datetime


def criar_banco_dados():
    conn = sqlite3.connect('chat_atendimentos.db')
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS atendimentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_atendente TEXT NOT NULL,
        id_usuario TEXT NOT NULL,
        departamento TEXT NOT NULL,
        data_inicio TEXT NOT NULL,
        data_fim TEXT,
        status TEXT NOT NULL
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS mensagens (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        id_atendimento INTEGER NOT NULL,
        remetente TEXT NOT NULL,
        mensagem TEXT NOT NULL,
        data_envio TEXT NOT NULL,
        FOREIGN KEY (id_atendimento) REFERENCES atendimentos(id)
    )
    ''')

    conn.commit()
    conn.close()


def iniciar_atendimento(id_atendente, id_usuario, departamento):
    conn = sqlite3.connect('chat_atendimentos.db')
    cursor = conn.cursor()

    data_inicio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO atendimentos (id_atendente, id_usuario, departamento, data_inicio, status)
    VALUES (?, ?, ?, ?, ?)
    ''', (id_atendente, id_usuario, departamento, data_inicio, 'em_andamento'))

    id_atendimento = cursor.lastrowid
    conn.commit()
    conn.close()
    return id_atendimento


def finalizar_atendimento(id_atendimento):
    conn = sqlite3.connect('chat_atendimentos.db')
    cursor = conn.cursor()

    data_fim = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    UPDATE atendimentos 
    SET data_fim = ?, status = 'finalizado'
    WHERE id = ?
    ''', (data_fim, id_atendimento))

    conn.commit()
    conn.close()


def registrar_mensagem(id_atendimento, remetente, mensagem):
    conn = sqlite3.connect('chat_atendimentos.db')
    cursor = conn.cursor()

    data_envio = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    cursor.execute('''
    INSERT INTO mensagens (id_atendimento, remetente, mensagem, data_envio)
    VALUES (?, ?, ?, ?)
    ''', (id_atendimento, remetente, mensagem, data_envio))

    conn.commit()
    conn.close()


criar_banco_dados()