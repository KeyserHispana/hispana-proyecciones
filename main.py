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

# --- Función para leer y parsear los archivos de texto con FECHA ---
def cargar_datos_desde_txt(nombre_archivo):
    datos = {}
    fecha_str = None
    
    if not os.path.exists(nombre_archivo):
        return fecha_str, datos
    
    with open(nombre_archivo, 'r', encoding='utf-8') as f:
        lineas = f.readlines()
        
    nombre_actual = None
    for linea in lineas:
        linea = linea.strip()
        if not linea:
            continue
            
        # Extraer la fecha si está en la línea
        if linea.lower().startswith('fecha:'):
            fecha_str = linea.split(':')[1].strip()
            continue
            
        if linea.startswith('$'):
            try:
                valor_limpio = int(float(linea.replace('$', '').replace(',', '')))
                if nombre_actual:
                    datos[nombre_actual] = valor_limpio
            except ValueError:
                pass
        elif not linea.startswith('Flights:') and not linea.startswith('Airlines:') and not linea.startswith('Previsión') and not linea.startswith('Siguiente'):
            nombre_actual = linea
            
    return fecha_str, datos

# --- Función para encontrar el nombre exacto usando aproximación ---
def buscar_nombre_alianza(nombre_buscado, diccionario_datos):
    if nombre_buscado in diccionario_datos:
        return nombre_buscado
    
    # Buscar la coincidencia más cercana
    coincidencias = get_close_matches(nombre_buscado, diccionario_datos.keys(), n=1, cutoff=0.4)
    if coincidencias:
        return coincidencias[0]
    return None

# --- Función para calcular días transcurridos usando las fechas de los TXT ---
def calcular_dias_entre_archivos(fecha_pasada, fecha_actual):
    formato = "%Y-%m-%d"
    try:
        f_pasada = datetime.strptime(fecha_pasada, formato)
        f_actual = datetime.strptime(fecha_actual, formato)
        dias = (f_actual - f_pasada).days
        return max(1, dias) # Evitar división por cero si ponen la misma fecha
    except (ValueError, TypeError):
        # Fallback en caso de que escriban mal la fecha
        return 14

# --- Configuración del Bot ---
intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f"Bot conectado como {bot.user}")

# --- Comando de Proyección Automática con Múltiples Rivales ---
@bot.command(name='comparar')
async def comparar(ctx, h_name: str, *r_names):
    # Límite máximo de 5 rivales a comparar.
    if len(r_names) > 5:
        await ctx.send("⚠️ Por favor, ingresa un máximo de 5 alianzas rivales a comparar.")
        return
    
    if len(r_names) == 0:
        await ctx.send("⚠️ Debes incluir al menos una alianza rival. Ejemplo: `!comparar Hispana FAME`")
        return

    fecha_pasada, datos_pasados = cargar_datos_desde_txt('pasados.txt')
    fecha_actual, datos_actuales = cargar_datos_desde_txt('actuales.txt')
    
    if not datos_actuales:
        await ctx.send("⚠️ El archivo `actuales.txt` está vacío o no se encuentra en el repositorio.")
        return
        
    if not fecha_pasada or not fecha_actual:
        await ctx.send("⚠️ Falta la fecha en los archivos. Asegúrate de que la primera línea diga `Fecha: AAAA-MM-DD`.")
        return
        
    # Resolver nombre de tu alianza
    h_key = buscar_nombre_alianza(h_name, datos_actuales)
    if not h_key:
        await ctx.send(f"⚠️ No se encontró la alianza base: `{h_name}`.")
        return
    
    # Resolver nombres de las alianzas rivales
    rivales_encontrados = []
    rivales_faltantes = []
    
    for r_name in r_names:
        r_key = buscar_nombre_alianza(r_name, datos_actuales)
        if r_key:
            rivales_encontrados.append(r_key)
        else:
            rivales_faltantes.append(r_name)
    
    if rivales_faltantes:
        await ctx.send(f"⚠️ No se encontraron las siguientes alianzas: `{', '.join(rivales_faltantes)}`")
        if not rivales_encontrados:
            return

    # Cálculo exacto de días transcurridos
    dias_analizados = calcular_dias_entre_archivos(fecha_pasada, fecha_actual)
    future_days = 14 # Proyección estándar a futuro

    h_val = datos_actuales[h_key]
    h_val_pasado = datos_pasados.get(h_key, h_val)
    h_growth = round((h_val - h_val_pasado) / dias_analizados, 2)
    h_projected = h_val + (h_growth * future_days)

    # Lógica de Ranking de Crecimiento Diario Global
    crecimientos_globales = []
    for alianza, val_actual in datos_actuales.items():
        val_pasado = datos_pasados.get(alianza, val_actual)
        crecimiento = round((val_actual - val_pasado) / dias_analizados, 2)
        crecimientos_globales.append((alianza, crecimiento))
         
    crecimientos_globales.sort(key=lambda x: x[1], reverse=True)
    hispana_rank = next((i + 1 for i, x in enumerate(crecimientos_globales) if x[0] == h_key), "N/A")

    embed = Embed(
        title=f"📊 Proyección: {h_key} vs Rivales", 
        color=discord.Color.green()
    )
    
    embed.description = (
        f"📅 Período: **{fecha_pasada}** a **{fecha_actual}** ({dias_analizados} días)\n"
        f"🎯 Proyección a futuro: **{future_days} días**\n"
        f"🏆 **Ranking Global de Crecimiento Diario ({h_key}): #{hispana_rank}**"
    )
    
    embed.add_field(
        name=f"🔵 {h_key} (Base)",
        value=f"**Valor:** ${h_val:,} | **CD:** +${h_growth:,.0f} | **Proy:** ${h_projected:,.0f}",
        inline=False
    )
    
    # Añadir rivales al embed en formato compacto
    for r_key in rivales_encontrados:
        r_val = datos_actuales[r_key]
        r_val_pasado = datos_pasados.get(r_key, r_val)
        r_growth = round((r_val - r_val_pasado) / dias_analizados, 2)
        r_projected = r_val + (r_growth * future_days)
        
        distancia = r_val - h_val
        velocidad_neta = h_growth - r_growth
        
        if velocidad_neta > 0:
            dias_necesarios = distancia / velocidad_neta
            fecha_estimada = datetime.now() + timedelta(days=dias_necesarios)
            resultado = f"⏳ Las pasaremos en **{dias_necesarios:.1f}** días ({fecha_estimada.strftime('%d %b %Y')})"
        else:
            resultado = "⚠️ Rival más rápido o igual. No los alcanzaremos a este ritmo."
             
        embed.add_field(
            name=f"🔴 {r_key}",
            value=f"**Valor:** ${r_val:,} | **CD:** +${r_growth:,.0f} | **Proy:** ${r_projected:,.0f}\n{resultado}",
            inline=False
        )

    embed.set_footer(text="⭐ Developed by HISPANA Alliance ⭐")
    await ctx.send(embed=embed)

keep_alive()
bot.run(os.environ['PROJECTION_BOT_TOKEN'])
