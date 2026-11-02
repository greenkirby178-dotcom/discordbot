import asyncio
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

@client.event
async def on_message(message):

    # DMとBotの発言は対象外
    if message.guild is None or message.author.bot:
        return

    role = discord.utils.get(message.guild.roles, name="チャット規制")

    if role is not None and role in message.author.roles:
        try:
            await message.delete()
        except discord.Forbidden:
            pass

@tree.command(
    name="chatmute",
    description="指定したユーザーをチャット規制します"
)
@app_commands.guild_only()
@app_commands.describe(
    member="規制するユーザー",
    minutes="規制時間(分)"
)
async def chatmute(
    interaction: discord.Interaction,
    member: discord.Member,
    minutes: int
):
    # 管理者または「二刀流モデレーター」ロールを持っているか確認
    moderator_role = discord.utils.get(interaction.guild.roles, name="二刀流モデレーター")

    is_admin = interaction.user.guild_permissions.administrator
    is_moderator = moderator_role in interaction.user.roles if moderator_role else False

    if not (is_admin or is_moderator):
        await interaction.response.send_message(
            "❌ このコマンドを使用する権限がありません。",
            ephemeral=True
        )
        return
    # 規制時間のチェック
    if minutes < 1 or minutes > 60:
        await interaction.response.send_message(
            "❌ 規制時間は1〜60分の間で指定してください。",
            ephemeral=True
        )
        return
    role = discord.utils.get(interaction.guild.roles, name="チャット規制")

    if role is None:
        await interaction.response.send_message(
            "❌ 『チャット規制』ロールが見つかりません。",
            ephemeral=True
        )
        return

    if role in member.roles:
        await interaction.response.send_message(
            "⚠️ そのユーザーは既にチャット規制中です。",
            ephemeral=True
        )
        return

    await interaction.response.defer()

    try:
        await member.add_roles(role)

    except discord.Forbidden:
        await interaction.followup.send(
            "❌ ロールを付与できません。\nBotのロール順位を確認してください。",
            ephemeral=True
        )
        return

    await interaction.followup.send(
        f"🚫 {member.mention} はチャット規制を受けました。\n"
        f"**{minutes}分間** {member.display_name} のチャットを規制します。"
    )

    # 指定時間待機
    await asyncio.sleep(minutes * 60)

    # 最新のメンバー情報を取得
    member = await interaction.guild.fetch_member(member.id)

    # まだロールが付いていれば解除
    if role in member.roles:

        try:
            await member.remove_roles(role)

            await interaction.channel.send(
                f"✅ {member.mention} のチャット規制を解除しました。"
            )

        except discord.Forbidden:
            pass

@chatmute.error
async def chatmute_error(interaction: discord.Interaction, error):

    if isinstance(error, app_commands.MissingPermissions):
        await interaction.response.send_message(
            "❌ このコマンドは管理者のみ使用できます。",
            ephemeral=True
        )
    else:
        print(error)

client.run(TOKEN)

