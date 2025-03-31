import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
from db_SQLite import registrar_mensagem


class Usuario:
    def __init__(self, nome, email, id_usuario, cpf):
        self._nome = nome
        self._email = email
        self._id_usuario = id_usuario
        self._cpf = cpf
        self._conexao_ativa = False
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._id_atendimento = None
    def conectar(self, host='localhost', port=8080):
        try:
            self._socket.connect((host, port))
            self._conexao_ativa = True
            self._socket.send(f"ID:{self._id_usuario}".encode('utf-8'))
            return True
        except Exception as e:
            print(f"Erro ao conectar: {e}")
            return False

    def desconectar(self):
        if self._conexao_ativa:
            try:
                self._socket.send('Sair'.encode('utf-8'))
                self._socket.close()
                self._conexao_ativa = False
                self._id_atendimento = None
            except Exception as e:
                print(f"Erro ao desconectar: {e}")
    #para o BD
    def registrar_mensagem(self, remetente, mensagem):
        if self._id_atendimento:
            registrar_mensagem(self._id_atendimento, remetente, mensagem)
    @property
    def nome(self):
        return self._nome

    @property
    def email(self):
        return self._email

    @property
    def id_usuario(self):
        return self._id_usuario

    @property
    def cpf(self):
        return self._cpf

    @property
    def conexao_ativa(self):
        return self._conexao_ativa


class UsuarioTela:
    def __init__(self, root):
        self.root = root
        self.root.title("Usuário - Sistema de Chat")

        #Usuário
        self.usuario = Usuario(
            "Maria de Fátima Silva",
            "maria@gmail.com",
            "user123",
            "12345678901"
        )

        #Conexão
        self.host = 'localhost'
        self.port = 8080
        self.running = False

        #Tela
        self.setup_ui()

    def setup_ui(self):
        info_frame = tk.LabelFrame(self.root, text="Informações do Usuário", padx=5, pady=5)
        info_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(info_frame, text=f"Nome: {self.usuario.nome}").pack(anchor="w")
        tk.Label(info_frame, text=f"ID: {self.usuario.id_usuario}").pack(anchor="w")
        tk.Label(info_frame, text=f"Email: {self.usuario.email}").pack(anchor="w")
        self.status_label = tk.Label(info_frame, text="Status: Desconectado")
        self.status_label.pack(anchor="w")


        control_frame = tk.Frame(self.root)
        control_frame.pack(padx=10, pady=5, fill="x")

        self.connect_button = tk.Button(control_frame, text="Conectar", command=self.conectar)
        self.connect_button.pack(side="left", padx=5)

        self.disconnect_button = tk.Button(control_frame, text="Desconectar", command=self.desconectar,
                                           state="disabled")
        self.disconnect_button.pack(side="left", padx=5)

        chat_frame = tk.LabelFrame(self.root, text="Chat", padx=5, pady=5)
        chat_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=50, height=15, state="disabled")
        self.chat_area.pack(padx=5, pady=5, fill="both", expand=True)

        #Mensagem
        input_frame = tk.Frame(self.root)
        input_frame.pack(padx=10, pady=5, fill="x")

        self.message_entry = tk.Entry(input_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.message_entry.bind("<Return>", self.enviar_mensagem)

        self.send_button = tk.Button(input_frame, text="Enviar", command=self.enviar_mensagem, state="disabled")
        self.send_button.pack(side="left", padx=5)

        # Thread para receber mensagens
        self.receber_thread = None

    def conectar(self):
        if self.usuario.conectar(self.host, self.port):
            self.running = True
            self.connect_button.config(state="disabled")
            self.disconnect_button.config(state="normal")
            self.send_button.config(state="normal")
            self.status_label.config(text="Status: Conectado")
            self.mostrar_mensagem("Sistema", "Conectado ao atendente")


            self.receber_thread = threading.Thread(target=self.receber_mensagens, daemon=True)
            self.receber_thread.start()
        else:
            messagebox.showerror("Erro", "Não foi possível conectar ao servidor")

    def receber_mensagens(self):
        while self.running and self.usuario.conexao_ativa:
            try:
                resposta = self.usuario._socket.recv(1024).decode('utf-8')
                if not resposta or resposta.lower() == 'sair':
                    self.mostrar_mensagem("Sistema", "Atendente encerrou a conexão")
                    break
                if resposta.startswith("ID_ATENDIMENTO:"):
                    self.usuario._id_atendimento = int(resposta.split(":")[1])
                else:
                    self.mostrar_mensagem("Atendente", resposta)
                    self.usuario.registrar_mensagem("Atendente", resposta)
            except ConnectionResetError:
                self.mostrar_mensagem("Sistema", "Conexão com o atendente foi perdida")
                break
            except Exception as e:
                if self.running:
                    self.mostrar_mensagem("Erro", f"Falha na comunicação: {e}")
                break

        self.desconectar()

    def enviar_mensagem(self, event=None):
        mensagem = self.message_entry.get()
        if mensagem and self.usuario.conexao_ativa:
            try:
                self.usuario._socket.send(mensagem.encode('utf-8'))
                self.mostrar_mensagem("Você", mensagem)
                self.usuario.registrar_mensagem(self.usuario.nome, mensagem)
                self.message_entry.delete(0, tk.END)
                if mensagem.lower() == 'sair':
                    self.desconectar()
            except Exception as e:
                self.mostrar_mensagem("Erro", f"Falha ao enviar mensagem: {e}")
                self.desconectar()

    def desconectar(self):
        if self.usuario.conexao_ativa:
            self.running = False
            self.usuario.desconectar()
            self.connect_button.config(state="normal")
            self.disconnect_button.config(state="disabled")
            self.send_button.config(state="disabled")
            self.status_label.config(text="Status: Desconectado")
            self.mostrar_mensagem("Sistema", "Desconectado do atendente")

    def mostrar_mensagem(self, remetente, mensagem):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"{remetente}: {mensagem}\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def on_closing(self):
        self.running = False
        if self.usuario.conexao_ativa:
            self.desconectar()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = UsuarioTela(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()
