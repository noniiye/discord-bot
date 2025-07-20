
import discord
from discord.ext import commands
from discord import app_commands, Interaction, Embed, ButtonStyle
from discord.ui import View, Button
import json
import os
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

DATA_FILE = "store_data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, "w") as f:
            json.dump({}, f)
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ Logged in as {bot.user}")

@tree.command(name="إنشاء_متجر", description="إنشاء متجر باسم مخصص")
async def create_store(interaction: Interaction, اسم_المتجر: str):
    data = load_data()
    guild_id = str(interaction.guild_id)
    data[guild_id] = {"store_name": اسم_المتجر, "categories": {}, "payment_link": "", "order_channel": ""}
    save_data(data)
    await interaction.response.send_message(embed=Embed(title="✅ تم", description=f"تم إنشاء المتجر باسم **{اسم_المتجر}**", color=0x00ff00))

@tree.command(name="إضافة_قسم", description="إضافة قسم جديد")
async def add_category(interaction: Interaction, القسم: str):
    data = load_data()
    guild_id = str(interaction.guild_id)
    if guild_id not in data:
        return await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.")
    data[guild_id]["categories"][القسم] = {}
    save_data(data)
    await interaction.response.send_message(embed=Embed(title="✅ تم", description=f"تمت إضافة القسم **{القسم}**", color=0x00ff00))

@tree.command(name="إضافة_منتج", description="إضافة منتج داخل قسم")
async def add_product(interaction: Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    data = load_data()
    guild_id = str(interaction.guild_id)
    if guild_id not in data or القسم not in data[guild_id]["categories"]:
        return await interaction.response.send_message("❌ تأكد من وجود القسم والمتجر.")
    data[guild_id]["categories"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
    save_data(data)
    await interaction.response.send_message(embed=Embed(title="✅ تم", description=f"أُضيف المنتج **{المنتج}** إلى القسم **{القسم}**", color=0x00ff00))

@tree.command(name="تحديد_رابط_الدفع", description="تحديد رابط الدفع للفواتير")
async def set_payment_link(interaction: Interaction, الرابط: str):
    data = load_data()
    guild_id = str(interaction.guild_id)
    if guild_id not in data:
        return await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.")
    data[guild_id]["payment_link"] = الرابط
    save_data(data)
    await interaction.response.send_message(embed=Embed(title="✅ تم", description="تم تعيين رابط الدفع بنجاح.", color=0x00ff00))

@tree.command(name="تحديد_روم_الطلبات", description="تحديد روم إرسال الطلبات")
async def set_order_channel(interaction: Interaction, channel: discord.TextChannel):
    data = load_data()
    guild_id = str(interaction.guild_id)
    if guild_id not in data:
        return await interaction.response.send_message("❌ يجب إنشاء متجر أولاً.")
    data[guild_id]["order_channel"] = str(channel.id)
    save_data(data)
    await interaction.response.send_message(embed=Embed(title="✅ تم", description=f"تم تعيين روم الطلبات إلى {channel.mention}", color=0x00ff00))

@tree.command(name="طلب", description="تنفيذ طلب")
async def order(interaction: Interaction):
    data = load_data()
    guild_id = str(interaction.guild_id)
    if guild_id not in data or not data[guild_id]["categories"]:
        return await interaction.response.send_message("❌ لا يوجد متجر أو أقسام.")

    view = View()
    for category in data[guild_id]["categories"]:
        view.add_item(Button(label=category, style=ButtonStyle.primary, custom_id=f"cat:{category}"))
    await interaction.response.send_message(embed=Embed(title="اختر القسم", color=0x3498db), view=view, ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if not interaction.type == discord.InteractionType.component:
        return
    data = load_data()
    guild_id = str(interaction.guild_id)
    if interaction.data["custom_id"].startswith("cat:"):
        category = interaction.data["custom_id"].split(":")[1]
        view = View()
        for product in data[guild_id]["categories"][category]:
            view.add_item(Button(label=product, style=ButtonStyle.primary, custom_id=f"prod:{category}:{product}"))
        await interaction.response.edit_message(embed=Embed(title=f"اختر المنتج من قسم {category}", color=0x3498db), view=view)

    elif interaction.data["custom_id"].startswith("prod:"):
        _, category, product = interaction.data["custom_id"].split(":")
        await interaction.response.send_modal(OrderQuantityModal(category, product))

class OrderQuantityModal(discord.ui.Modal, title="أدخل الكمية"):
    def __init__(self, category, product):
        super().__init__()
        self.category = category
        self.product = product

        self.qty = discord.ui.TextInput(label="الكمية", style=discord.TextStyle.short, required=True)
        self.add_item(self.qty)

    async def on_submit(self, interaction: discord.Interaction):
        data = load_data()
        guild_id = str(interaction.guild_id)
        qty = int(self.qty.value)
        product_data = data[guild_id]["categories"][self.category][self.product]
        if qty > product_data["quantity"]:
            return await interaction.response.send_message("❌ الكمية غير متوفرة", ephemeral=True)

        total = qty * product_data["price"]
        product_data["quantity"] -= qty
        save_data(data)

        # إرسال الطلب إلى روم الطلبات
        order_channel_id = data[guild_id].get("order_channel")
        if order_channel_id:
            ch = bot.get_channel(int(order_channel_id))
            await ch.send(f"📥 طلب جديد:
المنتج: **{self.product}**
القسم: **{self.category}**
الكمية: **{qty}**
من: {interaction.user.mention}")

        # إرسال الفاتورة والتقييم للخاص
        store_name = data[guild_id]["store_name"]
        payment_link = data[guild_id]["payment_link"]
        desc = f"**{store_name}**
المنتج: {self.product}
الكمية: {qty}
السعر الإجمالي: {total} ريال
رابط الدفع: {payment_link}"
        invoice = Embed(title="فاتورتك", description=desc, color=0x2ecc71)
        await interaction.user.send(embed=invoice)

        view = View()
        view.add_item(Button(label="⭐ 1", style=ButtonStyle.secondary, custom_id="rate:1"))
        view.add_item(Button(label="⭐ 2", style=ButtonStyle.secondary, custom_id="rate:2"))
        view.add_item(Button(label="⭐ 3", style=ButtonStyle.secondary, custom_id="rate:3"))
        view.add_item(Button(label="⭐ 4", style=ButtonStyle.secondary, custom_id="rate:4"))
        view.add_item(Button(label="⭐ 5", style=ButtonStyle.secondary, custom_id="rate:5"))
        await interaction.user.send(embed=Embed(title="قيّم طلبك من 1 إلى 5 نجوم"), view=view)

        await interaction.response.send_message("✅ تم تنفيذ الطلب. راجع الخاص.", ephemeral=True)

@bot.event
async def on_component(interaction: discord.Interaction):
    if interaction.data["custom_id"].startswith("rate:"):
        stars = interaction.data["custom_id"].split(":")[1]
        await interaction.response.send_message("شكرًا لتقييمك!", ephemeral=True)

        data = load_data()
        guild_id = str(interaction.guild_id)
        order_channel_id = data[guild_id].get("order_channel")
        if order_channel_id:
            ch = bot.get_channel(int(order_channel_id))
            await ch.send(f"⭐ تقييم جديد من {interaction.user.mention}: {stars} نجوم")

# حذف الأوامر
@tree.command(name="حذف_متجر", description="حذف المتجر")
async def delete_store(interaction: Interaction):
    data = load_data()
    if str(interaction.guild_id) in data:
        del data[str(interaction.guild_id)]
        save_data(data)
        await interaction.response.send_message("✅ تم حذف المتجر.")
    else:
        await interaction.response.send_message("❌ لا يوجد متجر لحذفه.")

@tree.command(name="حذف_قسم", description="حذف قسم")
async def delete_category(interaction: Interaction, القسم: str):
    data = load_data()
    guild_id = str(interaction.guild_id)
    if القسم in data.get(guild_id, {}).get("categories", {}):
        del data[guild_id]["categories"][القسم]
        save_data(data)
        await interaction.response.send_message("✅ تم حذف القسم.")
    else:
        await interaction.response.send_message("❌ القسم غير موجود.")

@tree.command(name="حذف_منتج", description="حذف منتج")
async def delete_product(interaction: Interaction, القسم: str, المنتج: str):
    data = load_data()
    guild_id = str(interaction.guild_id)
    if المنتج in data.get(guild_id, {}).get("categories", {}).get(القسم, {}):
        del data[guild_id]["categories"][القسم][المنتج]
        save_data(data)
        await interaction.response.send_message("✅ تم حذف المنتج.")
    else:
        await interaction.response.send_message("❌ المنتج غير موجود.")

@tree.command(name="حذف_رابط", description="حذف رابط الدفع")
async def delete_payment_link(interaction: Interaction):
    data = load_data()
    guild_id = str(interaction.guild_id)
    data[guild_id]["payment_link"] = ""
    save_data(data)
    await interaction.response.send_message("✅ تم حذف رابط الدفع.")

# Keep alive
app = Flask('')

@app.route('/')
def home():
    return "البوت يعمل!"

def run():
    app.run(host='0.0.0.0', port=8080)

Thread(target=run).start()

bot.run(os.environ["TOKEN"])

