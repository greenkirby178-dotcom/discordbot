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

client.run(TOKEN)
