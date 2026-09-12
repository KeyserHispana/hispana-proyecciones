from flask import Flask
from threading import Thread
import os
from datetime import datetime, timedelta
import discord
from discord.ext import commands
from discord import Embed

# --- Servidor Flask para UptimeRobot (Mantener 24/7) ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Proyecciones activo 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Configuración del Bot de Discord ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Bot de proyecciones conectado como {bot.user}")


# --- Comando de Proyección con Tarjeta Dual ---
@bot.command(name='compare_predict')
async def compare_predict(ctx, h_name: str, r_name: str, h_pos: int, r_pos: int, h_val: int, r_val: int, h_growth: float, r_growth: float, past_days: int = 7, future_days: int = 14):
    
    distancia = r_val - h_val
    velocidad_neta = h_growth - r_growth
    
    embed = Embed(
        title=f"Prediction between {h_name} and {r_name}", 
        color=discord.Color.green()
    )
    
    embed.description = f"Past days analyzed: **{past_days}**\nFuture days projected: **{future_days}**"
    
    # Columna Izquierda (Hispana)
    h_projected = h_val + (h_growth * future_days)
    embed.add_field(
        name=f"{h_name} (lower value)",
        value=f"Position: **{h_pos}**\nCurrent value: **{h_val}**\nDaily growth: **{h_growth}**\nProjected value: **{h_projected:.1f}**",
        inline=True
    )
    
    # Columna Derecha (Rival)
    r_projected = r_val + (r_growth * future_days)
    embed.add_field(
        name=f"{r_name} (higher value)",
        value=f"Position: **{r_pos}**\nCurrent value: **{r_val}**\nDaily growth: **{r_growth}**\nProjected value: **{r_projected:.1f}**",
        inline=True
    )
    
    # Sección de Resultados
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

# Arrancar Flask en segundo plano
keep_alive()

# Ejecutar el Bot con su token seguro en Render
bot.run(os.environ['PROJECTION_BOT_TOKEN'])
