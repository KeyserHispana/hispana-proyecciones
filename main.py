from flask import Flask
from threading import Thread
import os
import sqlite3
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord import Embed

# --- Servidor Flask para UptimeRobot ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Proyecciones con Base de Datos activo 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Configuración de la Base de Datos SQLite ---
def init_db():
    conn = sqlite3.connect('hispana_data.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            position INTEGER,
            value INTEGER,
            date TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- Configuración del Bot ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# --- Comando para registrar datos (extraídos de tus fotos) ---
@bot.command(name='registrar')
async def registrar(ctx, name: str, position: int, value: int):
    conn = sqlite3.connect('hispana_data.db')
    cursor = conn.cursor()
    fecha_hoy = datetime.now().strftime("%Y-%m-%d")
    
    cursor.execute("INSERT INTO records (name, position, value, date) VALUES (?, ?, ?, ?)",
                   (name, position, value, fecha_hoy))
    conn.commit()
    conn.close()
    
    await ctx.send(f"✅ Registro guardado: **{name}** | Pos: {position} | Puntos: {value} ({fecha_hoy})")

# --- Comando de Proyección Automática usando la Base de Datos ---
@bot.command(name='compare_predict')
async def compare_predict(ctx, h_name: str, r_name: str, future_days: int = 14):
    conn = sqlite3.connect('hispana_data.db')
    cursor = conn.cursor()
    
    def get_latest_and_past(alliance_name):
        # Obtener el registro más reciente
        cursor.execute("SELECT position, value, date FROM records WHERE name = ? ORDER BY date DESC LIMIT 1", (alliance_name,))
        latest = cursor.fetchone()
        
        # Obtener un registro de hace ~7 días
        cursor.execute("SELECT value, date FROM records WHERE name = ? AND date <= date('now', '-6 days') ORDER BY date DESC LIMIT 1", (alliance_name,))
        past = cursor.fetchone()
        return latest, past

    h_latest, h_past = get_latest_and_past(h_name)
    r_latest, r_past = get_latest_and_past(r_name)
    conn.close()
    
    if not h_latest or not r_latest:
        await ctx.send("⚠️ Faltan datos registrados para una de las alianzas. Usa `!registrar` primero.")
        return
        
    h_pos, h_val, h_date = h_latest
    r_pos, r_val, r_date = r_latest
    
    # Calcular crecimiento diario basado en el histórico si existe
    if h_past:
        h_diff_days = max(1, (datetime.strptime(h_date, "%Y-%m-%d") - datetime.strptime(h_past[1], "%Y-%m-%d")).days)
        h_growth = round((h_val - h_past[0]) / h_diff_days, 2)
        past_days_analyzed = h_diff_days
    else:
        h_growth = 0.0
        past_days_analyzed = 7

    if r_past:
        r_diff_days = max(1, (datetime.strptime(r_date, "%Y-%m-%d") - datetime.strptime(r_past[1], "%Y-%m-%d")).days)
        r_growth = round((r_val - r_past[0]) / r_diff_days, 2)
    else:
        r_growth = 0.0

    distancia = r_val - h_val
    velocidad_neta = h_growth - r_growth
    
    embed = Embed(
        title=f"Prediction between {h_name} and {r_name}", 
        color=discord.Color.green()
    )
    
    embed.description = f"Past days analyzed: **{past_days_analyzed}**\nFuture days projected: **{future_days}**"
    
    # Columna Izquierda
    h_projected = h_val + (h_growth * future_days)
    embed.add_field(
        name=f"{h_name} (lower value)",
        value=f"Position: **{h_pos}**\nCurrent value: **{h_val}**\nDaily growth: **{h_growth}**\nProjected value: **{h_projected:.1f}**",
        inline=True
    )
    
    # Columna Derecha
    r_projected = r_val + (r_growth * future_days)
    embed.add_field(
        name=f"{r_name} (higher value)",
        value=f"Position: **{r_pos}**\nCurrent value: **{r_val}**\nDaily growth: **{r_growth}**\nProjected value: **{r_projected:.1f}**",
        inline=True
    )
    
    # Resultados
    if velocidad_neta > 0:
        dias_necesarios = distancia / velocidad_neta
        fecha_estimada = datetime.now() + timedelta(days=dias_necesarios)
        fecha_texto = fecha_estimada.strftime("%d %b %Y")
        resultado_texto = f"⏳ Estimated days to overtake: **{dias_necesarios:.1f}**\n📅 Estimated date: **{fecha_texto}**"
    else:
        resultado_texto = "⚠️ El rival mantiene mayor o igual velocidad de crecimiento."

    embed.add_field(
        name="Result",
        value=resultado_texto,
        inline=False
    )
    
    embed.set_footer(text="⭐ Developed by HISPANA Alliance ⭐")
    await ctx.send(embed=embed)

keep_alive()
bot.run(os.environ['PROJECTION_BOT_TOKEN'])
