import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta, datetime
from collections import defaultdict
import os
from flask import Flask
from threading import Thread
import time
from pathlib import Path

# ─── CONFIG ────────────────────────────────────────────────
DISCORD_TOKEN = os.environ['discordkey']
GUILD_ID = 1276211173770924065
LOG_CHANNEL_ID = 1457165025931432019
RULES_CHANNEL_ID = 1276492961055637534
MOD_CONTACT_CHANNEL_ID = 1445162538886238419
APPEAL_LINK = "https://appeal.gg/WV3NaANC"

MOD_ROLE_IDS = [1445154830971572254, 1278403720299937853, 1462218720226054295]

AUTOMOD_CHANNEL_ID = 1465090478797230120
AUTOMOD_LOG_CHANNEL_ID = 1465091133158723786
AUTOMOD_FORBIDDEN_WORDS = [
    "porn","nude","nudes","boobs","tits","ass","pussy","cock","dick","cum","xxx","nsfw","fuck","fucked",
    "fucking","slut","whore","dildo","blowjob","anal","vagina","penis","masturbate","cumshot","orgasm",
    "snapchat","instagram","discord.gg","discordapp","phone number","address","location","email",
    "🍑","🍆","💦","👅","🍒","stupid","loser","idiot","bitch","whore","slut","kill yourself","kys",
    "die","cunt", "girls"
]

AUTOMOD_SPAM_LIMIT = 5
AUTOMOD_SPAM_INTERVAL = 5
AUTOMOD_SPAM_TIMEOUT = timedelta(hours=1)
AUTOMOD_FORBIDDEN_CHANNEL_ID = 1465090478797230120
AUTOMOD_WORD_TIMEOUT = timedelta(hours=1)
AUTOMOD_EXCEPT_USER = 1277708926863020122

PROMO_CHANNEL_ID = 1469014593085902890

LEVEL_ROLES = {
    5: 1469012447808454919,
    10: 1469012503714463807,
    20: 1469012567979462803,
    35: 1469013415090716774,
    50: 1469013481968894033
}

LEVEL_RESTRICTIONS = {
    5: {"messages": None, "links": None},
    10: {"messages": 1, "links": None},
    20: {"messages": 1, "links": 1},
    35: {"messages": None, "links": 2},
    50: {"messages": None, "links": None}  # unlimited
}


# ─── INTENTS ───────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

warnings = {}
user_messages = defaultdict(list)

xp_data = {}

XP_PER_MESSAGE = 15
XP_COOLDOWN = 30  # seconds

# ─── MODERATOR RESTRICTION ────────────────────────────────
def mod_only():
    async def predicate(interaction: discord.Interaction):
        guild = bot.get_guild(GUILD_ID)
        member = guild.get_member(interaction.user.id)
        if member is None or not any(role.id in MOD_ROLE_IDS for role in member.roles):
            await interaction.response.send_message(
                "❌ You are not allowed to use this command.",
                ephemeral=True
            )
            return False
        return True
    return app_commands.check(predicate)

# ─── READY ────────────────────────────────────────────────
@bot.event
async def on_ready():
    guild = discord.Object(id=GUILD_ID)
    await bot.tree.sync(guild=guild)
    print(f"{bot.user} is online and commands synced!")

# ─── /W COMMAND ──────────────────────────────────────────
@bot.tree.command(
    name="w",
    description="A little guide for new members!",
    guild=discord.Object(id=GUILD_ID)
)
async def w(interaction: discord.Interaction):
    embed = discord.Embed(
        title="Roles and Events! ✨",
        description=(
            "**Don’t be shy and grab your roles** in <#1276623770009862298> ✨\n"
            "_Only one color role at a time, don’t forget to unreact 🎨_\n\n"
            "**Introduce yourself** in <#1443005501263843371> 💖\n\n"
            "**Check what’s happening rn** in <#1443088173646221403> 👀💫\n\n"
            "Have fun, take your time, and enjoy!! 🤍🎀✨"
        ),
        color=discord.Color.from_str("#C8A2C8")
    )
    await interaction.response.send_message(embed=embed)

# ─── /REMIND COMMAND ─────────────────────────────────────

@bot.tree.command(
    name="remind",
    description="Send a verification reminder to a role",
    guild=discord.Object(id=GUILD_ID)
)
@mod_only()
@app_commands.describe(role="Role to remind")
async def remind(interaction: discord.Interaction, role: discord.Role):
    embed = discord.Embed(
        title="🌸 Verification Reminder 🌸",
        description=(
            f"**Hi {role.mention}** ! 🤍\n\n"
            "Just a little reminder to complete your verification so you can "
            "**unlock the full server and all our channels** ✨\n\n"
            "You can open a verification ticket in <#1278454522922139749> "
            "if it is not already done!\n"
            "Or continue the process through your existing ticket if you’ve already started! 💌\n\n"
            "This step helps us keep the server safe and girl-only, and we really appreciate your patience "
            "and cooperation 🤍\n\n"
            "If you have any questions or need help at any point, don’t hesitate to ask: "
            "we’re happy to help 🫶✨\n"
            "We can’t wait to welcome you fully into the server 🌷"
        ),
        color=discord.Color.from_str("#C8A2C8")
    )

    await interaction.channel.send(embed=embed)
    await interaction.response.send_message(
        f"✅ Reminder sent to {role.mention}.",
        ephemeral=True
    )

# ─── /WARN COMMAND ───────────────────────────────────────
@bot.tree.command(
    name="warn",
    description="Warn a user",
    guild=discord.Object(id=GUILD_ID)
)
@mod_only()
@app_commands.describe(member="User to warn", reason="Reason for warning")
async def warn(interaction: discord.Interaction, member: discord.Member, reason: str):
    blocked_mentions = ["@everyone", "@here", "<@1276450889564946432>", "<@1445154830971572254>"]
    exempt_users = MOD_ROLE_IDS

    if interaction.user.id not in exempt_users:
        for tag in blocked_mentions:
            if tag in reason:
                await interaction.response.send_message(
                    f"❌ Your warning reason cannot contain {tag}.",
                    ephemeral=True
                )
                return

    warnings[member.id] = warnings.get(member.id, 0) + 1
    count = warnings[member.id]
    now = datetime.utcnow()

    if count == 1:
        embed = discord.Embed(
            title="Heads up! You got your first warning.",
            description=(
                f"Hi {member.mention}.\n\n"
                f"You have received **your first warning** in {interaction.guild.name}. "
                "Since it is your first warning, it is nothing for now, but further violations "
                "will result in a temporary ban/kick.\n\n"
                f"You can review the server rules in the <#{RULES_CHANNEL_ID}> channel.\n\n"
                "You think it is unfair or something is missing? Contact the moderators through "
                f"<#{MOD_CONTACT_CHANNEL_ID}> if you have any questions."
            ),
            color=discord.Color.yellow()
        )

    elif count == 2:
        embed = discord.Embed(
            title="Uh-oh! That's your 2nd warning.",
            description=(
                "**Here’s what happens now:**\n\n"
                f"Hi {member.mention}.\n"
                "This time, you’ve **been muted for 1 hour**. "
                "Next warnings may come with stronger actions, so let’s keep things friendly!\n\n"
                f"You can review the server rules in the <#{RULES_CHANNEL_ID}> channel.\n\n"
                f"You think it is unfair or something is missing? Click on this link "
                f"{APPEAL_LINK} to appeal the warning and mute"
            ),
            color=discord.Color.orange()
        )
        await member.timeout(timedelta(hours=1))

    elif count == 3:
        embed = discord.Embed(
            title="Careful, that’s your 3rd warning!",
            description=(
                "**Here’s what happens now:**\n\n"
                f">>> Hi {member.mention}.\n"
                "You’ve been **muted for a day**. "
                "Future warnings could bring tougher actions, so let’s try to keep it cool!\n\n"
                f"You can review the server rules in the <#{RULES_CHANNEL_ID}> channel.\n\n"
                f"You think it is unfair or something is missing? Click on this link "
                f"{APPEAL_LINK} to appeal the warning and mute"
            ),
            color=discord.Color.red()
        )
        await member.timeout(timedelta(days=1))

    elif count == 4:
        embed = discord.Embed(
            title="Yikes! That’s your 4th warning.",
            description=(
                "**Here’s what happens now:**\n\n"
                f">>> Hi {member.mention}.\n"
                "You’ve been **muted for 7 days**. "
                "This is the final warning... Another will result in a kick.\n\n"
                f"You can review the server rules in the <#{RULES_CHANNEL_ID}> channel.\n\n"
                f"You think it is unfair or something is missing? Click on this link "
                f"{APPEAL_LINK} to appeal the warning and mute"
            ),
            color=discord.Color.dark_red()
        )
        await member.timeout(timedelta(days=7))

    else:
        embed = discord.Embed(
            title="You’ve reached the limit on warnings.",
            description=(
                f"Sorry {member.mention}, but **you’ve been kick from** "
                f"{interaction.guild.name} after 4 warnings. Take care!\n\n"
                f"You think it is unfair or something is missing? Click on this link "
                f"{APPEAL_LINK} to appeal the kick"
            ),
            color=discord.Color.from_rgb(0, 0, 0)
        )
        await member.send(embed=embed)
        await member.kick(reason="Exceeded warning limit")
        return

    try:
        await member.send(embed=embed)
    except discord.Forbidden:
        pass

    log_channel = bot.get_channel(LOG_CHANNEL_ID)
    if log_channel:
        report_embed = discord.Embed(
            title="❌ Report",
            color=discord.Color.red(),
            timestamp=now
        )
        report_embed.add_field(
            name="👤 User",
            value=(
                f"**Username:** {member} ({member.mention})\n"
                f"**ID:** `{member.id}`\n"
                f"**Account created:** <t:{int(member.created_at.timestamp())}:F>\n"
                f"**Joined server:** <t:{int(member.joined_at.timestamp())}:F>"
            ),
            inline=False
        )
        report_embed.add_field(name="📌 Reason", value=reason, inline=False)
        report_embed.add_field(name="🛡️ Moderator", value=f"Reported by {interaction.user.mention}", inline=False)
        await log_channel.send(embed=report_embed)

    await interaction.response.send_message(
        f"{member.mention} warned ({count}/5).",
        ephemeral=True
    )

# ─── HELPER FUNCTIONS ─────────────────────────────────────
def get_level(total_xp):
    level = 0
    xp_needed = 100
    while total_xp >= xp_needed:
        level += 1
        total_xp -= xp_needed
        xp_needed = int(xp_needed * 1.3)  # medium-hard scaling
    return level, total_xp, xp_needed

# ─── /RANK COMMAND ───────────────────────────────────────
@bot.tree.command(
    name="rank",
    description="See your current level and XP",
    guild=discord.Object(id=GUILD_ID)
)
async def rank(interaction: discord.Interaction):
    user_id = interaction.user.id
    if user_id not in xp_data:
        await interaction.response.send_message("You have no XP yet!", ephemeral=True)
        return

    total_xp = xp_data[user_id]["xp"]
    level, current_xp, xp_needed = get_level(total_xp)
    progress = int((current_xp / xp_needed) * 10)
    bar = "🟪" * progress + "⬜" * (10 - progress)
    percent = int((current_xp / xp_needed) * 100)

    embed = discord.Embed(
        title=f"✨ Your Rank {interaction.user.name}! ☄️",
        description=(
            f"📊 **Level**\nLevel {level}\n\n"
            f"⭐ **XP**\n{current_xp} / {xp_needed}\n\n"
            f"📈 **Progress**\n{bar}\n{percent}%"
        ),
        color=discord.Color.from_str("#F6CEE3")
    )
    embed.set_thumbnail(url=interaction.user.display_avatar.url)
    await interaction.response.send_message(embed=embed)

# ─── /LEADERBOARD COMMAND ───────────────────────────────
@bot.tree.command(
    name="leaderboard",
    description="See the top XP users",
    guild=discord.Object(id=GUILD_ID)
)
async def leaderboard(interaction: discord.Interaction):
    top = sorted(xp_data.items(), key=lambda x: x[1]["xp"], reverse=True)[:10]
    description = ""
    guild = bot.get_guild(GUILD_ID)
    for i, (user_id, data) in enumerate(top, start=1):
        member = guild.get_member(int(user_id))
        if member:
            description += f"**{i}. {member.name}** — Level {data['level']} ({data['xp']} XP)\n"
    embed = discord.Embed(
        title="🏆 XP Leaderboard 🏆",
        description=description or "No data yet.",
        color=discord.Color.from_str("#F6CEE3")
    )
    await interaction.response.send_message(embed=embed)

# ─── /SETLEVEL COMMAND (MOD ONLY) ───────────────────────
@bot.tree.command(
    name="setlevel",
    description="Set a user's level manually (Mods only)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(member="The member to modify", level="The level to set")
async def setlevel(interaction: discord.Interaction, member: discord.Member, level: int):

    if not interaction.user.guild_permissions.manage_roles:
        await interaction.response.send_message(
            "❌ You don't have permission.",
            ephemeral=True
        )
        return

    if level < 0:
        await interaction.response.send_message(
            "Level must be 0 or higher.",
            ephemeral=True
        )
        return

    user_id = member.id

    if user_id not in xp_data:
        xp_data[user_id] = {
            "xp": 0,
            "level": 0,
            "last_message": 0
        }

    # 🔥 THIS IS THE IMPORTANT PART
    # Convert level to XP using your system formula
    total_xp = 0
    for i in range(level):
        total_xp += (i + 1) * 100  # <-- CHANGE if your XP scaling is different

    xp_data[user_id]["xp"] = total_xp
    xp_data[user_id]["level"] = level

    await interaction.response.send_message(
        f"✨ {member.mention} is now Level {level}."
    )

# ─── /SHUTUPNORI COMMAND ───────────────────────
@bot.tree.command(
    name="sunori",
    description="Tell Nori to be quiet 😭",
    guild=discord.Object(id=GUILD_ID)
)
async def shutupnori(interaction: discord.Interaction):
    await interaction.response.send_message("**SHUT UP NORI!!!** 😭")

# ─── /EMBED COMMAND (MOD ONLY) ───────────────────────

@bot.tree.command(
    name="embed",
    description="Send a custom embed (Mods only)",
    guild=discord.Object(id=GUILD_ID)
)
@app_commands.describe(
    title="Title of the embed",
    description="Main text",
    color="Hex color like #FF0000"
)
async def embed(interaction: discord.Interaction, title: str, description: str, color: str):

    # Permission check FIRST
    if not interaction.user.guild_permissions.manage_messages:
        await interaction.response.send_message(
            "❌ You don't have permission.",
            ephemeral=True
        )
        return

    # Defer immediately (this prevents public response)
    await interaction.response.defer(ephemeral=True)

    # Convert hex color
    try:
        if color.startswith("#"):
            color = color[1:]
        embed_color = discord.Color(int(color, 16))
    except ValueError:
        await interaction.followup.send(
            "❌ Invalid color. Use hex like #FF0000.",
            ephemeral=True
        )
        return

    embed = discord.Embed(
        title=title,
        description=description,
        color=embed_color,
        timestamp=datetime.utcnow()
    )

    await interaction.channel.send(embed=embed)

    await interaction.followup.send("✅ Embed sent.", ephemeral=True)

# ─── AUTO-MODERATION ─────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return

    # ─── XP SYSTEM (ALL CHANNELS) ─────────────────────
    user_id = message.author.id
    now = time.time()

    if user_id not in xp_data:
        xp_data[user_id] = {
            "xp": 0,
            "level": 0,
            "last_message": 0
        }

    if now - xp_data[user_id]["last_message"] >= XP_COOLDOWN:
        xp_data[user_id]["last_message"] = now
        xp_data[user_id]["xp"] += XP_PER_MESSAGE

        new_level, _, _ = get_level(xp_data[user_id]["xp"])

        if new_level > xp_data[user_id]["level"]:
            xp_data[user_id]["level"] = new_level
            await message.channel.send(
                f"✨ {message.author.mention} leveled up to **Level {new_level}**!"
            )

    now = datetime.utcnow().timestamp()
    user_messages[message.author.id].append(now)
    user_messages[message.author.id] = [
        t for t in user_messages[message.author.id] if now - t < AUTOMOD_SPAM_INTERVAL
    ]

    if len(user_messages[message.author.id]) > AUTOMOD_SPAM_LIMIT:
        try:
            await message.author.timeout(AUTOMOD_SPAM_TIMEOUT, reason="Spamming")
        except discord.Forbidden:
            pass
        user_messages[message.author.id] = []
        log = bot.get_channel(AUTOMOD_LOG_CHANNEL_ID)
        if log:
            embed = discord.Embed(title="❌ Auto-Moderation: Spam", color=discord.Color.red(), timestamp=datetime.utcnow())
            embed.add_field(name="👤 User", value=f"{message.author} ({message.author.mention})", inline=False)
            embed.add_field(name="💬 Message", value=message.content[:1024], inline=False)
            embed.add_field(name="🛡️ Action", value="Timeout 1h", inline=False)
            await log.send(embed=embed)
        await message.delete()
        return

    if message.channel.id == AUTOMOD_FORBIDDEN_CHANNEL_ID:
        lowered = message.content.lower()
        found_word = next((w for w in AUTOMOD_FORBIDDEN_WORDS if w in lowered), None)

        if found_word:
            try:
                await message.delete()
            except discord.Forbidden:
                pass

            try:
                await message.author.timeout(
                    AUTOMOD_WORD_TIMEOUT,
                    reason=f"Forbidden word: {found_word}"
                )
            except discord.Forbidden:
                pass

                
            log = bot.get_channel(AUTOMOD_LOG_CHANNEL_ID)
            if log:
                embed = discord.Embed(title="❌ Auto-Moderation: Forbidden Word", color=discord.Color.red(), timestamp=datetime.utcnow())
                embed.add_field(name="👤 User", value=f"{message.author} ({message.author.mention})", inline=False)
                embed.add_field(name="💬 Message", value=message.content[:1024], inline=False)
                embed.add_field(name="📌 Word used", value=found_word, inline=False)
                embed.add_field(name="🛡️ Action", value="Timeout 1h", inline=False)
                await log.send(embed=embed)
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

    await bot.process_commands(message)
    
# ─── /BAN COMMAND ───────────────────────────────────────
@bot.tree.command(
    name="ban",
    description="Ban a user",
    guild=discord.Object(id=GUILD_ID)
)
@mod_only()
@app_commands.describe(member="User to ban", reason="Reason for ban")
async def ban(interaction: discord.Interaction, member: discord.Member, reason: str):
    dm_embed = discord.Embed(
        title="🚫 You have been banned from **{interaction.guild.name}**",
        description=(
            f"Sorry {member.mention}.You have been **banned** from **{interaction.guild.name}**.\n\n"
            f"**Reason:** {reason}\n\n"
            f"If you think this is a mistake, you may appeal here:\n{APPEAL_LINK}"
        ),
        color=discord.Color.red()
    )

    try:
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        pass

    await member.ban(reason=reason)

    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        log_embed = discord.Embed(
            title="🔨 Ban",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        log_embed.add_field(name="👤 User", value=f"{member} ({member.id})", inline=False)
        log_embed.add_field(name="📌 Reason", value=reason, inline=False)
        log_embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=False)
        await log.send(embed=log_embed)

    await interaction.response.send_message(
        f"✅ {member.mention} has been banned.",
        ephemeral=True
    )


# ─── /UNBAN COMMAND ─────────────────────────────────────
@bot.tree.command(
    name="unban",
    description="Unban a user",
    guild=discord.Object(id=GUILD_ID)
)
@mod_only()
@app_commands.describe(user_id="ID of the user to unban", reason="Reason for unban")
async def unban(interaction: discord.Interaction, user_id: str, reason: str):
    guild = interaction.guild
    user = await bot.fetch_user(int(user_id))

    await guild.unban(user, reason=reason)

    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        embed = discord.Embed(
            title="♻️ Unban",
            color=discord.Color.green(),
            timestamp=datetime.utcnow()
        )
        embed.add_field(name="👤 User", value=f"{user} ({user.id})", inline=False)
        embed.add_field(name="📌 Reason", value=reason, inline=False)
        embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=False)
        await log.send(embed=embed)

    await interaction.response.send_message(
        f"✅ {user} has been unbanned.",
        ephemeral=True
    )


# ─── /KICK COMMAND ──────────────────────────────────────
@bot.tree.command(
    name="kick",
    description="Kick a user",
    guild=discord.Object(id=GUILD_ID)
)
@mod_only()
@app_commands.describe(member="User to kick", reason="Reason for kick")
async def kick(interaction: discord.Interaction, member: discord.Member, reason: str):
    dm_embed = discord.Embed(
        title="👢 You have been kicked from **{interaction.guild.name}**",
        description=(
            f"Sorry {member.mention}. You have been **kicked** from **{interaction.guild.name}**.\n\n"
            f"**Reason:** {reason}\n\n"
            f"If you think this is unfair, you may appeal here:\n{APPEAL_LINK}"
        ),
        color=discord.Color.red()
    )

    try:
        await member.send(embed=dm_embed)
    except discord.Forbidden:
        pass

    await member.kick(reason=reason)

    log = bot.get_channel(LOG_CHANNEL_ID)
    if log:
        log_embed = discord.Embed(
            title="👢 Kick",
            color=discord.Color.red(),
            timestamp=datetime.utcnow()
        )
        log_embed.add_field(name="👤 User", value=f"{member} ({member.id})", inline=False)
        log_embed.add_field(name="📌 Reason", value=reason, inline=False)
        log_embed.add_field(name="🛡️ Moderator", value=interaction.user.mention, inline=False)
        await log.send(embed=log_embed)

    await interaction.response.send_message(
        f"✅ {member.mention} has been kicked.",
        ephemeral=True
    )

# ─── FLASK SERVER TO KEEP BOT ALIVE ─────────────────────
app = Flask('')

@app.route("/")
def home():
    return "Nori is good!"

def run():
    app.run(host="0.0.0.0", port=8080)

def keep_alive():
    t = Thread(target=run)
    t.start()

keep_alive()

# ─── START BOT ────────────────────────────────────────────
bot.run(DISCORD_TOKEN)








































