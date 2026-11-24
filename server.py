"""Aplicação local para um usuário. Execute python server.py."""
import argparse
import base64
import binascii
import json
import os
import secrets
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

from engine import EXAMPLES, MAX_BYTES, load_csv, plan_query, query

ROOT = Path(__file__).resolve().parent


class AppServer(ThreadingHTTPServer):
    def __init__(self, address):
        super().__init__(address, Handler)
        self.datasets = {}
        self.lock = threading.Lock()


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass

    def send(self, value, status=200, content_type="application/json; charset=utf-8"):
        data = value if isinstance(value, bytes) else json.dumps(value, ensure_ascii=False, allow_nan=False).encode()
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self.send((ROOT / "index.html").read_bytes(), content_type="text/html; charset=utf-8")
        elif self.path == "/api/config":
            self.send({"ai_enabled": bool(os.getenv("OPENAI_API_KEY")),
                       "examples": [{"id": item["id"], "question": item["question"]} for item in EXAMPLES]})
        else:
            self.send({"error": "Página inexistente."}, 404)

    def do_POST(self):
        # Bloqueia requisições de outras origens no navegador.
        host = self.headers.get("Host", "")
        allowed = {f"127.0.0.1:{self.server.server_port}", f"localhost:{self.server.server_port}"}
        if host not in allowed or self.headers.get("Origin", f"http://{host}") != f"http://{host}":
            self.send({"error": "Origem não permitida."}, 403)
            return
        if self.headers.get_content_type() != "application/json":
            self.send({"error": "Envie JSON."}, 415)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= MAX_BYTES * 2:
                raise ValueError("Requisição vazia ou muito grande.")
            payload = json.loads(self.rfile.read(length))
            if not isinstance(payload, dict):
                raise ValueError("Corpo JSON inválido.")
            if self.path in {"/api/upload", "/api/sample"}:
                if self.path == "/api/sample":
                    raw = (ROOT / "data/vendas_demo.csv").read_bytes()
                else:
                    encoded = payload.get("data")
                    if not isinstance(encoded, str):
                        raise ValueError("Arquivo inválido.")
                    raw = base64.b64decode(encoded, validate=True)
                dataset = load_csv(raw)
                token = secrets.token_urlsafe(24)
                with self.server.lock:
                    # Mantém apenas as cinco bases mais recentes em memória.
                    if len(self.server.datasets) >= 5:
                        del self.server.datasets[next(iter(self.server.datasets))]
                    self.server.datasets[token] = dataset
                self.send({"dataset": token, "schema": dataset["schema"],
                           "count": len(dataset["rows"]), "preview": dataset["rows"][:5]})
            elif self.path == "/api/ask":
                token = payload.get("dataset")
                if not isinstance(token, str):
                    raise ValueError("Carregue uma base.")
                with self.server.lock:
                    dataset = self.server.datasets.get(token)
                if dataset is None:
                    raise ValueError("A base expirou. Carregue novamente o arquivo.")
                if payload.get("example"):
                    example = next((item for item in EXAMPLES if item["id"] == payload["example"]), None)
                    if not example:
                        raise ValueError("Exemplo desconhecido.")
                    required = {"regiao": {"regiao", "valor_venda"},
                                "produto": {"produto", "quantidade"},
                                "mes": {"data", "valor_venda"}, "ticket": {"valor_venda"}}
                    if not required[example["id"]].issubset({col["name"] for col in dataset["schema"]}):
                        raise ValueError("Este exemplo precisa das colunas da base de demonstração.")
                    plan = {"sql": example["sql"], "clarification": ""}
                    mode = "Exemplo guiado com SQL predefinido"
                    question = example["question"]
                else:
                    question = payload.get("question")
                    if not isinstance(question, str) or not 1 <= len(question.strip()) <= 1000:
                        raise ValueError("Escreva uma pergunta de até 1.000 caracteres.")
                    plan = plan_query(question, dataset["schema"])
                    mode = "Consulta planejada por IA"
                if plan["clarification"]:
                    self.send({"clarification": plan["clarification"], "mode": mode})
                    return
                result = query(dataset, plan["sql"])
                result.update({"question": question, "mode": mode,
                               "summary": f"Consulta executada sobre {len(dataset['rows'])} registros. Resultado apresentado abaixo."})
                self.send(result)
            else:
                self.send({"error": "Rota inexistente."}, 404)
        except (ValueError, binascii.Error) as error:
            self.send({"error": str(error)}, 400)
        except Exception:
            self.send({"error": "Falha interna ao processar a solicitação."}, 500)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    app = AppServer(("127.0.0.1", args.port))
    print(f"Assistente disponível em http://127.0.0.1:{args.port}")
    try:
        app.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        app.server_close()
