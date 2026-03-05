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
    result = random.choice(["1分", "5分", "10分", "1時間", "1日","1週間","3週間","一か月","半年","一年","追放"])
    await interaction.response.send_message(result)

@client.event
async def on_ready():
    await tree.sync()
    print(f"ログインしました: {client.user}")

client.run(TOKEN)

