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
    if message.guild is None or message.author.bot or message.webhook_id is not None:
        return

    role = discord.utils.get(message.guild.roles, name="チャット規制")

    if role is not None and role in message.author.roles:
        try:
            await message.delete()
        except discord.Forbidden:
            pass
        return

    try:
        await asyncio.to_thread(points_store.record_chat, message.guild.id, message.author.id, message.id)
    except sqlite3.Error as error:
        print(f"Chat reward failed: {error}")
    if await handle_points_prefix(message):
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
VALID_CAPACITIES = (2, 3, 4, 6, 8, 12)
CAPACITY_COLOURS = {
    2: 0xFF0000,   # 赤
    3: 0xFF8000,   # オレンジ
    4: 0xFFFF00,   # 黄色
    6: 0x00FF00,   # 緑
    8: 0x0080FF,   # 青
    12: 0xA000FF,  # 紫
}
table_states = {}
table_locks = {}


def table_embed_list(slots, statuses=None, capacity=6):
    statuses = statuses or {}
    embeds = []
    embed = discord.Embed(title=f"{capacity}v{capacity} War List", colour=discord.Colour(CAPACITY_COLOURS[capacity]))
    for number, users in sorted(slots.items()):
        if len(embed.fields) == 25:
            embeds.append(embed)
            embed = discord.Embed(title=f"{capacity}v{capacity} War List（続き）", colour=discord.Colour(CAPACITY_COLOURS[capacity]))
        labels = statuses.get(number, {})
        regular_count = sum(labels.get(uid, "regular") == "regular" for uid in users)
        extra_count = len(users) - regular_count
        heading = f"{number}@{max(0, capacity - regular_count)}"
        if extra_count:
            heading += f" ({extra_count})"
        lines = []
        for uid in users:
            status = labels.get(uid, "regular")
            if status == "substitute":
                lines.append(f"> (補<@{uid}>)")
            elif status == "tentative":
                lines.append(f"> (仮<@{uid}>)")
            else:
                lines.append(f"> <@{uid}>")
        value = "\n".join(lines) or "参加者なし"
        if len(value) > 1024:
            raise ValueError("この時間の欄は表示上限に達しています。")
        embed.add_field(name=heading, value=value, inline=False)
    if not slots:
        embed.description = "まだ挙手はありません。`/c 数字` または `!arc 数字` で参加できます。"
    embed.set_footer(text=TABLE_FOOTER)
    embeds.append(embed)
    if sum(len(e) for e in embeds) > 5900:
        raise ValueError("テーブルが表示上限に達しました。/mcd でリセットしてください。")
    return embeds


def is_signup_table(message):
    return (
        message.author.id == client.user.id
        and any(re.fullmatch(r"(2v2|3v3|4v4|6v6|8v8|12v12) War List(?:（続き）)?", e.title or "")
                and e.footer.text in (TABLE_FOOTER, "補欠: Substitute, 仮: Tentative")
                for e in message.embeds)
    )


async def remove_extra_tables(channel, keep):
    # このBot自身の募集枠だけを対象に、過去に残った重複枠も整理する。
    async for message in channel.history(limit=100):
        if message.id == keep.id or not is_signup_table(message):
            continue
        try:
            await message.delete()
        except discord.NotFound:
            pass


async def get_table_state(channel):
    if channel.id in table_states:
        return table_states[channel.id]
    state = {"active": False, "message": None, "slots": {}, "statuses": {}, "capacity": 6}
    async for message in channel.history(limit=100):
        if (message.author.id == client.user.id
                and message.content.endswith("がこのチャンネルの募集テーブルを削除しました。")):
            break
        if not is_signup_table(message):
            continue
        state["message"] = message
        state["active"] = True
        state["capacity"] = int(re.match(r"(\d+)v", message.embeds[0].title).group(1))
        for embed in message.embeds:
            for field in embed.fields:
                number = int(field.name.split("@")[0])
                state["slots"][number] = [int(x) for x in re.findall(r"<@!?(\d+)>", field.value)]
                state["statuses"][number] = {
                    int(uid): {"補": "substitute", "仮": "tentative"}.get(mark, "regular")
                    for mark, uid in re.findall(r"(補|仮)?<@!?(\d+)>", field.value)
                }
        break
    if state["message"] is not None:
        await remove_extra_tables(channel, state["message"])
    table_states[channel.id] = state
    return state


async def create_table(channel, capacity=6):
    if capacity not in VALID_CAPACITIES:
        raise ValueError("募集人数は2・3・4・6・8・12から選んでください。")
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        if state["active"]:
            current_capacity = state.get("capacity", 6)
            if capacity != current_capacity and not any(state["slots"].values()):
                state["capacity"] = capacity
                try:
                    await update_table(channel, state, {})
                except Exception:
                    state["capacity"] = current_capacity
                    raise
                return f"募集形式を{capacity}v{capacity}に変更しました。"
            await remove_extra_tables(channel, state["message"])
            if capacity != current_capacity:
                return (f"既に{current_capacity}v{current_capacity}で募集中です。参加者がいるため形式を変更できません。"
                        f" /mcd または !armcd で削除してから、!armc {capacity} または /mc で作成してください。")
            return f"既に{current_capacity}v{current_capacity}の募集テーブルがあります。再表示は /now または !arnow を使ってください。"
        previous_capacity = state.get("capacity", 6)
        state["capacity"] = capacity
        try:
            await update_table(channel, state, {})
        except Exception:
            state["capacity"] = previous_capacity
            raise
        state["active"] = True
        return f"{capacity}v{capacity}の挙手テーブルを作成しました。"


def regular_users(slots, statuses, number):
    return [uid for uid in slots.get(number, [])
            if statuses.get(number, {}).get(uid, "regular") == "regular"]


signup_role_locks = {}
signup_role_usage = {}


async def sync_signup_roles(channel, slots):
    """AR数字ロールを、同じサーバー内の全募集の参加者と同期する。"""
    guild = channel.guild
    async with signup_role_locks.setdefault(guild.id, asyncio.Lock()):
        if guild.id not in signup_role_usage:
            # 再起動後も別チャンネルで使用中のロールを消さないよう復元する。
            usage = {}
            candidates = {c.id: c for c in [*guild.text_channels, *guild.threads, channel]}
            for candidate in candidates.values():
                permissions = candidate.permissions_for(guild.me)
                if not (permissions.view_channel and permissions.read_message_history):
                    continue
                recovered = await get_table_state(candidate)
                if recovered["active"]:
                    usage[candidate.id] = {n: set(users) for n, users in recovered["slots"].items()}
            signup_role_usage[guild.id] = usage
        usage = signup_role_usage[guild.id]
        before = {}
        for table in usage.values():
            for number, users in table.items():
                before.setdefault(number, set()).update(users)
        proposed = dict(usage)
        proposed[channel.id] = {n: set(users) for n, users in slots.items()}
        desired = {}
        for table in proposed.values():
            for number, users in table.items():
                desired.setdefault(number, set()).update(users)
        numbers = set(before) | set(desired)
        if not numbers:
            usage[channel.id] = proposed[channel.id]
            return
        if not guild.me.guild_permissions.manage_roles:
            raise ValueError("❌ Botに『ロールの管理』権限を付けてください。")
        roles = {role.name: role for role in await guild.fetch_roles()}
        for number in numbers:
            role = roles.get(f"AR{number}")
            if role is not None and (role.managed or role >= guild.me.top_role or role.permissions.value != 0):
                raise ValueError(f"❌ AR{number}を管理できません。Botより下の、権限を持たない通常ロールにしてください。")
        members = {}
        async def member_for(uid):
            if uid not in members:
                try:
                    members[uid] = await guild.fetch_member(uid)
                except discord.NotFound:
                    members[uid] = None
            return members[uid]
        # 作成・付与・取り外しが失敗した場合は、可能な限り変更を戻す。
        undo = []
        created = []
        try:
            for number in sorted(numbers):
                wanted = desired.get(number, set())
                role = roles.get(f"AR{number}")
                if wanted and role is None:
                    role = await guild.create_role(
                        name=f"AR{number}", permissions=discord.Permissions.none(),
                        mentionable=False, reason="募集参加者の自動ロール"
                    )
                    roles[role.name] = role
                    created.append(role)
                if role is None:
                    continue
                for uid in sorted(wanted):
                    member = await member_for(uid)
                    if member is None:
                        raise ValueError("❌ 対象メンバーがサーバーに見つかりません。")
                    if role not in member.roles:
                        await member.add_roles(role, reason="募集への挙手")
                        undo.append((member, role, "remove"))
                for uid in sorted(before.get(number, set()) - wanted):
                    member = await member_for(uid)
                    if member is not None and role in member.roles:
                        await member.remove_roles(role, reason="募集からの退出")
                        undo.append((member, role, "add"))
        except (discord.HTTPException, ValueError) as error:
            for member, role, action in reversed(undo):
                try:
                    if action == "remove":
                        await member.remove_roles(role, reason="募集更新の取り消し")
                    else:
                        await member.add_roles(role, reason="募集更新の取り消し")
                except discord.HTTPException:
                    pass
            for role in created:
                try:
                    await role.delete(reason="募集更新の取り消し")
                except discord.HTTPException:
                    pass
            raise ValueError("❌ 募集ロールの更新に失敗しました。Botのロール管理権限とロール順位を確認してください。") from error
        # 全チャンネルを合わせて0人になった数字だけロールを削除する。
        for number in sorted(numbers):
            role = roles.get(f"AR{number}")
            if not desired.get(number) and role is not None:
                try:
                    await role.delete(reason="募集参加者が0人になったため")
                except discord.NotFound:
                    pass
                except discord.HTTPException as error:
                    raise ValueError(f"❌ AR{number}の削除に失敗しました。Botのロール管理権限と順位を確認してください。") from error
        usage[channel.id] = proposed[channel.id]


async def update_table(channel, state, slots, statuses=None):
    source = state.get("statuses", {}) if statuses is None else statuses
    statuses = {
        number: {uid: source.get(number, {}).get(uid, "regular") for uid in users}
        for number, users in slots.items()
    }
    capacity = state.get("capacity", 6)
    completions = []
    for number in sorted(slots):
        previous = regular_users(state["slots"], state.get("statuses", {}), number)
        current = regular_users(slots, statuses, number)
        if len(previous) < capacity and len(current) == capacity:
            completions.append((number, current))
    embeds = table_embed_list(slots, statuses, capacity)
    # 投稿に失敗しても既存の募集を失わないよう、新しい枠の送信後に古い枠を削除する。
    old_message = state["message"]
    new_message = await channel.send(
        embeds=embeds, allowed_mentions=discord.AllowedMentions.none()
    )
    try:
        await sync_signup_roles(channel, slots)
    except (ValueError, discord.HTTPException):
        try:
            await new_message.delete()
        except discord.HTTPException:
            pass
        raise
    if old_message is not None:
        try:
            await old_message.delete()
        except discord.NotFound:
            pass
        except discord.HTTPException:
            # 古い枠を消せない場合はロールと新規投稿を戻す。
            await sync_signup_roles(channel, state["slots"])
            try:
                await new_message.delete()
            except discord.HTTPException:
                pass
            raise
    state["message"] = new_message
    state["slots"] = slots
    state["statuses"] = statuses
    await remove_extra_tables(channel, new_message)
    for number, users in completions:
        mentions = "、".join(f"<@{uid}>" for uid in users)
        try:
            await channel.send(
                f"{number}にて揃いました！{mentions}",
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=False,
                    users=[discord.Object(id=uid) for uid in users], replied_user=False
                ),
            )
        except discord.HTTPException as error:
            print(f"募集成立通知の送信に失敗しました: {error}")


async def repost_table(channel):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        if not state["active"]:
            raise ValueError("募集テーブルがありません。先に /mc または !armc で作成してください。")
        await update_table(channel, state, state["slots"])


async def join_table(channel, user_id, number, status="regular"):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        if not state["active"]:
            raise ValueError("募集テーブルがありません。先に /mc または !armc で作成してください。")
        capacity = state.get("capacity", 6)
        slots = {key: list(users) for key, users in state["slots"].items()}
        statuses = {key: dict(labels) for key, labels in state.get("statuses", {}).items()}
        users = slots.setdefault(number, [])
        labels = statuses.setdefault(number, {})
        if user_id in users and labels.get(user_id, "regular") == status:
            await update_table(channel, state, state["slots"])
            return f"{number}の欄には既に同じ区分で登録されています。"
        regular_others = sum(labels.get(uid, "regular") == "regular" for uid in users if uid != user_id)
        if status == "regular" and regular_others >= capacity:
            await update_table(channel, state, state["slots"])
            return f"{number}の欄は通常参加の定員{capacity}人に達しています。"
        if user_id not in users:
            users.append(user_id)
        labels[user_id] = status
        await update_table(channel, state, slots, statuses)
        regular_count = sum(labels.get(uid, "regular") == "regular" for uid in users)
        label = {"regular": "通常参加", "substitute": "補欠", "tentative": "仮"}[status]
        return f"{number}の欄に{label}で登録しました。残り{capacity - regular_count}人です。"


async def leave_table(channel, user_id, number):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        if not state["active"]:
            raise ValueError("募集テーブルがありません。先に /mc または !armc で作成してください。")
        capacity = state.get("capacity", 6)
        slots = {key: list(users) for key, users in state["slots"].items()}
        users = slots.get(number, [])
        if user_id not in users:
            await update_table(channel, state, state["slots"])
            return "⚠️ 指定したメンバーはその欄に挙手していません。"
        users.remove(user_id)
        if not users:
            del slots[number]
        await update_table(channel, state, slots)
        regular_count = sum(state.get("statuses", {}).get(number, {}).get(uid, "regular") == "regular" for uid in users)
        return f"{number}の欄から挙手を取り消しました。残り{capacity - regular_count}人です。"


@tree.command(name="mc", description="挙手テーブルを表示します")
@app_commands.guild_only()
@app_commands.describe(mode="募集形式（省略時は6v6）")
@app_commands.choices(mode=[app_commands.Choice(name=f"{n}v{n}", value=n) for n in VALID_CAPACITIES])
async def mc(interaction: discord.Interaction, mode: int = 6):
    await interaction.response.defer(ephemeral=True)
    result = await create_table(interaction.channel, mode)
    await interaction.followup.send(result, ephemeral=True)


@tree.command(name="now", description="現在の募集状態を最新の位置に表示し直します")
@app_commands.guild_only()
async def now(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    try:
        await repost_table(interaction.channel)
        result = "現在の募集状態を表示し直しました。"
    except ValueError as error:
        result = str(error)
    await interaction.followup.send(result, ephemeral=True)


async def reset_table(channel):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        await sync_signup_roles(channel, {})
        # 削除処理の前に受付を停止する。空の枠を作り直さない。
        state["active"] = False
        state["slots"] = {}
        state["statuses"] = {}
        tracked = state["message"]
        if tracked is not None:
            try:
                await tracked.delete()
            except discord.NotFound:
                pass
        state["message"] = None
        # 過去に残った自分の募集枠も取り除く。
        async for message in channel.history(limit=100):
            if not is_signup_table(message):
                continue
            try:
                await message.delete()
            except discord.NotFound:
                pass


@tree.command(name="mcd", description="このチャンネルの募集テーブルを削除し、挙手受付を終了します")
@app_commands.guild_only()
async def mcd(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=False)
    await reset_table(interaction.channel)
    await interaction.followup.send(
        f"🗑️ {interaction.user.mention} がこのチャンネルの募集テーブルを削除しました。",
        ephemeral=False, allowed_mentions=discord.AllowedMentions.none()
    )


@tree.command(name="c", description="指定した数字の欄に挙手します")
@app_commands.guild_only()
@app_commands.describe(number="挙手する欄の数字（0〜48）", member="登録するメンバー（省略すると自分）")
async def c(interaction: discord.Interaction, number: app_commands.Range[int, 0, 48], member: discord.Member | None = None):
    await interaction.response.defer(ephemeral=True)
    try:
        target = member if member is not None else interaction.user
        result = await join_table(interaction.channel, target.id, number)
    except ValueError as error:
        result = str(error)
    await interaction.followup.send(result, ephemeral=True)


@tree.command(name="d", description="指定した数字の欄から挙手を取り消します")
@app_commands.guild_only()
@app_commands.describe(number="取り消す欄の数字（0〜48）", member="取り消すメンバー（省略すると自分）")
async def d(interaction: discord.Interaction, number: app_commands.Range[int, 0, 48], member: discord.Member | None = None):
    await interaction.response.defer(ephemeral=True)
    try:
        target = member if member is not None else interaction.user
        result = await leave_table(interaction.channel, target.id, number)
    except ValueError as error:
        result = str(error)
    await interaction.followup.send(result, ephemeral=True)


@tree.command(name="s", description="指定した数字の欄に補欠で登録します")
@app_commands.guild_only()
@app_commands.describe(number="登録する欄の数字（0〜48）", member="登録するメンバー（省略すると自分）")
async def s(interaction: discord.Interaction, number: app_commands.Range[int, 0, 48], member: discord.Member | None = None):
    await interaction.response.defer(ephemeral=True)
    try:
        target = member if member is not None else interaction.user
        result = await join_table(interaction.channel, target.id, number, "substitute")
    except ValueError as error:
        result = str(error)
    await interaction.followup.send(result, ephemeral=True)


@tree.command(name="t", description="指定した数字の欄に仮で登録します")
@app_commands.guild_only()
@app_commands.describe(number="登録する欄の数字（0〜48）", member="登録するメンバー（省略すると自分）")
async def t(interaction: discord.Interaction, number: app_commands.Range[int, 0, 48], member: discord.Member | None = None):
    await interaction.response.defer(ephemeral=True)
    try:
        target = member if member is not None else interaction.user
        result = await join_table(interaction.channel, target.id, number, "tentative")
    except ValueError as error:
        result = str(error)
    await interaction.followup.send(result, ephemeral=True)


async def clear_table_slot(channel, number):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        if not state["active"]:
            raise ValueError("募集テーブルがありません。先に /mc または !armc で作成してください。")
        capacity = state.get("capacity", 6)
        slots = {key: list(users) for key, users in state["slots"].items()}
        removed = slots.pop(number, [])
        await update_table(channel, state, slots)
        if not removed:
            return f"{number}の欄には参加者がいません。"
        return f"{number}の欄の参加者{len(removed)}人を募集テーブルから削除しました。"


@tree.command(name="out", description="指定した数字の欄の参加者全員を募集テーブルから削除します")
@app_commands.guild_only()
@app_commands.describe(number="削除する欄の数字（0〜48）")
async def out(interaction: discord.Interaction, number: app_commands.Range[int, 0, 48]):
    await interaction.response.defer(ephemeral=True)
    try:
        result = await clear_table_slot(interaction.channel, number)
    except ValueError as error:
        result = str(error)
    await interaction.followup.send(result, ephemeral=True)


def parse_signup_times(text):
    match = re.fullmatch(r"([0-9]+)(?:-([0-9]+))?", text)
    if match is None:
        raise ValueError("時間は0〜48の整数、または `21-23` の形で指定してください。")
    start = int(match.group(1))
    end = int(match.group(2)) if match.group(2) is not None else start
    if not 0 <= start <= end <= 48:
        raise ValueError("時間は0〜48で、開始≦終了になるよう指定してください。")
    return list(range(start, end + 1))


async def apply_prefix_times(channel, command, numbers, user_id=None):
    async with table_locks.setdefault(channel.id, asyncio.Lock()):
        state = await get_table_state(channel)
        if not state["active"]:
            raise ValueError("募集テーブルがありません。先に /mc または !armc で作成してください。")
        capacity = state.get("capacity", 6)
        slots = {key: list(users) for key, users in state["slots"].items()}
        statuses = {key: dict(labels) for key, labels in state.get("statuses", {}).items()}
        for number in numbers:
            if command == "!arout":
                slots.pop(number, None)
                statuses.pop(number, None)
                continue
            if command == "!ard":
                users = slots.get(number, [])
                if user_id in users:
                    users.remove(user_id)
                    statuses.get(number, {}).pop(user_id, None)
                if not users:
                    slots.pop(number, None)
                    statuses.pop(number, None)
                continue
            status = {"!arc": "regular", "!ars": "substitute", "!art": "tentative"}[command]
            users = slots.setdefault(number, [])
            labels = statuses.setdefault(number, {})
            regular_others = sum(labels.get(uid, "regular") == "regular" for uid in users if uid != user_id)
            if status == "regular" and regular_others >= capacity:
                raise ValueError(f"{number}の欄は通常参加の定員{capacity}人です。今回の指定は変更していません。")
            if user_id not in users:
                users.append(user_id)
            labels[user_id] = status
        # 範囲全体を検証後に一度だけ再表示し、途中までの変更を防ぐ。
        await update_table(channel, state, slots, statuses)


async def handle_arc(message):
    try:
        await handle_signup_prefix(message)
    except ValueError as error:
        await message.reply(str(error), mention_author=False)
    except discord.HTTPException:
        await message.reply("❌ 募集を更新できませんでした。Botの権限を確認してください。", mention_author=False)


async def handle_signup_prefix(message):
    parts = message.content.split()
    if not parts or parts[0] not in ("!arc", "!ard", "!ars", "!art", "!arnow", "!armcd", "!armc", "!arout"):
        return
    if parts[0] == "!arout":
        if len(parts) != 2:
            await message.reply("使い方：`!arout 数字` または `!arout 開始-終了`", mention_author=False)
            return
        try:
            numbers = parse_signup_times(parts[1])
            await apply_prefix_times(message.channel, "!arout", numbers)
        except ValueError as error:
            await message.reply(str(error), mention_author=False)
        return
    if parts[0] == "!armc":
        if (len(parts) not in (1, 2)
                or (len(parts) == 2 and (not re.fullmatch(r"[0-9]+", parts[1])
                                        or int(parts[1]) not in VALID_CAPACITIES))):
            await message.reply("使い方：`!armc [2 / 3 / 4 / 6 / 8 / 12]`（省略時は6v6）", mention_author=False)
            return
        capacity = int(parts[1]) if len(parts) == 2 else 6
        result = await create_table(message.channel, capacity)
        if result.startswith("既に"):
            await message.reply(result, mention_author=False)
        return
    if parts[0] == "!armcd":
        if len(parts) != 1:
            await message.reply("使い方：`!armcd`", mention_author=False)
            return
        await reset_table(message.channel)
        await message.reply(
            f"🗑️ {message.author.mention} がこのチャンネルの募集テーブルを削除しました。",
            mention_author=False, allowed_mentions=discord.AllowedMentions.none()
        )
        return
    if parts[0] == "!arnow":
        if len(parts) != 1:
            await message.reply("使い方：`!arnow`", mention_author=False)
            return
        try:
            await repost_table(message.channel)
        except ValueError as error:
            await message.reply(str(error), mention_author=False)
        return
    command = parts[0]
    if len(parts) not in (2, 3):
        await message.reply(f"使い方：`{command} 数字または開始-終了 [@メンバー]`", mention_author=False)
        return
    try:
        numbers = parse_signup_times(parts[1])
    except ValueError as error:
        await message.reply(str(error), mention_author=False)
        return
    target = message.author
    if len(parts) == 3:
        match = re.fullmatch(r"<@!?(\d+)>", parts[2])
        if match is None:
            await message.reply("対象はサーバーのメンバー1人をメンションしてください。", mention_author=False)
            return
        target_id = int(match.group(1))
        target = message.guild.get_member(target_id)
        if target is None:
            try:
                target = await message.guild.fetch_member(target_id)
            except discord.NotFound:
                await message.reply("そのメンバーはこのサーバーにいません。", mention_author=False)
                return
            except discord.HTTPException:
                await message.reply("メンバーを確認できませんでした。もう一度試してください。", mention_author=False)
                return
    try:
        await apply_prefix_times(message.channel, command, numbers, target.id)
    except ValueError as error:
        await message.reply(str(error), mention_author=False)


@tree.error
async def table_command_error(interaction: discord.Interaction, error):
    if interaction.command is None or interaction.command.name not in ("mc", "mcd", "c", "d", "s", "t", "now", "out"):
        print(error)
        return
    original = getattr(error, "original", error)
    if isinstance(original, ValueError):
        text = str(original)
    else:
        text = "❌ テーブルの更新に失敗しました。Botの「チャンネルを見る」「メッセージを送信」「埋め込みリンク」「メッセージ履歴を読む」権限を確認してください。"
    print(f"Table command failed: {original}")
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True)
    else:
        await interaction.response.send_message(text, ephemeral=True)



import unicodedata

COURSE_CODES = {'MBC': 'マリオブラザーズサーキット', 'CC': 'トロフィーシティ', 'WS': 'シュポポコースター', 'DKS': 'DKうちゅうセンター', 'DD': 'サンサンさばく', 'SGB': 'ヘイホーカーニバル', 'WSr': 'ワリオスタジアム', 'AF': 'キラーシップ', 'DKP': 'DKスノーマウンテン', 'SP': 'ロゼッタてんもんだい', 'SHr': 'アイスビルディング', 'WSs': 'ワリオシップ', 'KTB': 'ノコノコビーチ', 'FO': 'リバーサイドサファリ', 'PS': 'ピーチスタジアム', 'PB': 'ピーチビーチ', 'SSS': 'ソルティータウン', 'DDJ': 'ディノディノジャングル', 'GBR': 'ハテナしんでん', 'CCF': 'プクプクフォールズ', 'DDD': 'ショーニューロード', 'BCi': 'おばけシネマ', 'FH': 'ホネホネツイスター', 'MMM': 'モーモーカントリー', 'CM': 'チョコマウンテン', 'TF': 'キノピオファクトリー', 'BC': 'クッパキャッスル', 'AH': 'どんぐりツリーハウス', 'MC': 'マリオサーキット', 'RR': 'レインボーロード'}

def course_key(value):
    return unicodedata.normalize("NFKC", value).strip().casefold()

TO_JAPANESE = {course_key(code): name for code, name in COURSE_CODES.items()}
TO_CODE = {course_key(name): code for code, name in COURSE_CODES.items()}

@tree.command(name="cej", description="英語のコース略称を日本語名に変換します")
@app_commands.describe(course="英語の略称（例：MBC）")
async def cej(interaction: discord.Interaction, course: str):
    await interaction.response.send_message(TO_JAPANESE.get(course_key(course), "該当する略称がありません。"))

@tree.command(name="cje", description="日本語のコース名を英語の略称に変換します")
@app_commands.describe(course="日本語のコース名（例：マリオブラザーズサーキット）")
async def cje(interaction: discord.Interaction, course: str):
    await interaction.response.send_message(TO_CODE.get(course_key(course), "該当するコース名がありません。"))


def course_suggestions(values, current):
    query = course_key(current)
    matches = [value for value in values if query in course_key(value)]
    matches.sort(key=lambda value: not course_key(value).startswith(query))
    return [app_commands.Choice(name=value, value=value) for value in matches[:25]]


@cej.autocomplete("course")
async def suggest_course_code(interaction: discord.Interaction, current: str):
    return course_suggestions(COURSE_CODES, current)


@cje.autocomplete("course")
async def suggest_course_name(interaction: discord.Interaction, current: str):
    return course_suggestions(COURSE_CODES.values(), current)


import sqlite3
import uuid
from contextlib import contextmanager, closing
from pathlib import Path


MAX_HL_POT = 10**12


class PointsStore:
    """Balances, escrow and game progress commit together in one transaction."""
    def __init__(self, path):
        self.path = path
        with self.transaction() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS wallets (
                    guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
                    balance INTEGER NOT NULL CHECK(balance >= 0),
                    PRIMARY KEY(guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS hl_games (
                    id TEXT PRIMARY KEY, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
                    games INTEGER NOT NULL, bet INTEGER NOT NULL,
                    played INTEGER NOT NULL DEFAULT 0, wins INTEGER NOT NULL DEFAULT 0,
                    card INTEGER NOT NULL, active INTEGER NOT NULL DEFAULT 1,
                    result TEXT NOT NULL DEFAULT '',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                CREATE UNIQUE INDEX IF NOT EXISTS hl_one_active
                    ON hl_games(guild_id, user_id) WHERE active=1;
                CREATE TABLE IF NOT EXISTS chat_counts (
                    guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
                    count INTEGER NOT NULL DEFAULT 0,
                    PRIMARY KEY(guild_id, user_id)
                );
                CREATE TABLE IF NOT EXISTS rewarded_messages (
                    message_id INTEGER PRIMARY KEY
                );
                CREATE TABLE IF NOT EXISTS point_history (
                    id INTEGER PRIMARY KEY, guild_id INTEGER NOT NULL, user_id INTEGER NOT NULL,
                    delta INTEGER NOT NULL, reason TEXT NOT NULL, game_id TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
            """)

        self.migrate_streak_reset()

    def migrate_streak_reset(self):
        migration = '2026-11-11-streak-reset-v1'
        # Hold the write lock through backup and reset so the backup is the exact pre-reset state.
        with self.transaction() as db:
            db.execute('CREATE TABLE IF NOT EXISTS point_migrations '
                       '(name TEXT PRIMARY KEY, backup_path TEXT NOT NULL)')
            applied = db.execute('SELECT backup_path FROM point_migrations WHERE name=?', (migration,)).fetchone()
            if applied:
                print(f'Points reset already applied; backup: {applied[0]}', flush=True)
                return
            backup_path = str(Path(self.path).with_name(f'points-before-streak-{uuid.uuid4().hex}.sqlite3'))
            with closing(sqlite3.connect(self.path)) as source, closing(sqlite3.connect(backup_path)) as target:
                source.backup(target)
                if target.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                    raise RuntimeError('ポイントのバックアップ検証に失敗しました。リセットを中止します。')
            columns = {row['name'] for row in db.execute('PRAGMA table_info(hl_games)')}
            if 'pot' not in columns:
                db.execute('ALTER TABLE hl_games ADD COLUMN pot INTEGER NOT NULL DEFAULT 0')
            count = db.execute('SELECT COUNT(*) FROM wallets').fetchone()[0]
            db.execute("INSERT INTO point_history(guild_id,user_id,delta,reason) "
                       "SELECT guild_id,user_id,500-balance,'管理者依頼：500ptにリセット' FROM wallets")
            db.execute('UPDATE wallets SET balance=500')
            db.execute("UPDATE hl_games SET active=0,pot=0,result='ポイントリセットにより終了しました。' WHERE active=1")
            db.execute('DELETE FROM chat_counts')
            db.execute('INSERT INTO point_migrations VALUES (?,?)', (migration, backup_path))
        print(f'Points reset complete: {count} wallets set to 500; games and chat counts reset; backup: {backup_path}', flush=True)

    @contextmanager
    def transaction(self):
        db = sqlite3.connect(self.path, timeout=10)
        db.row_factory = sqlite3.Row
        try:
            db.execute('BEGIN IMMEDIATE')
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    def wallet(self, db, guild_id, user_id):
        inserted = db.execute('INSERT OR IGNORE INTO wallets VALUES (?, ?, 500)',
                              (guild_id, user_id)).rowcount
        if inserted:
            db.execute('INSERT INTO point_history(guild_id,user_id,delta,reason) VALUES (?,?,500,?)',
                       (guild_id, user_id, '初期ポイント'))
        return db.execute('SELECT balance FROM wallets WHERE guild_id=? AND user_id=?',
                          (guild_id, user_id)).fetchone()['balance']

    def change(self, db, game, delta, reason):
        db.execute('UPDATE wallets SET balance=balance+? WHERE guild_id=? AND user_id=?',
                   (delta, game['guild_id'], game['user_id']))
        db.execute('INSERT INTO point_history(guild_id,user_id,delta,reason,game_id) VALUES (?,?,?,?,?)',
                   (game['guild_id'], game['user_id'], delta, reason, game['id']))

    def record_chat(self, guild_id, user_id, message_id):
        with self.transaction() as db:
            # A redelivered message must not award a second point or count twice.
            if not db.execute('INSERT OR IGNORE INTO rewarded_messages VALUES (?)',
                              (message_id,)).rowcount:
                return
            self.wallet(db, guild_id, user_id)
            db.execute('INSERT INTO chat_counts VALUES (?,?,1) '
                       'ON CONFLICT(guild_id,user_id) DO UPDATE SET count=count+1',
                       (guild_id, user_id))
            count = db.execute('SELECT count FROM chat_counts WHERE guild_id=? AND user_id=?',
                               (guild_id, user_id)).fetchone()[0]
            if count % 10 == 0:
                db.execute('UPDATE wallets SET balance=balance+1 WHERE guild_id=? AND user_id=?',
                           (guild_id, user_id))
                db.execute('INSERT INTO point_history(guild_id,user_id,delta,reason) VALUES (?,?,1,?)',
                           (guild_id, user_id, '10チャット報酬'))

    def balance(self, guild_id, user_id):
        with self.transaction() as db:
            available = self.wallet(db, guild_id, user_id)
            held = db.execute('SELECT COALESCE(SUM(pot),0) FROM hl_games '
                              'WHERE guild_id=? AND user_id=? AND active=1',
                              (guild_id, user_id)).fetchone()[0]
            return available, held

    def ranking(self, guild_id):
        with self.transaction() as db:
            return [dict(row) for row in db.execute(
                "SELECT w.user_id, w.balance + COALESCE(g.pot,0) AS points "
                "FROM wallets w LEFT JOIN hl_games g ON g.guild_id=w.guild_id "
                "AND g.user_id=w.user_id AND g.active=1 WHERE w.guild_id=? "
                "ORDER BY points DESC, w.user_id ASC", (guild_id,)
            )]

    def winrate(self, guild_id, user_id):
        with self.transaction() as db:
            row = db.execute(
                "SELECT COUNT(*) AS challenges, COALESCE(SUM(played),0) AS rounds, "
                "COALESCE(SUM(wins),0) AS wins, COALESCE(SUM(pot-bet),0) AS profit "
                "FROM hl_games g WHERE guild_id=? AND user_id=? AND active=0 AND bet>0 AND played>0 "
                "AND result != 'ポイントリセットにより終了しました。' "
                "AND EXISTS (SELECT 1 FROM point_history h WHERE h.game_id=g.id "
                "AND h.reason='High Low 挑戦開始')",
                (guild_id, user_id),
            ).fetchone()
            return dict(row)

    def active_games(self):
        with self.transaction() as db:
            return [dict(row) for row in db.execute('SELECT * FROM hl_games WHERE active=1')]

    def resume(self, guild_id, user_id):
        with self.transaction() as db:
            row = db.execute('SELECT * FROM hl_games WHERE guild_id=? AND user_id=? AND active=1',
                             (guild_id, user_id)).fetchone()
            if row is None:
                raise ValueError('進行中のゲームがありません。/hl で開始してください。')
            return dict(row)

    def start(self, guild_id, user_id, games, bet):
        if not 1 <= games <= 1000 or not 0 <= bet <= 1000000:
            raise ValueError('ゲーム数は1〜1000、賭け額は0〜1,000,000ポイントで指定してください。')
        with self.transaction() as db:
            balance = self.wallet(db, guild_id, user_id)
            if db.execute('SELECT 1 FROM hl_games WHERE guild_id=? AND user_id=? AND active=1',
                          (guild_id, user_id)).fetchone():
                raise ValueError('進行中のゲームがあります。/hlresume で再表示できます。')
            cost = bet
            if balance < cost:
                raise ValueError(f'ポイントが足りません。この挑戦には{cost:,}ptが必要です（利用可能：{balance:,}pt）。')
            game = dict(id=uuid.uuid4().hex, guild_id=guild_id, user_id=user_id)
            db.execute('INSERT INTO hl_games(id,guild_id,user_id,games,bet,card,pot) VALUES (?,?,?,?,?,?,?)',
                       (game['id'], guild_id, user_id, games, bet, random.randint(1, 13), bet))
            self.change(db, game, -cost, 'High Low 挑戦開始')
            return dict(db.execute('SELECT * FROM hl_games WHERE id=?', (game['id'],)).fetchone())

    def answer(self, game_id, user_id, guild_id, expected_round, choice):
        if choice not in ('High', 'Low', 'Stop'):
            raise ValueError('回答が不正です。')
        with self.transaction() as db:
            row = db.execute('SELECT * FROM hl_games WHERE id=?', (game_id,)).fetchone()
            if row is None or row['user_id'] != user_id or row['guild_id'] != guild_id:
                raise ValueError('このゲームは開始した人だけ操作できます。')
            game = dict(row)
            if not game['active'] or game['played'] != expected_round:
                raise ValueError('このボタンは受付済みです。/hlresume で最新の状態を表示してください。')
            if choice == 'Stop':
                if game['played'] == 0:
                    raise ValueError('最初の1回はHighかLowを選んでください。1勝後から確定できます。')
                game['active'] = 0
                game['result'] += f"\n確定しました。{game['pot']:,}ptを受け取ります。"
            else:
                winning_cards = 13 - game['card'] if choice == 'High' else game['card'] - 1
                if winning_cards == 0:
                    raise ValueError('その選択は勝率0%です。もう一方か「確定」を選んでください。')
                next_card = random.choice([n for n in range(1, 14) if n != game['card']])
                won = (next_card > game['card']) == (choice == 'High')
                previous_pot = game['pot']
                game['pot'] = hl_payout(previous_pot, winning_cards) if won else 0
                game['played'] += 1
                game['wins'] += int(won)
                game['active'] = int(won and game['played'] < game['games']
                                     and (game['bet'] == 0 or 0 < game['pot'] < MAX_HL_POT))
                game['result'] = (f"{card_name(game['card'])} → {card_name(next_card)}（{choice}）\n"
                                  + ('✅ 勝ち' if won else '❌ 負け・挑戦分は全ロスト')
                                  + f"\n{previous_pot:,}pt → {game['pot']:,}pt")
                if won and not game['active']:
                    game['result'] += f"\n終了・{game['pot']:,}ptを自動確定しました。"
                game['card'] = random.randint(1, 13)
            if not game['active']:
                self.change(db, game, game['pot'], 'High Low 挑戦精算')
            db.execute('UPDATE hl_games SET played=?,wins=?,card=?,active=?,result=?,pot=? WHERE id=?',
                       (game['played'], game['wins'], game['card'], game['active'], game['result'], game['pot'], game_id))
            return game


points_store = None


def card_name(card):
    return {1: 'A', 11: 'J', 12: 'Q', 13: 'K'}.get(card, str(card))


def hl_payout(pot, winning_cards):
    # Exact integer arithmetic: 95% expected return, including the stake, rounded down.
    return min(MAX_HL_POT, pot * 95 * 12 // (100 * winning_cards))


def points_game_embed(game):
    embed = discord.Embed(title='High & Low 連勝チャレンジ' if game['active'] else 'High & Low 結果', colour=0x00CC66)
    embed.description = (f"<@{game['user_id']}> ・開始時の投入 **{game['bet']:,}pt**\n"
                         f"{game['played']}/{game['games']}回終了・{game['wins']}勝\n"
                         f"現在の挑戦ポイント **{game['pot']:,}pt**\n"
                         f"{'今確定した場合の' if game['active'] else '確定'}収支 **{game['pot']-game['bet']:+,}pt**")
    if game['active']:
        embed.add_field(name=f"第{game['played']+1}ゲーム・今のカード {card_name(game['card'])}",
                        value='勝つと全額を次へ。1回負けると挑戦ポイントは0。1勝後から「確定」で受け取れます。', inline=False)
        for label, count in [('High', 13-game['card']), ('Low', game['card']-1)]:
            value = '選択不可（勝率0%）'
            if count:
                value = f"勝率 {count}/12・勝った場合 **{hl_payout(game['pot'], count):,}pt**（元手込み）"
            embed.add_field(name=label, value=value, inline=False)
    if game['result']:
        embed.add_field(name='直前の結果', value=game['result'], inline=False)
    embed.set_footer(text='期待払戻率95%・端数切捨て｜A=1/K=13・同数再抽選｜上限1兆ptで自動確定｜/hlresumeで再開')
    return embed


class PointsHighLowView(discord.ui.View):
    def __init__(self, game):
        super().__init__(timeout=None)
        self.game = game
        for label, style in [('High', discord.ButtonStyle.success),
                             ('Low', discord.ButtonStyle.primary),
                             ('Stop', discord.ButtonStyle.secondary)]:
            button = discord.ui.Button(label='確定して終了' if label == 'Stop' else label,
                                       style=style, custom_id=f'points_hl:{game["id"]}:{game["played"]}:{label}')
            button.disabled = (
                (label == 'Stop' and game['played'] == 0)
                or (label == 'High' and game['card'] == 13)
                or (label == 'Low' and game['card'] == 1)
            )
            button.callback = self.answer
            self.add_item(button)

    async def answer(self, interaction):
        await interaction.response.defer()
        choice = interaction.data['custom_id'].rsplit(':', 1)[1]
        try:
            game = await asyncio.to_thread(points_store.answer, self.game['id'], interaction.user.id,
                                           interaction.guild_id, self.game['played'], choice)
        except ValueError as error:
            await interaction.followup.send(str(error), ephemeral=True)
            return
        next_view = PointsHighLowView(game) if game['active'] else None
        if next_view:
            client.add_view(next_view)
        # The result is already durable. A failed Discord edit can be recovered with /hlresume.
        await interaction.edit_original_response(embed=points_game_embed(game), view=next_view)
        self.stop()

    async def on_error(self, interaction, error, item):
        print(f'Points game error: {type(error).__name__}: {error}')
        await interaction.followup.send('表示の更新に失敗しました。/points balance と /hlresume で保存済みの状態を確認してください。', ephemeral=True)


@client.event
async def setup_hook():
    global points_store
    path = Path(os.getenv('POINTS_DB_PATH', '/var/data/points.sqlite3'))
    # Fail closed if the persistent disk is missing; never create an ephemeral wallet database.
    if not path.parent.is_dir():
        raise RuntimeError('ポイント保存先がありません。/var/data に永続ディスクを設定してください。')
    points_store = await asyncio.to_thread(PointsStore, str(path))
    for game in await asyncio.to_thread(points_store.active_games):
        client.add_view(PointsHighLowView(game))
    print(f'Points database ready: {path}', flush=True)


@tree.command(name='hl', description='High・Lowボタンでポイントを賭けて遊びます')
@app_commands.guild_only()
@app_commands.describe(games='目標の連勝数（1〜1000）', bet='この挑戦に投入するポイント（省略・0なら練習）。1敗で挑戦分全ロスト')
async def hl(interaction: discord.Interaction, games: app_commands.Range[int, 1, 1000],
             bet: app_commands.Range[int, 0, 1000000] = 0):
    await interaction.response.defer()
    try:
        game = await asyncio.to_thread(points_store.start, interaction.guild_id, interaction.user.id, games, bet)
    except ValueError as error:
        await interaction.followup.send(str(error), ephemeral=True)
        return
    view = PointsHighLowView(game)
    client.add_view(view)
    await interaction.followup.send(embed=points_game_embed(game), view=view)


points_group = app_commands.Group(name='points', description='ポイント残高とランキング')
tree.add_command(points_group)


@points_group.command(name='balance', description='自分の所持ポイントを表示します')
@app_commands.guild_only()
async def points(interaction: discord.Interaction):
    await interaction.response.defer(ephemeral=True)
    available, held = await asyncio.to_thread(points_store.balance, interaction.guild_id, interaction.user.id)
    await interaction.followup.send(points_text(available, held), ephemeral=True)



class PointsRankingView(discord.ui.View):
    def __init__(self, owner_id, rows, mode):
        super().__init__(timeout=180)
        self.owner_id = owner_id
        self.rows = rows if mode == 'all' else rows[:int(mode)]
        self.page = 0
        self.lock = asyncio.Lock()
        self.pages = max(1, (len(self.rows) + 19) // 20)
        self.update_buttons()

    def update_buttons(self):
        self.previous.disabled = self.page == 0
        self.next_page.disabled = self.page == self.pages - 1

    def embed(self):
        embed = discord.Embed(title='サーバーポイントランキング', colour=0x00CC66)
        start = self.page * 20
        lines = []
        for index in range(start, min(start + 20, len(self.rows))):
            row = self.rows[index]
            lines.append(f"**{row['rank']}位** <@{row['user_id']}> — **{row['points']:,}pt**")
        embed.description = '\n'.join(lines) or 'ポイント登録済みのメンバーがいません。'
        embed.set_footer(text=f'{self.page+1}/{self.pages}ページ・{len(self.rows)}人｜同点は同順位｜挑戦中のポイント込み・取得時点の順位')
        return embed

    async def move(self, interaction, offset):
        if interaction.user.id != self.owner_id:
            await interaction.response.send_message('ページ操作は実行者のみです。自分で /points ranking または !arpr を使ってください。', ephemeral=True)
            return
        async with self.lock:
            self.page = max(0, min(self.pages - 1, self.page + offset))
            self.update_buttons()
            await interaction.response.edit_message(embed=self.embed(), view=self)

    @discord.ui.button(label='前のページ', style=discord.ButtonStyle.secondary)
    async def previous(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.move(interaction, -1)

    @discord.ui.button(label='次のページ', style=discord.ButtonStyle.secondary)
    async def next_page(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.move(interaction, 1)


async def make_points_ranking(guild, owner_id, mode):
    rows = await asyncio.to_thread(points_store.ranking, guild.id)
    members = []
    previous_points = None
    rank = 0
    for row in rows:
        member = guild.get_member(row['user_id'])
        if member is None:
            try:
                member = await guild.fetch_member(row['user_id'])
            except discord.NotFound:
                continue
        if member.bot:
            continue
        if row['points'] != previous_points:
            rank = len(members) + 1
        row['rank'] = rank
        previous_points = row['points']
        members.append(row)
        if mode != 'all' and len(members) == int(mode):
            break
    return PointsRankingView(owner_id, members, mode)


@points_group.command(name='ranking', description='サーバーのポイントランキングを表示します')
@app_commands.guild_only()
@app_commands.describe(mode='ランキングの表示形式')
@app_commands.choices(mode=[
    app_commands.Choice(name='top5', value='5'),
    app_commands.Choice(name='top10', value='10'),
    app_commands.Choice(name='メンバー全員', value='all'),
])
async def points_ranking(interaction: discord.Interaction, mode: str = '10'):
    await interaction.response.defer()
    view = await make_points_ranking(interaction.guild, interaction.user.id, mode)
    await interaction.followup.send(embed=view.embed(), view=view if view.pages > 1 else None,
                                    allowed_mentions=discord.AllowedMentions.none())


@tree.command(name='hlresume', description='保存されたHigh Lowの続きを表示します')
@app_commands.guild_only()
async def hlresume(interaction: discord.Interaction):
    await interaction.response.defer()
    try:
        game = await asyncio.to_thread(points_store.resume, interaction.guild_id, interaction.user.id)
    except ValueError as error:
        await interaction.followup.send(str(error), ephemeral=True)
        return
    view = PointsHighLowView(game)
    client.add_view(view)
    await interaction.followup.send(embed=points_game_embed(game), view=view)


@tree.command(name='winrate', description='High Lowの勝率と累計収支を表示します')
@app_commands.guild_only()
async def winrate(interaction: discord.Interaction):
    await interaction.response.defer()
    stats = await asyncio.to_thread(points_store.winrate, interaction.guild_id, interaction.user.id)
    await interaction.followup.send(winrate_text(interaction.user.mention, stats),
                                    allowed_mentions=discord.AllowedMentions.none())


@points_ranking.error
@winrate.error
@hl.error
@points.error
@hlresume.error
async def points_command_error(interaction: discord.Interaction, error):
    print(f'Points command error: {error}')
    text = 'ポイント処理に失敗しました。/points balance と /hlresume で状態を確認してください。'
    if interaction.response.is_done():
        await interaction.followup.send(text, ephemeral=True)
    else:
        await interaction.response.send_message(text, ephemeral=True)



def winrate_text(mention, stats):
    rounds = stats['rounds']
    rate = f"{stats['wins'] / rounds * 100:.2f}%" if rounds else '記録なし'
    return (f"**{mention} のHigh & Low成績**\n"
            f"勝率：**{rate}**（{stats['wins']}勝 {rounds-stats['wins']}敗）\n"
            f"累計収支：**{stats['profit']:+,}pt**\n"
            f"終了した挑戦：{stats['challenges']}回・回答：{rounds}回\n"
            "集計対象：ポイントリセット後、このサーバーで終了したポイントを賭けた挑戦。\n"
            "勝率はHigh／Lowの回答ごと、収支は受取額−投入額です。")


def points_text(available, held):
    return (f'所持ポイント：**{available+held:,}pt**\n利用可能：{available:,}pt\n'
            f'挑戦中（未確定）：{held:,}pt\n初回500pt・10チャットで1pt・サーバーごとに保存')


async def handle_points_prefix(message):
    parts = message.content.split()
    if not parts or parts[0] not in ('!arp', '!arhl', '!arhlresume', '!arwr', '!arpr'):
        return False
    try:
        if parts[0] == '!arpr':
            modes = {'top5': '5', 'top10': '10', 'all': 'all', '全員': 'all'}
            if len(parts) > 2 or (len(parts) == 2 and parts[1] not in modes):
                raise ValueError('使い方：`!arpr [top5 / top10 / all]`（省略時はtop10）')
            mode = modes[parts[1]] if len(parts) == 2 else '10'
            view = await make_points_ranking(message.guild, message.author.id, mode)
            await message.reply(embed=view.embed(), view=view if view.pages > 1 else None,
                                mention_author=False, allowed_mentions=discord.AllowedMentions.none())
            return True
        if parts[0] == '!arwr':
            if len(parts) != 1:
                raise ValueError('使い方：`!arwr`')
            stats = await asyncio.to_thread(points_store.winrate, message.guild.id, message.author.id)
            await message.reply(winrate_text(message.author.mention, stats), mention_author=False,
                                allowed_mentions=discord.AllowedMentions.none())
            return True
        if parts[0] == '!arp':
            if len(parts) != 1:
                raise ValueError('使い方：`!arp`')
            available, held = await asyncio.to_thread(points_store.balance, message.guild.id, message.author.id)
            await message.reply(points_text(available, held), mention_author=False)
            return True
        if parts[0] == '!arhlresume':
            if len(parts) != 1:
                raise ValueError('使い方：`!arhlresume`')
            game = await asyncio.to_thread(points_store.resume, message.guild.id, message.author.id)
        else:
            if len(parts) not in (2, 3) or any(not re.fullmatch(r'[0-9]{1,7}', part) for part in parts[1:]):
                raise ValueError('使い方：`!arhl 目標連勝数 [この挑戦への投入額]`（例：`!arhl 10 50`）')
            games = int(parts[1])
            bet = int(parts[2]) if len(parts) == 3 else 0
            game = await asyncio.to_thread(points_store.start, message.guild.id, message.author.id, games, bet)
        view = PointsHighLowView(game)
        client.add_view(view)
        await message.reply(embed=points_game_embed(game), view=view, mention_author=False)
    except ValueError as error:
        await message.reply(str(error), mention_author=False)
    except (sqlite3.Error, discord.HTTPException) as error:
        print(f'Points prefix command failed: {error}')
        await message.reply('処理または表示に失敗しました。!arp と !arhlresume で保存状態を確認してください。',
                            mention_author=False)
    return True


client.run(TOKEN)



