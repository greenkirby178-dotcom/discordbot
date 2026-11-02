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

@tree.command(name="wc", description="MKWorldのコースの中からランダムに一つ選びます")
async def wc(interaction: discord.Interaction):
    course_list = [
        "マリオブラザーズサーキット",
        "トロフィーシティ",
        "シュポポコースター",
        "DKうちゅうセンター",
        "サンサンさばく",
        "ヘイホーカーニバル",
        "ワリオスタジアム",
        "キラーシップ",
        "DKスノーマウンテン",
        "ロゼッタてんもんだい",
        "アイスビルディング",
        "ワリオシップ",
        "ノコノコビーチ",
        "リバーサイドサファリ",
        "ピーチスタジアム",
        "ピーチビーチ",
        "ソルティータウン",
        "ディノディノジャングル",
        "ハテナしんでん",
        "プクプクフォールズ",
        "ショーニューロード",
        "おばけシネマ",
        "ホネホネツイスター",
        "モーモーカントリー",
        "チョコマウンテン",
        "キノピオファクトリー",
        "クッパキャッスル",
        "どんぐりツリーハウス",
        "マリオサーキット",
        "レインボーロード",
        "SFC マリオサーキット 1",
        "SFC マリオサーキット 2",
        "SFC マリオサーキット 3",
        "SFC おばけぬま 1",
        "SFC おばけぬま 2",
        "SFC おばけぬま 3",
        "SFC チョコレーとう 1",
        "SFC チョコレーとう 2",
        "SFC バニラレイク 1",
        "SFC ノコノコビーチ 1",
    ]
    result = random.choice(course_list)
    await interaction.response.send_message(result)

@tree.command(name="dlcc",description="dlc48コースの中から一つコースを選びます")
async def dlcc(interaction: discord.Interaction):
    course_list = ["bpp","btc","bcmo","bcma","btb","bsr","bsg","bnh","bnym","bmc3","bkd","bwp","bsst","bsl","bmg","bshs","bll","bbl","brrm","bmt",
    "bbb","bpg","bmm","brr7","bad","brp","dks","yi","bbr","bmc","bws","bssy","batd","bdcr","bmh","bscs","blal","bsw","bkc",
    "vv","bra","dkm","bdct","bppc","bmd","briw","bbc3","brrw"]
    result = random.choice(course_list)
    await interaction.response.send_message(result)

@tree.command(name="allcc",description="96コースの中から一つコースを選びます")
async def allcc(interaction: discord.Interaction):
    course_list = ["mks","wp","ssc","tr","mc","th","tm","sgf","sa","ds","ed","mw","cc","bdd","bc","rr","yc","ea","dd","dmc",
    "bp","cl","ww","ac","rmmm","rmc","rccb","rtt","rddd","rdp3","rRRy","rdkj","rwc","rsl","rmp","ryv","rttc","rpps","rgv",
    "rrrd","dwgm","drr","diio","dhc","dnbc","drir","dsbs","dbb","bpp","btc","bcmo","bcma","btb","bsr","bsg","bnh","bnym","bmc3","bkd","bwp","bsst","bsl","bmg","bshs","bll","bbl","brrm","bmt",
    "bbb","bpg","bmm","brr7","bad","brp","dks","yi","bbr","bmc","bws","bssy","batd","bdcr","bmh","bscs","blal","bsw","bkc",
    "vv","bra","dkm","ddtc","dppc","bmd","briw","bbc3","brrw"]
    result = random.choice(course_list)
    await interaction.response.send_message(result)


@client.event
async def on_ready():
    await tree.sync()
    print(f"ログインしました: {client.user}")

client.run(TOKEN)

