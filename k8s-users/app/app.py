from flask import Flask, request, jsonify
import psycopg2
import os

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.environ["DB_HOST"],
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"]
    )

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS usuarios (
            id SERIAL PRIMARY KEY,
            nome VARCHAR(100) NOT NULL,
            email VARCHAR(100) UNIQUE NOT NULL,
            idade INT
        )
    """)
    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def index():
    return jsonify({"mensagem": "Sistema de cadastro de usuários - OK"})

@app.route("/usuarios", methods=["POST"])
def criar_usuario():
    dados = request.get_json()
    nome = dados.get("nome")
    email = dados.get("email")
    idade = dados.get("idade")

    if not nome or not email:
        return jsonify({"erro": "Nome e email são obrigatórios"}), 400

    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO usuarios (nome, email, idade) VALUES (%s, %s, %s) RETURNING id",
            (nome, email, idade)
        )
        usuario_id = cur.fetchone()[0]
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"mensagem": "Usuário criado!", "id": usuario_id}), 201
    except psycopg2.errors.UniqueViolation:
        return jsonify({"erro": "Email já cadastrado"}), 409
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/usuarios", methods=["GET"])
def listar_usuarios():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, idade FROM usuarios ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        usuarios = [
            {"id": r[0], "nome": r[1], "email": r[2], "idade": r[3]}
            for r in rows
        ]
        return jsonify(usuarios)
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/usuarios/<int:usuario_id>", methods=["GET"])
def buscar_usuario(usuario_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, nome, email, idade FROM usuarios WHERE id = %s", (usuario_id,))
        row = cur.fetchone()
        cur.close()
        conn.close()
        if not row:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"id": row[0], "nome": row[1], "email": row[2], "idade": row[3]})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

@app.route("/usuarios/<int:usuario_id>", methods=["DELETE"])
def deletar_usuario(usuario_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM usuarios WHERE id = %s RETURNING id", (usuario_id,))
        deleted = cur.fetchone()
        conn.commit()
        cur.close()
        conn.close()
        if not deleted:
            return jsonify({"erro": "Usuário não encontrado"}), 404
        return jsonify({"mensagem": "Usuário removido!"})
    except Exception as e:
        return jsonify({"erro": str(e)}), 500

if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)