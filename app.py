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

# Rota para Relatório Consolidado por Período
@app.get("/api/relatorio")
def gerar_relatorio(inicio: str, fim: str):
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT 
            SUM(clipp_np) as clipp_np, SUM(clipp_pix) as clipp_pix, SUM(clipp_especie) as clipp_especie, SUM(clipp_cartao) as clipp_cartao,
            SUM(osrecargas_np) as os_np, SUM(osrecargas_pix) as os_pix, SUM(osrecargas_especie) as os_especie, SUM(osrecargas_cartao) as os_cartao,
            SUM(shoficina_np) as sh_np, SUM(shoficina_pix) as sh_pix, SUM(shoficina_especie) as sh_especie, SUM(shoficina_cartao) as sh_cartao,
            SUM(total_geral) as total_periodo
        FROM caixa 
        WHERE data_caixa BETWEEN ? AND ?
    """, (inicio, fim))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row or row["total_periodo"] is None:
        return {"tem_dados": False}
    
    r = dict(row)
    
    # Soma de cada programa
    total_clipp = (r["clipp_np"] or 0) + (r["clipp_pix"] or 0) + (r["clipp_especie"] or 0) + (r["clipp_cartao"] or 0)
    total_os = (r["os_np"] or 0) + (r["os_pix"] or 0) + (r["os_especie"] or 0) + (r["os_cartao"] or 0)
    total_sh = (r["sh_np"] or 0) + (r["sh_pix"] or 0) + (r["sh_especie"] or 0) + (r["sh_cartao"] or 0)
    
    # Soma por meio de pagamento
    tot_np = (r["clipp_np"] or 0) + (r["os_np"] or 0) + (r["sh_np"] or 0)
    tot_pix = (r["clipp_pix"] or 0) + (r["os_pix"] or 0) + (r["sh_pix"] or 0)
    tot_especie = (r["clipp_especie"] or 0) + (r["os_especie"] or 0) + (r["sh_especie"] or 0)
    tot_cartao = (r["clipp_cartao"] or 0) + (r["os_cartao"] or 0) + (r["sh_cartao"] or 0)

    return {
        "tem_dados": True,
        "total_clipp": total_clipp,
        "total_os": total_os,
        "total_sh": total_sh,
        "tot_np": tot_np,
        "tot_pix": tot_pix,
        "tot_especie": tot_especie,
        "tot_cartao": tot_cartao,
        "total_periodo": r["total_periodo"] or 0.0
    }
