import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, Embed, ButtonStyle
import sqlite3, os
from flask import Flask
from threading import Thread

# ====== Flask keep_alive =======
app = Flask('')

@app.route('/')
def home():
    return "Bot is alive"

def keep_alive():
    Thread(target=lambda: app.run(host='0.0.0.0', port=8080)).start()

# ====== Database Setup =======
conn = sqlite3.connect("store.db")
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS stores (
    guild_id INTEGER PRIMARY KEY,
    owner_id INTEGER,
    store_name TEXT,
    order_channel_id INTEGER,
    payment_link TEXT
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS categories (
    guild_id INTEGER,
    category_name TEXT,
    PRIMARY KEY(guild_id, category_name)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS products (
    guild_id INTEGER,
    category_name TEXT,
    product_name TEXT,
    price INTEGER,
    quantity INTEGER,
    PRIMARY KEY(guild_id, category_name, product_name)
)
""")

c.execute("""
CREATE TABLE IF NOT EXISTS ratings (
    user_id INTEGER,
    guild_id INTEGER,
    stars INTEGER
)
""")

conn.commit()

# ===== Bot Setup =====
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ===== Helper Functions =====
def get_store(gid):
    c.execute("SELECT * FROM stores WHERE guild_id=?", (gid,))
    r = c.fetchone()
    if r:
        return {
            "owner_id": r[1],
            "store_name": r[2],
            "order_channel_id": r[3],
            "payment_link": r[4] or "https://payment.com"
        }
    return None

def update_quantity(gid, cat, product, qty):
    c.execute("UPDATE products SET quantity=? WHERE guild_id=? AND category_name=? AND product_name=?",
              (qty, gid, cat, product))
    conn.commit()

def get_products(gid, cat):
    c.execute("SELECT product_name, price, quantity FROM products WHERE guild_id=? AND category_name=?", (gid, cat))
    return c.fetchall()

def send_invoice(user, category, product, price, qty, total, link):
    embed = Embed(title="📄 فاتورة الطلب", color=0x2ecc71)
    embed.add_field(name="القسم", value=category)
    embed.add_field(name="المنتج", value=product)
    embed.add_field(name="السعر", value=f"{price} ريال")
    embed.add_field(name="الكمية", value=str(qty))
    embed.add_field(name="الإجمالي", value=f"{total} ريال")
    embed.add_field(name="رابط الدفع", value=f"[اضغط هنا للدفع]({link})")
    embed.set_footer(text="الرجاء إرسال إيصال الدفع بعد التحويل")
    return user.send(embed=embed)

class RatingView(ui.View):
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=60)
        self.user_id = user_id
        self.guild_id = guild_id

        for i in range(1, 6):
            self.add_item(ui.Button(label=f"{i} ⭐", style=ButtonStyle.secondary, custom_id=f"rate_{i}"))

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.user_id

    @ui.button(label="تجاهل", style=ButtonStyle.danger)
    async def ignore(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(content="❌ تم تجاهل التقييم.", view=None)

@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type == discord.InteractionType.component and interaction.data['custom_id'].startswith("rate_"):
        stars = int(interaction.data['custom_id'].split("_")[1])
        user = interaction.user
        c.execute("INSERT INTO ratings (user_id, guild_id, stars) VALUES (?, ?, ?)", (user.id, interaction.guild.id, stars))
        conn.commit()
        await interaction.response.edit_message(content=f"⭐ شكراً لتقييمك {stars} نجوم!", view=None)

# ===== Slash Command: طلب =====
@tree.command(name="طلب", description="🛒 طلب منتج")
@app_commands.describe(category="اسم القسم", product="اسم المنتج", quantity="الكمية المطلوبة")
async def order(interaction: Interaction, category: str, product: str, quantity: int):
    store = get_store(interaction.guild.id)
    if not store:
        await interaction.response.send_message("❌ لا يوجد متجر محدد.", ephemeral=True)
        return

    products = get_products(interaction.guild.id, category)
    selected = next((p for p in products if p[0] == product), None)
    if not selected:
        await interaction.response.send_message("❌ المنتج غير موجود.", ephemeral=True)
        return

    if quantity > selected[2]:
        await interaction.response.send_message("❌ الكمية غير متوفرة.", ephemeral=True)
        return

    total = selected[1] * quantity
    update_quantity(interaction.guild.id, category, product, selected[2] - quantity)

    await send_invoice(interaction.user, category, product, selected[1], quantity, total, store["payment_link"])

    await interaction.response.send_message("✅ تم إرسال الفاتورة على الخاص.", ephemeral=True)

    # تقييم بعد الطلب
    try:
        await interaction.user.send("✨ ما رأيك بتجربتك؟ اختر عدد النجوم:", view=RatingView(interaction.user.id, interaction.guild.id))
    except:
        pass

# ===== Events =====
@bot.event
async def on_ready():
    print(f"✅ Bot is ready as {bot.user}")
    await tree.sync()

# ===== Main Start =====
keep_alive()
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
