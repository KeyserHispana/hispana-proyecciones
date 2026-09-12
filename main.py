from flask import Flask
from threading import Thread
import os
from datetime import datetime, timedelta
from difflib import get_close_matches
import discord
from discord.ext import commands
from discord import Embed

# --- Servidor Flask para UptimeRobot ---
app = Flask('')

@app.route('/')
def home():
    return "Bot de Proyecciones de Alianzas activo 24/7"

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

# --- Función para leer y parsear los archivos de texto ---
def cargar_datos_desde_txt(nombre_archivo):
    datos = {}
    if not os.path.exists(nombre_archivo):
        return datos
    
    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
        
    nombre_actual = None
    for linea in lineas:
        linea = linea.strip()
        if linea.startswith('$'):
            try:
                valor_limpio = int(float(linea.replace('$', '').replace(',', '')))
                if nombre_actual:
                    datos[nombre_actual] = valor_limpio
            except ValueError:
                pass
        elif linea and not linea.startswith('Flights:') and not linea.startswith('Airlines:') and not linea.startswith('Previsión') and not linea.startswith('Siguiente'):
            nombre_actual = linea
            
    return datos

# --- Función para encontrar el nombre exacto usando aproximación ---
def buscar_nombre_alianza(nombre_buscado, diccionario_datos):
    if nombre_buscado in diccionario_datos:
        return nombre_buscado
    
    # Buscar la coincidencia más cercana (cutoff 0.4 permite tolerar errores de escritura o faltas de emojis)
    coincidencias = get_close_matches(nombre_buscado, diccionario_datos.keys(), n=1, cutoff=0.4)
    if coincidencias:
        return coincidencias[0]
    return None

# --- Configuración del Bot ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# --- Comando de Proyección Automática con Búsqueda Inteligente ---
@bot.command(name='compare_predict')
async def compare_predict(ctx, h_name: str, r_name: str, future_days: int = 14):
    datos_pasados = cargar_datos_desde_txt('pasados.txt')
    datos_actuales = cargar_datos_desde_txt('actuales.txt')
    
    if not datos_actuales:
        await ctx.send("⚠️ El archivo `actuales.txt` está vacío o no se encuentra en el repositorio.")
        return
        
    # Resolver nombres con el sistema de coincidencia aproximada
    h_key = buscar_nombre_alianza(h_name, datos_actuales)
    r_key = buscar_nombre_alianza(r_name, datos_actuales)
    
    if not h_key or not r_key:
        missing = []
        if not h_key: missing.append(h_name)
        if not r_key: missing.append(r_name)
        await ctx.send(f"⚠️ No se encontró una coincidencia clara para: `{', '.join(missing)}`. Revisa el texto.")
        return

    # Usar los nombres reales encontrados
    h_val = datos_actuales[h_key]
    r_val = datos_actuales[r_key]
    
    h_val_pasado = datos_pasados.get(h_key, h_val)
    r_val_pasado = datos_pasados.get(r_key, r_val)
    
    dias_analizados = 7 
    h_growth = round((h_val - h_val_pasado) / dias_analizados, 2)
    r_growth = round((r_val - r_val_pasado) / dias_analizados, 2)

    distancia = r_val - h_val
    velocidad_neta = h_growth - r_growth
    
    embed = Embed(
        title=f"Prediction: {h_key} vs {r_key}", 
        color=discord.Color.green()
    )
    
    embed.description = f"Period analyzed: **{dias_analizados} days**\nFuture days projected: **{future_days}**"
    
    h_projected = h_val + (h_growth * future_days)
    embed.add_field(
        name=f"{h_key} (Your Alliance)",
        value=f"Current value: **${h_val:,}**\nDaily growth: **+{h_growth}**\nProjected value: **${h_projected:,.1f}**",
        inline=True
    )
    
    r_projected = r_val + (r_growth * future_days)
    embed.add_field(
        name=f"{r_key} (Rival)",
        value=f"Current value: **${r_val:,}**\nDaily growth: **+{r_growth}**\nProjected value: **${r_projected:,.1f}**",
        inline=True
    )
    
    if velocidad_neta > 0:
        dias_necesarios = distancia / velocidad_neta
        fecha_estimada = datetime.now() + timedelta(days=dias_necesarios)
        fecha_texto = fecha_estimada.strftime("%d %b %Y")
        resultado_texto = f"⏳ Estimated days to overtake: **{dias_necesarios:.1f}**\n📅 Estimated date: **{fecha_texto}**"
    else:
        resultado_texto = "⚠️ El rival mantiene mayor o igual velocidad de crecimiento en este periodo."

    embed.add_field(
        name="Result",
        value=resultado_texto,
        inline=False
    )
    
    embed.set_footer(text="⭐ Developed by HISPANA Alliance ⭐")
    await ctx.send(embed=embed)

keep_alive()
bot.run(os.environ['PROJECTION_BOT_TOKEN'])
