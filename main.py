from datetime import datetime, timedelta
import discord
from discord import Embed

def create_prediction_embed(hispana_data, rival_data, past_days=7, future_days=14):
    # hispana_data y rival_data pueden ser tuplas o diccionarios con: (nombre, posicion, valor_actual, crecimiento_diario)
    h_name, h_pos, h_val, h_growth = hispana_data
    r_name, r_pos, r_val, r_growth = rival_data
    
    # Cálculos
    distancia = r_val - h_val
    velocidad_neta = h_growth - r_growth
    
    embed = Embed(
        title=f"Prediction between {h_name} and {r_name}", 
        color=discord.Color.green()
    )
    
    # Cabecera de metadatos
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
    
    embed.set_footer(text="⭐ Developed for HISPANA Alliance ⭐")
    return embed
