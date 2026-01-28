import os
import asyncio
import discord
from discord.ext import commands
from discord import app_commands
from datetime import timedelta, datetime
from collections import defaultdict
from fastapi import FastAPI
from threading import Thread
import uvicorn

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
    "die","cunt"
]
AUTOMOD_SPAM_LIMIT = 5
AUTOMOD_SPAM_INTERVAL = 5
AUTOMOD_SPAM_TIMEOUT = timedelta(hours=1)
AUTOMOD_WORD_TIMEOUT = timedelta(hours=1)
AUTOMOD_EXCEPT_USER = 1277708926863020122

PORT = int(os.environ.get("PORT", 10000))  # required for Render

# ─── INTENTS ───────────────────────────────────────────────
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

warnings = {}
user_messages = defaultdict(list)

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

# ─── AUTO-MODERATION ─────────────────────────────────────
@bot.event
async def on_message(message: discord.Message):
    if message.author.bot:
        return
    if message.channel.id != AUTOMOD_CHANNEL_ID:
        return
    if message.author.id == AUTOMOD_EXCEPT_USER:
        return

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

    lowered = message.content.lower()
    for word in AUTOMOD_FORBIDDEN_WORDS:
        if word in lowered:
            try:
                await message.author.timeout(AUTOMOD_WORD_TIMEOUT, reason=f"Forbidden word: {word}")
            except discord.Forbidden:
                pass
            log = bot.get_channel(AUTOMOD_LOG_CHANNEL_ID)
            if log:
                embed = discord.Embed(title="❌ Auto-Moderation: Forbidden Word", color=discord.Color.red(), timestamp=datetime.utcnow())
                embed.add_field(name="👤 User", value=f"{message.author} ({message.author.mention})", inline=False)
                embed.add_field(name="💬 Message", value=message.content[:1024], inline=False)
                embed.add_field(name="📌 Word used", value=word, inline=False)
                embed.add_field(name="🛡️ Action", value="Timeout 1h", inline=False)
                await log.send(embed=embed)
            try:
                await message.delete()
            except discord.Forbidden:
                pass
            return

    await bot.process_commands(message)

# ─── FASTAPI PING SERVER FOR RENDER ───────────────────────
app = FastAPI()

@app.get("/")
async def ping():
    return {"status": "Bot is running!"}

def run_webserver():
    uvicorn.run(app, host="0.0.0.0", port=PORT)

# ─── START BOT ────────────────────────────────────────────
async def main():
    Thread(target=run_webserver, daemon=True).start()  # start webserver in background
    async with bot:
        await bot.start(DISCORD_TOKEN)

asyncio.run(main())
