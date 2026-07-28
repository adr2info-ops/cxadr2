from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import sqlite3
import os

app = FastAPI(title="Caixa Diário")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DB_NAME = "caixa_diario.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS caixa (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        data_caixa TEXT UNIQUE NOT NULL,
        
        clipp_np REAL DEFAULT 0.0,
        clipp_pix REAL DEFAULT 0.0,
        clipp_especie REAL DEFAULT 0.0,
        clipp_cartao REAL DEFAULT 0.0,
        
        osrecargas_np REAL DEFAULT 0.0,
        osrecargas_pix REAL DEFAULT 0.0,
        osrecargas_especie REAL DEFAULT 0.0,
        osrecargas_cartao REAL DEFAULT 0.0,
        
        shoficina_np REAL DEFAULT 0.0,
        shoficina_pix REAL DEFAULT 0.0,
        shoficina_especie REAL DEFAULT 0.0,
        shoficina_cartao REAL DEFAULT 0.0,
        
        total_geral REAL DEFAULT 0.0,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

init_db()

class MovimentacaoSchema(BaseModel):
    data_caixa: str
    
    clipp_np: float = 0.0
    clipp_pix: float = 0.0
    clipp_especie: float = 0.0
    clipp_cartao: float = 0.0
    
    osrecargas_np: float = 0.0
    osrecargas_pix: float = 0.0
    osrecargas_especie: float = 0.0
    osrecargas_cartao: float = 0.0
    
    shoficina_np: float = 0.0
    shoficina_pix: float = 0.0
    shoficina_especie: float = 0.0
    shoficina_cartao: float = 0.0

@app.get("/", response_class=HTMLResponse)
def carregar_pagina():
    if os.path.exists("index.html"):
        with open("index.html", "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Arquivo index.html não encontrado!</h1>"

# Rota para Buscar Lançamentos por Data
@app.get("/api/caixa/{data_caixa}")
def buscar_caixa(data_caixa: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM caixa WHERE data_caixa = ?", (data_caixa,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {"encontrado": False}
    
    resultado = dict(row)
    resultado["encontrado"] = True
    return resultado

# Rota para Salvar / Atualizar Caixa
@app.post("/api/caixa")
def salvar_caixa(dados: MovimentacaoSchema):
    total_clipp = dados.clipp_np + dados.clipp_pix + dados.clipp_especie + dados.clipp_cartao
    total_os = dados.osrecargas_np + dados.osrecargas_pix + dados.osrecargas_especie + dados.osrecargas_cartao
    total_sh = dados.shoficina_np + dados.shoficina_pix + dados.shoficina_especie + dados.shoficina_cartao
    
    total_geral = total_clipp + total_os + total_sh
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
        INSERT INTO caixa (
            data_caixa,
            clipp_np, clipp_pix, clipp_especie, clipp_cartao,
            osrecargas_np, osrecargas_pix, osrecargas_especie, osrecargas_cartao,
            shoficina_np, shoficina_pix, shoficina_especie, shoficina_cartao,
            total_geral
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(data_caixa) DO UPDATE SET
            clipp_np=excluded.clipp_np, clipp_pix=excluded.clipp_pix, clipp_especie=excluded.clipp_especie, clipp_cartao=excluded.clipp_cartao,
            osrecargas_np=excluded.osrecargas_np, osrecargas_pix=excluded.osrecargas_pix, osrecargas_especie=excluded.osrecargas_especie, osrecargas_cartao=excluded.osrecargas_cartao,
            shoficina_np=excluded.shoficina_np, shoficina_pix=excluded.shoficina_pix, shoficina_especie=excluded.shoficina_especie, shoficina_cartao=excluded.shoficina_cartao,
            total_geral=excluded.total_geral
        """, (
            dados.data_caixa,
            dados.clipp_np, dados.clipp_pix, dados.clipp_especie, dados.clipp_cartao,
            dados.osrecargas_np, dados.osrecargas_pix, dados.osrecargas_especie, dados.osrecargas_cartao,
            dados.shoficina_np, dados.shoficina_pix, dados.shoficina_especie, dados.shoficina_cartao,
            total_geral
        ))
        conn.commit()
    except Exception as e:
        conn.close()
        raise HTTPException(status_code=500, detail=str(e))
    
    conn.close()
    return {"status": "sucesso", "total_geral": total_geral}
