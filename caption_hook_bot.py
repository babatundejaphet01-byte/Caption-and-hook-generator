"""
Caption & Hook Generator - a Telegram bot that needs ONLY a Telegram bot token.
The user picks what they want, a platform and a tone, sends a topic,
and the bot fills pre-written templates. Edit the lists below to add your own lines.

Setup:
    pip install "python-telegram-bot>=20"
    export BOT_TOKEN="123456:ABC..."      (Windows: set BOT_TOKEN=123456:ABC...)
    python caption_hook_bot.py
"""
import os
import random
import re

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    ApplicationBuilder,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.environ["BOT_TOKEN"]

WELCOME = (
    "👋 Caption & Hook Generator\n\n"
    "I write ready-to-post captions, hooks, bios and hashtags for TikTok, "
    "Instagram and YouTube.\n\n"
    "What do you need?"
)

PLATFORMS = ["TikTok", "Instagram", "YouTube"]
TONES = ["Funny", "Serious", "Inspiring", "Educational"]

# ---------------------------------------------------------------- menus
MAIN_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("✍️ Caption", callback_data="kind:caption"),
     InlineKeyboardButton("🪝 Hook", callback_data="kind:hook")],
    [InlineKeyboardButton("👤 Bio", callback_data="kind:bio"),
     InlineKeyboardButton("#️⃣ Hashtags", callback_data="kind:hashtags")],
    [InlineKeyboardButton("✨ Full pack (all four)", callback_data="kind:all")],
])


def option_menu(options, prefix):
    rows = [[InlineKeyboardButton(o, callback_data=f"{prefix}:{o}")] for o in options]
    rows.append([InlineKeyboardButton("⬅️ Back", callback_data="home")])
    return InlineKeyboardMarkup(rows)


RESULT_MENU = InlineKeyboardMarkup([
    [InlineKeyboardButton("🔄 Regenerate", callback_data="again")],
    [InlineKeyboardButton("🏠 New request", callback_data="home")],
])

# ---------------------------------------------------------------- templates
HOOKS = {
    "Funny": [
        "POV: you finally understand {topic} and nobody believes you.",
        "Me pretending I know everything about {topic}:",
        "{topic}? Oh, you mean my villain origin story.",
        "Nobody: ... Me talking about {topic} for the 5th hour:",
    ],
    "Serious": [
        "Here's the truth about {topic} that most people ignore.",
        "If you care about {topic}, you need to hear this.",
        "The biggest mistake people make with {topic}.",
        "Stop scrolling. This changes how you see {topic}.",
    ],
    "Inspiring": [
        "You can master {topic}. Here's where to start.",
        "One year from now you'll wish you started {topic} today.",
        "Small steps in {topic} change everything.",
        "Your {topic} journey starts with one decision.",
    ],
    "Educational": [
        "3 things you didn't know about {topic}.",
        "{topic} explained in 30 seconds.",
        "Stop doing {topic} the hard way. Do this instead.",
        "The beginner's guide to {topic} nobody gave you.",
    ],
}

CAPTIONS = {
    "Funny": [
        "Me and {topic}: it's complicated 😂",
        "Plot twist: {topic} was the main character all along 🎬",
        "I came for {topic}, I stayed for the chaos 🤪",
    ],
    "Serious": [
        "{topic} deserves more attention than it gets.",
        "Let's talk honestly about {topic}.",
        "What I've learned about {topic}, and why it matters.",
    ],
    "Inspiring": [
        "Keep going. {topic} rewards the people who don't quit ✨",
        "Every expert in {topic} was once a beginner 🌱",
        "Dream big, start small, stay consistent with {topic} 🚀",
    ],
    "Educational": [
        "Quick lesson on {topic} you can use today 📚",
        "{topic} 101: everything you need to know 👇",
        "Save this for later: simple {topic} tips 💡",
    ],
}

PLATFORM_CTA = {
    "TikTok": ["Follow for more! 🔔", "Comment 'YES' for part 2 👇", "Share this with a friend 🔁"],
    "Instagram": ["Double tap and save this 💾", "Tag someone who needs this 👥", "Follow for more daily tips ✨"],
    "YouTube": ["Subscribe and hit the bell 🔔", "Tell me your thoughts in the comments 💬", "Watch the full video, link in bio ▶️"],
}

BIOS = {
    "Funny": [
        "Professional {topic} overthinker 😅 | Posting daily nonsense",
        "{topic} fan, snack lover, accidental expert 🍿",
    ],
    "Serious": [
        "Helping you understand {topic} 📌 | New content weekly",
        "{topic} • Honest advice • No fluff",
    ],
    "Inspiring": [
        "Turning {topic} into a lifestyle ✨ | Start today",
        "Dream. Build. Repeat. | {topic} 🚀",
    ],
    "Educational": [
        "Learn {topic} in minutes 📚 | Tips every day",
        "{topic} made simple 💡 | Free tips below 👇",
    ],
}

PLATFORM_TAGS = {
    "TikTok": ["fyp", "foryou", "viral", "trending", "tiktokgrowth", "learnontiktok"],
    "Instagram": ["instagood", "explorepage", "reels", "instadaily", "contentcreator",
                  "growthtips", "viralreels", "creatorsofinstagram"],
    "YouTube": ["youtube", "shorts", "youtubecreator", "subscribe", "tutorial"],
}
TAG_COUNT = {"TikTok": 5, "Instagram": 10, "YouTube": 5}


# ---------------------------------------------------------------- generators
def fill(template, topic):
    return template.format(topic=topic)


def make_hook(topic, platform, tone):
    return "🪝 HOOK\n" + fill(random.choice(HOOKS[tone]), topic)


def make_caption(topic, platform, tone):
    cta = random.choice(PLATFORM_CTA[platform])
    return f"✍️ CAPTION\n{fill(random.choice(CAPTIONS[tone]), topic)}\n\n{cta}"


def make_bio(topic, platform, tone):
    bio = fill(random.choice(BIOS[tone]), topic)
    limit = {"TikTok": 80, "Instagram": 150, "YouTube": 300}[platform]
    return f"👤 BIO ({platform}, max {limit} chars)\n{bio[:limit]}"


def make_hashtags(topic, platform, tone):
    words = re.findall(r"[A-Za-z0-9]+", topic.lower())
    own = ["".join(words)] + words
    own = [w for w in dict.fromkeys(own) if len(w) > 2][:3]
    pool = [t for t in PLATFORM_TAGS[platform] if t not in own]
    random.shuffle(pool)
    tags = (own + pool)[: TAG_COUNT[platform]]
    return "#️⃣ HASHTAGS\n" + " ".join("#" + t for t in tags)


MAKERS = {
    "caption": make_caption,
    "hook": make_hook,
    "bio": make_bio,
    "hashtags": make_hashtags,
}


def generate(ud):
    topic, platform, tone, kind = ud["topic"], ud["platform"], ud["tone"], ud["kind"]
    kinds = list(MAKERS) if kind == "all" else [kind]
    parts = [MAKERS[k](topic, platform, tone) for k in kinds]
    header = f"{platform} • {tone} • {topic}\n\n"
    return header + "\n\n".join(parts)


# ---------------------------------------------------------------- handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(WELCOME, reply_markup=MAIN_MENU)


async def on_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    data = q.data
    ud = context.user_data

    if data == "home":
        ud.clear()
        await q.message.reply_text(WELCOME, reply_markup=MAIN_MENU)

    elif data.startswith("kind:"):
        ud.clear()
        ud["kind"] = data.split(":", 1)[1]
        await q.message.reply_text("Which platform?", reply_markup=option_menu(PLATFORMS, "plat"))

    elif data.startswith("plat:"):
        ud["platform"] = data.split(":", 1)[1]
        await q.message.reply_text("Pick a tone:", reply_markup=option_menu(TONES, "tone"))

    elif data.startswith("tone:"):
        ud["tone"] = data.split(":", 1)[1]
        ud["awaiting_topic"] = True
        await q.message.reply_text("Now send me your topic or niche (e.g. 'fitness for beginners').")

    elif data == "again":
        if {"kind", "platform", "tone", "topic"} <= ud.keys():
            await q.message.reply_text(generate(ud), reply_markup=RESULT_MENU)
        else:
            await q.message.reply_text("Let's start over:", reply_markup=MAIN_MENU)


async def on_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    ud = context.user_data
    if not ud.get("awaiting_topic"):
        await update.message.reply_text("What do you need?", reply_markup=MAIN_MENU)
        return
    ud["topic"] = update.message.text.strip()[:80]
    ud["awaiting_topic"] = False
    await update.message.reply_text(generate(ud), reply_markup=RESULT_MENU)


def main():
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(on_button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, on_text))
    print("Bot is running... press Ctrl+C to stop.")
    app.run_polling()


if __name__ == "__main__":
    main()
