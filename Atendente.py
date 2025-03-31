import tkinter as tk
from tkinter import scrolledtext, messagebox
import socket
import threading
from db_SQLite import iniciar_atendimento, finalizar_atendimento, registrar_mensagem
from datetime import datetime

class Atendente:
    def __init__(self, nome, id_atendente, departamento):
        self._nome = nome
        self._id_atendente = id_atendente
        self._departamento = departamento
        self._disponivel = True
        self._usuario_atual = None
        self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._cliente_socket = None
        self._id_atendimento = None

    def iniciar_servidor(self, host='localhost', port=8080):
        try:
            self._socket.bind((host, port))
            self._socket.listen(1)
            self._disponivel = True
            return True
        except Exception as e:
            print(f"Erro ao iniciar servidor: {e}")
            return False

    def aceitar_conexao(self, id_usuario):
        try:
            self._cliente_socket, endereco = self._socket.accept()
            self._disponivel = False
            self._usuario_atual = id_usuario
            self._id_atendimento = iniciar_atendimento(
                self._id_atendente,
                id_usuario,
                self._departamento
            )
            return True
        except Exception as e:
            print(f"Erro ao aceitar conexão: {e}")
            return False
    def encerrar_atendimento(self):
        if self._cliente_socket:
            try:
                if self._id_atendimento:
                    finalizar_atendimento(self._id_atendimento)
                    self._id_atendimento = None
                self._cliente_socket.close()
                self._cliente_socket = None
                self._disponivel = True
                self._usuario_atual = None
            except Exception as e:
                print(f"Erro ao encerrar atendimento: {e}")
    #DB
    def registrar_mensagem(self, remetente, mensagem):
        if self._id_atendimento:
            registrar_mensagem(self._id_atendimento, remetente, mensagem)
    def encerrar_servidor(self):
        self.encerrar_atendimento()
        try:
            self._socket.close()
        except Exception as e:
            print(f"Erro ao encerrar servidor: {e}")

    @property
    def nome(self):
        return self._nome

    @property
    def id_atendente(self):
        return self._id_atendente

    @property
    def departamento(self):
        return self._departamento

    @property
    def disponivel(self):
        return self._disponivel


class AtendenteTela:
    def __init__(self, root):
        self.root = root
        self.root.title("Atendente - Sistema de Chat")


        #Atendente
        self.atendente = Atendente(
            "Marta Soares",
            "agent456",
            "1ª Vara Judicial (Família e Sucessões, Infância e Juventude, Cível e Juizado Especial Cível)"
        )

        #Conexão
        self.host = 'localhost'
        self.port = 8080
        self.running = False

        # Tela
        self.setup_ui()

    def setup_ui(self):
        # Frame de informações
        info_frame = tk.LabelFrame(self.root, text="Informações do Atendente", padx=5, pady=5)
        info_frame.pack(padx=10, pady=5, fill="x")

        tk.Label(info_frame, text=f"Nome: {self.atendente.nome}").pack(anchor="w")
        tk.Label(info_frame, text=f"ID: {self.atendente.id_atendente}").pack(anchor="w")
        tk.Label(info_frame, text=f"Departamento: {self.atendente.departamento}").pack(anchor="w")
        self.status_label = tk.Label(info_frame, text="Status: Desativado")
        self.status_label.pack(anchor="w")

        # Frame de controle
        control_frame = tk.Frame(self.root)
        control_frame.pack(padx=10, pady=5, fill="x")

        self.start_button = tk.Button(control_frame, text="Iniciar Servidor", command=self.iniciar_servidor)
        self.start_button.pack(side="left", padx=5)

        self.accept_button = tk.Button(control_frame, text="Aceitar Conexão", command=self.aceitar_conexao,
                                       state="disabled")
        self.accept_button.pack(side="left", padx=5)

        self.end_button = tk.Button(control_frame, text="Encerrar Servidor", command=self.encerrar_servidor,
                                    state="disabled")
        self.end_button.pack(side="left", padx=5)

        # Área de chat
        chat_frame = tk.LabelFrame(self.root, text="Chat", padx=5, pady=5)
        chat_frame.pack(padx=10, pady=5, fill="both", expand=True)

        self.chat_area = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, width=50, height=15, state="disabled")
        self.chat_area.pack(padx=5, pady=5, fill="both", expand=True)

        # Entrada de mensagem
        input_frame = tk.Frame(self.root)
        input_frame.pack(padx=10, pady=5, fill="x")

        self.message_entry = tk.Entry(input_frame)
        self.message_entry.pack(side="left", fill="x", expand=True, padx=5)
        self.message_entry.bind("<Return>", self.enviar_mensagem)

        self.send_button = tk.Button(input_frame, text="Enviar", command=self.enviar_mensagem, state="disabled")
        self.send_button.pack(side="left", padx=5)

        self.atendimento_thread = None

    def iniciar_servidor(self):
        if self.atendente.iniciar_servidor(self.host, self.port):
            self.running = True
            self.start_button.config(state="disabled")
            self.accept_button.config(state="normal")
            self.end_button.config(state="normal")
            self.status_label.config(text="Status: Disponível (Servidor ativo)")
            self.mostrar_mensagem("Sistema", "Servidor iniciado na porta 8080")

            threading.Thread(target=self.verificar_conexoes, daemon=True).start()
        else:
            messagebox.showerror("Erro", "Não foi possível iniciar o servidor")

    def verificar_conexoes(self):
        while self.running:
            if self.atendente.disponivel and self.accept_button['state'] == 'normal':
                self.root.update()

    def aceitar_conexao(self):
        id_usuario = "user123"

        if self.atendente.aceitar_conexao(id_usuario):
            self.accept_button.config(state="disabled")
            self.send_button.config(state="normal")
            self.status_label.config(text="Status: Ocupado (Em atendimento)")
            self.mostrar_mensagem("Sistema", "Conexão estabelecida com cliente")

            self.atendimento_thread = threading.Thread(target=self.receber_mensagens, daemon=True)
            self.atendimento_thread.start()
        else:
            messagebox.showerror("Erro", "Falha ao aceitar conexão")

    def receber_mensagens(self):
        while self.running and not self.atendente.disponivel:
            try:
                mensagem = self.atendente._cliente_socket.recv(1024).decode('utf-8')
                if not mensagem or mensagem.lower() == 'sair':
                    self.mostrar_mensagem("Sistema", "Cliente encerrou a conexão")
                    break
                self.mostrar_mensagem("Cliente", mensagem)
                self.atendente.registrar_mensagem("Cliente", mensagem)
            except ConnectionResetError:
                self.mostrar_mensagem("Sistema", "Cliente desconectado abruptamente")
                break
            except Exception as e:
                if self.running:
                    self.mostrar_mensagem("Erro", f"Falha na comunicação: {e}")
                break

        self.encerrar_atendimento()

    def enviar_mensagem(self, event=None):
        mensagem = self.message_entry.get()
        if mensagem and self.atendente._cliente_socket:
            try:
                self.atendente._cliente_socket.send(mensagem.encode('utf-8'))
                self.mostrar_mensagem("Você", mensagem)
                self.atendente.registrar_mensagem(self.atendente.nome, mensagem)
                self.message_entry.delete(0, tk.END)
                if mensagem.lower() == 'sair':
                    self.encerrar_atendimento()
            except Exception as e:
                self.mostrar_mensagem("Erro", f"Falha ao enviar mensagem: {e}")
                self.encerrar_atendimento()

    def encerrar_atendimento(self):
        if not self.atendente.disponivel:
            self.atendente.encerrar_atendimento()
            self.send_button.config(state="disabled")
            self.accept_button.config(state="normal")
            self.status_label.config(text="Status: Disponível")
            self.mostrar_mensagem("Sistema", "Atendimento encerrado")

    def encerrar_servidor(self):
        self.running = False
        self.encerrar_atendimento()
        self.atendente.encerrar_servidor()
        self.start_button.config(state="normal")
        self.accept_button.config(state="disabled")
        self.end_button.config(state="disabled")
        self.status_label.config(text="Status: Servidor desativado")
        self.mostrar_mensagem("Sistema", "Servidor encerrado")

    def mostrar_mensagem(self, remetente, mensagem):
        self.chat_area.config(state="normal")
        self.chat_area.insert(tk.END, f"{remetente}: {mensagem}\n")
        self.chat_area.config(state="disabled")
        self.chat_area.see(tk.END)

    def on_closing(self):
        self.running = False
        if hasattr(self.atendente, '_socket') and self.atendente._socket:
            self.encerrar_servidor()
        self.root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = AtendenteTela(root)
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    root.mainloop()