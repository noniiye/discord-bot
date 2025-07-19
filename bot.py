import discord
from discord.ext import commands
from discord import app_commands
from flask import Flask
import os
import threading
import json

TOKEN = os.getenv("TOKEN")  # تأكد من وضع التوكن في متغير البيئة في Render

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# سيرفر صغير لتشغيل البوت في Render
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot is running!"

def run_flask():
    app.run(host="0.0.0.0", port=8080)

threading.Thread(target=run_flask).start()

# قاعدة بيانات محلية لكل سيرفر (تُخزن داخل ملف JSON)
DB_FILE = "store_data.json"

def load_db():
    if not os.path.exists(DB_FILE):
        with open(DB_FILE, "w") as f:
            json.dump({}, f)
    with open(DB_FILE, "r") as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=2)

def get_guild_data(guild_id):
    db = load_db()
    return db.get(str(guild_id), {"products": [], "orders": []})

def set_guild_data(guild_id, data):
    db = load_db()
    db[str(guild_id)] = data
    save_db(db)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} commands.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

# ✅ أمر لإضافة منتج
@tree.command(name="اضافة_منتج", description="إضافة منتج جديد للمتجر")
@app_commands.describe(الاسم="اسم المنتج", السعر="سعر المنتج")
async def add_product(interaction: discord.Interaction, الاسم: str, السعر: int):
    guild_id = interaction.guild.id
    data = get_guild_data(guild_id)
    data["products"].append({"name": الاسم, "price": السعر})
    set_guild_data(guild_id, data)
    await interaction.response.send_message(f"✅ تم إضافة المنتج `{الاسم}` بسعر `{السعر}` ريال.", ephemeral=True)

# ✅ عرض المنتجات
@tree.command(name="عرض_المنتجات", description="عرض قائمة المنتجات")
async def show_products(interaction: discord.Interaction):
    guild_id = interaction.guild.id
    data = get_guild_data(guild_id)
    if not data["products"]:
        await interaction.response.send_message("❌ لا توجد منتجات حاليًا.", ephemeral=True)
        return

    embed = discord.Embed(title="🛒 المنتجات المتوفرة:", color=discord.Color.blue())
    for idx, product in enumerate(data["products"], start=1):
        embed.add_field(name=f"{idx}- {product['name']}", value=f"السعر: {product['price']} ريال", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# ✅ تقديم طلب شراء
@tree.command(name="طلب", description="طلب شراء منتج")
@app_commands.describe(رقم_المنتج="رقم المنتج من القائمة")
async def order(interaction: discord.Interaction, رقم_المنتج: int):
    guild_id = interaction.guild.id
    user = interaction.user
    data = get_guild_data(guild_id)

    if رقم_المنتج < 1 or رقم_المنتج > len(data["products"]):
        await interaction.response.send_message("❌ رقم المنتج غير صحيح.", ephemeral=True)
        return

    product = data["products"][رقم_المنتج - 1]
    order_info = {
        "user": user.id,
        "product": product,
        "status": "pending"
    }
    data["orders"].append(order_info)
    set_guild_data(guild_id, data)

    # إرسال الفاتورة في الرد
    embed = discord.Embed(title="🧾 فاتورة الطلب", color=discord.Color.green())
    embed.add_field(name="العميل", value=user.mention, inline=False)
    embed.add_field(name="المنتج", value=product['name'], inline=True)
    embed.add_field(name="السعر", value=f"{product['price']} ريال", inline=True)
    await interaction.response.send_message(embed=embed)

# ✅ إنهاء الطلب (للتاجر فقط)
@tree.command(name="انهاء_الطلب", description="إنهاء الطلب وإرسال تقييم للعميل")
@app_commands.describe(رقم_الطلب="رقم الطلب من 1 وما فوق")
async def complete_order(interaction: discord.Interaction, رقم_الطلب: int):
    guild_id = interaction.guild.id
    data = get_guild_data(guild_id)

    if رقم_الطلب < 1 or رقم_الطلب > len(data["orders"]):
        await interaction.response.send_message("❌ رقم الطلب غير صحيح.", ephemeral=True)
        return

    order = data["orders"][رقم_الطلب - 1]
    order["status"] = "completed"
    set_guild_data(guild_id, data)

    user = bot.get_user(order["user"])
    if user:
        try:
            await user.send(f"✅ تم إنهاء طلبك لمنتج `{order['product']['name']}` بنجاح.\n📩 من فضلك قيّم تجربتك معنا بإرسال رسالة هنا!")
        except:
            pass

    await interaction.response.send_message("✅ تم إنهاء الطلب وإرسال رسالة التقييم للعميل.", ephemeral=True)

bot.run(TOKEN)
