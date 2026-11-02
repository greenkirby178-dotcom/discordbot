import asyncio
import re
import random
import discord
from discord import app_commands
import os

TOKEN = os.getenv("TOKEN")  # Render用

intents = discord.Intents.default()
intents.message_content = True
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
        return

    await handle_arc(message)

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

@tree.command(name="ms", description="野良模擬をやるかどうかを決めます")
@app_commands.describe(n="1以上の整数（野良模擬をする確率は1/(n+1)）")
async def ms(interaction: discord.Interaction, n: app_commands.Range[int, 1]):
    if n < 1:
        await interaction.response.send_message(
            "❌ nには1以上の整数を指定してください。", ephemeral=True
        )
        return
    result = "野良模擬をする" if random.randrange(n + 1) == 0 else "野良模擬をしない"
    await interaction.response.send_message(result)


TABLE_FOOTER = "補欠: Substitute, 仮: Tentative | AR挙手テーブル"
table_states = {}
table_locks = {}


def table_embed_list(slots):
    embeds = []
    embed = discord.Embed(title="6v6 War List", colour=discord.Colour(0xF1E05A))
    for number, users in sorted(slots.items()):
        if len(embed.fields) == 25:
            embeds.append(embed)
            embed = discord.Embed(title="6v6 War List（続き）", colour=discord.Colour(0xF1E05A))
        embed.add_field(name=f"{number}@{max(0, 6 - len(users))}",
                        value="\n".join(f"> <@{uid}>" for uid in users) or "参加者なし", inline=False)
    if not slots:
        embed.description = "まだ挙手はありません。`/c 数字` または `!arc 数字` で参加できます。"
    embed.set_footer(text=TABLE_FOOTER)
    embeds.append(embed)
    if sum(len(e) for e in embeds) > 5900:
        raise ValueError("テーブルが表示上限に達しました。/md でリセットしてください。")
    return embeds


async def get_table_state(channel):
    if channel.id in table_states:
        return table_states[channel.id]
    state = {"message": None, "slots": {}}
    # 再起動後は、直近100件にある自分のテーブルから参加情報を復元する。
    async for message in channel.history(limit=100):
        if message.author.id != client.user.id or not message.embeds:
            continue
        if not any(e.footer.text == TABLE_FOOTER for e in message.embeds):
            continue
        state["message"] = message
        for embed in message.embeds:
            for field in embed.fields:
                number = int(field.name.split("@")[0])
                state["slots"][number] = [int(x) for x in re.findall(r"<@!?(\d+)>", field.value)]
        break
    table_states[channel.id] = state
    return state


async def update_table(channel, state, slots):
    embeds = table_embed_list(slots)
    # 投稿に失敗しても既存の募集を失わないよう、新しい枠の送信後に古い枠を削除する。
    old_message = state["message"]
    new_message = await channel.send(
        embeds=embeds, allowed_mentions=discord.AllowedMentions.none()
    )
    if old_message is not None:
        try:
            await old_message.delete()
        except discord.NotFound:
            pass
        except discord.HTTPException:
            # 古い枠を消せない場合は新規投稿を取り消し、元の参加情報を保つ。
            try:
                await new_message.delete()
            except discord.HTTPException:
                pass
            raise
    state["message"] = new_message
    state["slots"] = slots


async def repost_table(channel):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        await update_table(channel, state, state["slots"])


async def join_table(channel, user_id, number):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        slots = {key: list(users) for key, users in state["slots"].items()}
        users = slots.setdefault(number, [])
        if user_id in users:
            await update_table(channel, state, state["slots"])
            return f"{number}の欄には既に挙手しています。"
        if len(users) >= 6:
            await update_table(channel, state, state["slots"])
            return f"{number}の欄は定員6人に達しています。"
        users.append(user_id)
        await update_table(channel, state, slots)
        return f"{number}の欄に挙手しました。残り{6 - len(users)}人です。"


@tree.command(name="mc", description="挙手テーブルを表示します")
@app_commands.guild_only()
async def mc(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with table_locks.setdefault(interaction.channel_id, asyncio.Lock()):
        state = await get_table_state(interaction.channel)
        await update_table(interaction.channel, state, state["slots"])
    await interaction.followup.send("挙手テーブルを表示しました。", ephemeral=True)


@tree.command(name="now", description="現在の募集状態を最新の位置に表示し直します")
@app_commands.guild_only()
async def now(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    await repost_table(interaction.channel)
    await interaction.followup.send("現在の募集状態を表示し直しました。", ephemeral=True)


@tree.command(name="md", description="このチャンネルの挙手テーブルをリセットします")
@app_commands.guild_only()
async def md(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    async with table_locks.setdefault(interaction.channel_id, asyncio.Lock()):
        state = await get_table_state(interaction.channel)
        await update_table(interaction.channel, state, {})
    await interaction.followup.send("挙手テーブルをリセットしました。", ephemeral=True)


@tree.command(name="c", description="指定した数字の欄に挙手します")
@app_commands.guild_only()
@app_commands.describe(number="挙手する欄の数字（0〜48）")
async def c(interaction: discord.Interaction, number: app_commands.Range[int, 0, 48]):
    await interaction.response.defer(ephemeral=True)
    try:
        result = await join_table(interaction.channel, interaction.user.id, number)
    except ValueError as error:
        result = str(error)
    await interaction.followup.send(result, ephemeral=True)


async def handle_arc(message):
    parts = message.content.split()
    if not parts or parts[0] not in ("!arc", "!arnow"):
        return
    if parts[0] == "!arnow":
        if len(parts) != 1:
            await message.reply("使い方：`!arnow`", mention_author=False)
            return
        await repost_table(message.channel)
        return
    if len(parts) != 2 or not re.fullmatch(r"[0-9]+", parts[1]) or not 0 <= int(parts[1]) <= 48:
        await message.reply("使い方：`!arc 数字`（0〜48の整数）", mention_author=False)
        return
    try:
        # 更新された枠が返信を兼ねるため、成功後の確認メッセージは送らない。
        await join_table(message.channel, message.author.id, int(parts[1]))
    except ValueError as error:
        await message.reply(str(error), mention_author=False)


@tree.error
async def table_command_error(interaction: discord.Interaction, error):
    if interaction.command is None or interaction.command.name not in ("mc", "md", "c", "now"):
        print(error)
        return
    original = getattr(error, "original", error)
    text = "❌ テーブルの更新に失敗しました。Botの「チャンネルを見る」「メッセージを送信」「埋め込みリンク」「メッセージ履歴を読む」権限を確認してください。"
    print(f"Table command failed: {original}")
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True)
    else:
        await interaction.response.send_message(text, ephemeral=True)



client.run(TOKEN)
