import random
import discord
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")  # Render用

intents = discord.Intents.default()
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

@tree.command(name="to", description="toするかしないかを決めます")
async def to(interaction: discord.Interaction):
    result = random.choice(["toする", "toしない" ])
    await interaction.response.send_message(result)

@tree.command(name="totime", description="時間をランダムで決めます")
async def totime(interaction: discord.Interaction):
    n = random.randint(1,86400)
    result = random.choice([str(n) + "秒","追放",str(n) + "秒",str(n) + "秒",str(n) + "秒",])
    await interaction.response.send_message(result)

@tree.command(name="cc",description="既存48コースの中から一つコースを選びます")
async def cc(interaction: discord.Interaction):
    course_list = ["mks","wp","ssc","tr","mc","th","tm","sgf","sa","ds","ed","mw","cc","bdd","bc","rr","yc","ea","dd","dmc",
    "bp","cl","ww","ac","rmmm","rmc","rccb","rtt","rddd","rdp3","rRRy","rdkj","rwc","rsl","rmp","ryv","rttc","rpps","rgv",
    "rrrd","dwgm","drr","diio","dhc","dnbc","drir","dsbs","dbb"]
    result = random.choice(course_list)
    await interaction.response.send_message(result)

@client.event
async def on_ready():
    await tree.sync()
    print(f"ログインしました: {client.user}")

client.run(TOKEN)

