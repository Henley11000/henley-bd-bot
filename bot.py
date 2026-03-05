import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN")

# ── 你自己的 Telegram user ID，收通知用 ──
ADMIN_ID = int(os.environ.get("ADMIN_ID", "0"))

# ── 各地区推广话术模板 ──
TEMPLATES = {
    "my": """Hi! 👋 I'm Henley from HashWhale — a crypto lending & yield platform.

We're looking for crypto community leaders in Malaysia to partner with us 🤝
💰 Commission: $50–$200 USDT per referral
📈 Product: Crypto-backed loans & high-yield savings

Would love to chat if you're open to a collab! DM me anytime 😊""",

    "vn": """Xin chào! 👋 Tôi là Henley từ HashWhale — nền tảng cho vay crypto.

Chúng tôi đang tìm kiếm đối tác cộng đồng tại Việt Nam 🤝
💰 Hoa hồng: $50–$200 USDT
📈 Sản phẩm: Vay thế chấp crypto & tiết kiệm lãi suất cao

Rất mong được hợp tác với bạn! Nhắn tin cho tôi nhé 😊""",

    "ph": """Hi! 👋 I'm Henley from HashWhale — a crypto lending platform.

We're looking for crypto community owners in the Philippines 🤝
💰 Commission: $50–$200 USDT per successful referral
📈 We offer crypto-backed loans & yield products

Open to a quick chat? DM me anytime! 😊""",

    "dubai": """Hello! 👋 I'm Henley, BD at HashWhale — crypto lending & yield platform.

We're expanding in the UAE and looking for community partners 🤝
💰 Commission: $50–$200 USDT
📈 Crypto-collateralized loans & savings products

Would love to explore a partnership — feel free to DM! 😊""",

    "paris": """Bonjour! 👋 Je suis Henley de HashWhale — plateforme de prêts crypto.

Nous cherchons des partenaires communautaires en France 🤝
💰 Commission : 50–200 USDT
📈 Prêts adossés à des crypto-actifs & épargne à haut rendement

N'hésitez pas à me contacter en DM 😊""",
}

# ── 追踪记录（存在内存，重启会清空，够用） ──
contacts = {}  # { community_name: { region, status, notes } }

# ─────────────────────────────────────────
async def start(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 嗨 Henley！我是你的 HashWhale BD 助手\n\n"
        "指令列表：\n"
        "/template — 查看各地区推广话术\n"
        "/add — 添加新联系的社区\n"
        "/list — 查看所有联系记录\n"
        "/update — 更新某个社区状态\n"
        "/stats — 今日统计"
    )

async def template(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🇲🇾 马来西亚", callback_data="tpl_my"),
         InlineKeyboardButton("🇻🇳 越南", callback_data="tpl_vn")],
        [InlineKeyboardButton("🇵🇭 菲律宾", callback_data="tpl_ph"),
         InlineKeyboardButton("🇦🇪 Dubai", callback_data="tpl_dubai")],
        [InlineKeyboardButton("🇫🇷 Paris", callback_data="tpl_paris")],
    ]
    await update.message.reply_text("选择地区查看话术模板 👇",
                                     reply_markup=InlineKeyboardMarkup(keyboard))

async def button_handler(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    region = query.data.replace("tpl_", "")
    if region in TEMPLATES:
        await query.message.reply_text(
            f"📋 话术模板：\n\n{TEMPLATES[region]}\n\n"
            "👆 复制上面的内容，手动发到群里或私信给群主"
        )

async def add_contact(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """用法: /add 群名 地区 备注"""
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "用法：/add 群名 地区(my/vn/ph/dubai/paris) 备注\n"
            "例：/add MalaysiaCryptoHub my 群主叫 Ali，5000人"
        )
        return
    name = args[0]
    region = args[1]
    notes = " ".join(args[2:]) if len(args) > 2 else ""
    contacts[name] = {"region": region, "status": "已联系", "notes": notes}
    await update.message.reply_text(f"✅ 已记录：{name} ({region})\n备注：{notes}")

async def list_contacts(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    if not contacts:
        await update.message.reply_text("还没有记录，用 /add 添加第一个社区吧！")
        return
    text = "📋 联系记录：\n\n"
    for name, info in contacts.items():
        emoji = {"已联系": "📨", "有回复": "💬", "已合作": "🤝", "无回应": "❌"}.get(info["status"], "📌")
        text += f"{emoji} {name} [{info['region'].upper()}]\n状态：{info['status']}\n备注：{info['notes']}\n\n"
    await update.message.reply_text(text)

async def update_status(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    """用法: /update 群名 新状态"""
    args = ctx.args
    if len(args) < 2:
        await update.message.reply_text(
            "用法：/update 群名 状态\n"
            "状态选项：已联系 / 有回复 / 已合作 / 无回应"
        )
        return
    name = args[0]
    status = " ".join(args[1:])
    if name not in contacts:
        await update.message.reply_text(f"找不到 {name}，请先用 /add 添加")
        return
    contacts[name]["status"] = status
    await update.message.reply_text(f"✅ 已更新：{name} → {status}")
    # 如果有回复，提醒 admin
    if "回复" in status or "合作" in status:
        if ADMIN_ID:
            await ctx.bot.send_message(
                ADMIN_ID,
                f"🔔 注意！{name} 状态更新为「{status}」，快去跟进！"
            )

async def stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE):
    total = len(contacts)
    replied = sum(1 for c in contacts.values() if "回复" in c["status"])
    partnered = sum(1 for c in contacts.values() if "合作" in c["status"])
    await update.message.reply_text(
        f"📊 BD 进度统计\n\n"
        f"📨 总联系社区：{total}\n"
        f"💬 有回复：{replied}\n"
        f"🤝 已合作：{partnered}\n"
        f"📈 回复率：{round(replied/total*100) if total else 0}%"
    )

# ─────────────────────────────────────────
app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CommandHandler("template", template))
app.add_handler(CommandHandler("add", add_contact))
app.add_handler(CommandHandler("list", list_contacts))
app.add_handler(CommandHandler("update", update_status))
app.add_handler(CommandHandler("stats", stats))
app.add_handler(CallbackQueryHandler(button_handler))

print("Bot is running...")
app.run_polling()
