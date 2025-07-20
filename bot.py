import discord
from discord.ext import commands
from discord import app_commands, ui
import asyncio
import os

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

servers_data = {}

# === أوامر المتجر ===

@tree.command(name="انشاء_متجر", description="إنشاء متجر باسم مخصص")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, الاسم: str):
    servers_data[interaction.guild_id] = {
        "store_name": الاسم,
        "categories": {},
        "payment_link": None,
        "orders_channel": None
    }
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم إنشاء المتجر",
        description=f"اسم المتجر: {الاسم}",
        color=discord.Color.green()
    ))

@tree.command(name="تحديد_روم_الطلبات", description="تحديد الروم الذي تُرسل إليه الطلبات")
@app_commands.describe(الروم="اختر روم الطلبات")
async def تحديد_روم_الطلبات(interaction: discord.Interaction, الروم: discord.TextChannel):
    if interaction.guild_id in servers_data:
        servers_data[interaction.guild_id]["orders_channel"] = الروم.id
        await interaction.response.send_message(embed=discord.Embed(
            title="📥 تم تحديد روم الطلبات",
            description=f"الروم: {الروم.mention}",
            color=discord.Color.green()
        ))
    else:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر باستخدام /انشاء_متجر", ephemeral=True)

@tree.command(name="تحديد_رابط_الدفع", description="تحديد رابط الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def تحديد_رابط_الدفع(interaction: discord.Interaction, الرابط: str):
    if interaction.guild_id in servers_data:
        servers_data[interaction.guild_id]["payment_link"] = الرابط
        await interaction.response.send_message(embed=discord.Embed(
            title="💳 تم حفظ رابط الدفع",
            description=رابط,
            color=discord.Color.green()
        ))
    else:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)

@tree.command(name="اضافة_قسم", description="إضافة قسم جديد للمتجر")
@app_commands.describe(الاسم="اسم القسم")
async def اضافة_قسم(interaction: discord.Interaction, الاسم: str):
    if interaction.guild_id in servers_data:
        servers_data[interaction.guild_id]["categories"][الاسم] = {}
        await interaction.response.send_message(embed=discord.Embed(
            title="📂 تم إضافة القسم",
            description=الاسم,
            color=discord.Color.green()
        ))
    else:
        await interaction.response.send_message("❌ يجب أولاً إنشاء متجر.", ephemeral=True)

@tree.command(name="اضافة_منتج", description="إضافة منتج داخل قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية المتاحة", السعر="السعر")
async def اضافة_منتج(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: int):
    data = servers_data.get(interaction.guild_id)
    if not data or القسم not in data["categories"]:
        await interaction.response.send_message("❌ تأكد من وجود المتجر والقسم.", ephemeral=True)
        return
    data["categories"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
    await interaction.response.send_message(embed=discord.Embed(
        title="📦 تم إضافة المنتج",
        description=f"المنتج: {المنتج}\nالقسم: {القسم}\nالكمية: {الكمية}\nالسعر: {السعر}",
        color=discord.Color.green()
    ))

@tree.command(name="حذف_متجر", description="حذف المتجر بالكامل")
async def حذف_متجر(interaction: discord.Interaction):
    servers_data.pop(interaction.guild_id, None)
    await interaction.response.send_message("🗑️ تم حذف المتجر.")

@tree.command(name="حذف_قسم", description="حذف قسم")
@app_commands.describe(القسم="اسم القسم")
async def حذف_قسم(interaction: discord.Interaction, القسم: str):
    data = servers_data.get(interaction.guild_id)
    if data and القسم in data["categories"]:
        del data["categories"][القسم]
        await interaction.response.send_message(f"🗑️ تم حذف القسم {القسم}.")
    else:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)

@tree.command(name="حذف_منتج", description="حذف منتج")
@app_commands.describe(القسم="القسم", المنتج="اسم المنتج")
async def حذف_منتج(interaction: discord.Interaction, القسم: str, المنتج: str):
    data = servers_data.get(interaction.guild_id)
    if data and القسم in data["categories"] and المنتج in data["categories"][القسم]:
        del data["categories"][القسم][المنتج]
        await interaction.response.send_message(f"🗑️ تم حذف المنتج {المنتج} من القسم {القسم}.")
    else:
        await interaction.response.send_message("❌ تحقق من القسم والمنتج.", ephemeral=True)

@tree.command(name="حذف_رابط_الدفع", description="حذف رابط الدفع")
async def حذف_رابط_الدفع(interaction: discord.Interaction):
    data = servers_data.get(interaction.guild_id)
    if data:
        data["payment_link"] = None
        await interaction.response.send_message("✅ تم حذف رابط الدفع.")
    else:
        await interaction.response.send_message("❌ لم يتم العثور على متجر.", ephemeral=True)

# === تنفيذ الطلب والتقييم ===

class QuantityButton(ui.Button):
    def __init__(self, parent):
        self.parent = parent
        super().__init__(label="إدخال الكمية", style=discord.ButtonStyle.success)

    async def callback(self, interaction: discord.Interaction):
        await interaction.response.send_message("📥 أرسل الكمية المطلوبة هنا (رقم فقط):")

        def check(m):
            return m.author.id == self.parent.user_id and m.channel.id == interaction.channel.id

        try:
            msg = await bot.wait_for("message", check=check, timeout=60)
            quantity = int(msg.content)

            product_data = servers_data[self.parent.guild_id]["categories"][self.parent.category][self.parent.product]
            if quantity > product_data["quantity"]:
                await interaction.followup.send("❌ الكمية غير متوفرة.", ephemeral=True)
                return

            product_data["quantity"] -= quantity
            desc = f"القسم: {self.parent.category}\nالمنتج: {self.parent.product}\nالكمية: {quantity}"
            orders_channel_id = servers_data[self.parent.guild_id]["orders_channel"]
            store_name = servers_data[self.parent.guild_id]["store_name"]
            payment_link = servers_data[self.parent.guild_id]["payment_link"]

            if orders_channel_id:
                channel = bot.get_channel(orders_channel_id)
                await channel.send(embed=discord.Embed(
                    title="📥 طلب جديد",
                    description=f"{desc}\nالعميل: <@{self.parent.user_id}>",
                    color=discord.Color.blue()
                ))

            embed = discord.Embed(title="💰 فاتورة الطلب", color=discord.Color.gold())
            embed.add_field(name="🛍️ المتجر", value=store_name, inline=False)
            embed.add_field(name="📦 تفاصيل الطلب", value=desc, inline=False)
            embed.add_field(name="💳 رابط الدفع", value=payment_link or "لا يوجد", inline=False)
            await interaction.user.send(embed=embed)
            await interaction.user.send("📝 كيف تقيم الطلب؟", view=ReviewButtons(interaction.user.id, desc, self.parent.guild_id))
            await interaction.followup.send("✅ تم إرسال الفاتورة والتقييم في الخاص.", ephemeral=True)

        except:
            await interaction.followup.send("❌ لم يتم تنفيذ الطلب بسبب عدم الرد.", ephemeral=True)

class ProductButton(ui.Button):
    def __init__(self, parent, category, product):
        self.parent = parent
        self.category = category
        self.product = product
        super().__init__(label=product, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view = ui.View()
        view.add_item(QuantityButton(self))
        await interaction.response.send_message(f"🔢 اختر الكمية للمنتج: {self.product}", view=view, ephemeral=True)

class CategoryButton(ui.Button):
    def __init__(self, parent, category):
        self.parent = parent
        self.category = category
        super().__init__(label=category, style=discord.ButtonStyle.primary)

    async def callback(self, interaction: discord.Interaction):
        view = ui.View()
        for product in servers_data[self.parent.guild_id]["categories"][self.category]:
            view.add_item(ProductButton(self.parent, self.category, product))
        await interaction.response.send_message("📦 اختر المنتج:", view=view, ephemeral=True)

class OrderView(ui.View):
    def __init__(self, guild_id, user_id):
        super().__init__()
        self.guild_id = guild_id
        self.user_id = user_id
        for category in servers_data[guild_id]["categories"]:
            self.add_item(CategoryButton(self, category))

class ReviewButtons(ui.View):
    def __init__(self, user_id, desc, guild_id):
        super().__init__()
        self.user_id = user_id
        self.desc = desc
        self.guild_id = guild_id
        for rating in ["⭐", "⭐⭐", "⭐⭐⭐", "⭐⭐⭐⭐", "⭐⭐⭐⭐⭐"]:
            self.add_item(ReviewButton(self, rating))

class ReviewButton(ui.Button):
    def __init__(self, parent, rating):
        self.parent = parent
        self.rating = rating
        super().__init__(label=rating, style=discord.ButtonStyle.secondary)

    async def callback(self, interaction: discord.Interaction):
        if interaction.user.id != self.parent.user_id:
            await interaction.response.send_message("❌ هذا التقييم ليس لك.", ephemeral=True)
            return

        await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
        channel_id = servers_data[self.parent.guild_id]["orders_channel"]
        if channel_id:
            channel = bot.get_channel(channel_id)
            await channel.send(embed=discord.Embed(
                title="⭐ تقييم جديد",
                description=f"{self.parent.desc}\nالتقييم: {self.rating}\nمن: <@{self.parent.user_id}>",
                color=discord.Color.purple()
            ))

@tree.command(name="طلب", description="طلب منتج من المتجر")
async def طلب(interaction: discord.Interaction):
    if not servers_data.get(interaction.guild_id) or not servers_data[interaction.guild_id].get("orders_channel"):
        await interaction.response.send_message("❌ يجب تحديد روم الطلبات أولاً باستخدام /تحديد_روم_الطلبات", ephemeral=True)
        return

    await interaction.response.send_message("📋 اختر القسم:", view=OrderView(interaction.guild_id, interaction.user.id), ephemeral=True)

# === تفعيل البوت ===

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ تسجيل الدخول باسم: {bot.user}")

# === استضافة Render / Railway ===
import threading, time
from flask import Flask
app = Flask('')
@app.route('/')
def home():
    return "Bot is running"
def run():
    app.run(host='0.0.0.0', port=8080)
def keep_alive():
    t = threading.Thread(target=run)
    t.start()

keep_alive()
bot.run(os.getenv("TOKEN"))

