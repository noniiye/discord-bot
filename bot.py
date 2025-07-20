import discord
from discord.ext import commands
from discord import app_commands, ui
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

servers_data = {}

class ReviewButtons(ui.View):
    def __init__(self, user_id, order_desc, guild_id):
        super().__init__()
        self.user_id = user_id
        self.order_desc = order_desc
        self.guild_id = guild_id

    @ui.button(label="⭐", style=discord.ButtonStyle.primary)
    async def one_star(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_review(interaction, 1)

    @ui.button(label="⭐⭐", style=discord.ButtonStyle.primary)
    async def two_star(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_review(interaction, 2)

    @ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.primary)
    async def three_star(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.send_review(interaction, 3)

    async def send_review(self, interaction, stars):
        await interaction.response.send_message("شكرًا لتقييمك!", ephemeral=True)
        orders_channel = servers_data[self.guild_id].get("orders_channel")
        if orders_channel:
            channel = bot.get_channel(orders_channel)
            await channel.send(embed=discord.Embed(
                title="⭐ تقييم جديد",
                description=f"الطلب: {self.order_desc}\nالعميل: <@{self.user_id}>\nالتقييم: {'⭐'*stars}",
                color=discord.Color.yellow()
            ))

@tree.command(name="انشاء_متجر", description="إنشاء متجر جديد باسم معين")
@app_commands.describe(store_name="اسم المتجر")
async def create_store(interaction: discord.Interaction, store_name: str):
    guild_id = interaction.guild_id
    servers_data[guild_id] = {
        "store_name": store_name,
        "categories": {},
        "payment_link": "",
        "orders_channel": None
    }
    await interaction.response.send_message(embed=discord.Embed(
        title="✅ تم إنشاء المتجر",
        description=f"اسم المتجر: **{store_name}**",
        color=discord.Color.green()
    ))

@tree.command(name="تحديد_روم_الطلبات", description="تحديد الروم الذي يتم إرسال الطلبات إليه")
async def set_orders_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    servers_data[interaction.guild_id]["orders_channel"] = channel.id
    await interaction.response.send_message(embed=discord.Embed(
        title="📥 تم تعيين روم الطلبات",
        description=f"الروم: {channel.mention}",
        color=discord.Color.blue()
    ))

@tree.command(name="اضافة_قسم", description="إضافة قسم جديد للمتجر")
async def add_category(interaction: discord.Interaction, category_name: str):
    servers_data[interaction.guild_id]["categories"][category_name] = {}
    await interaction.response.send_message(embed=discord.Embed(
        title="📁 تم إضافة قسم",
        description=f"القسم: **{category_name}**",
        color=discord.Color.green()
    ))

@tree.command(name="اضافة_منتج", description="إضافة منتج إلى قسم")
async def add_product(interaction: discord.Interaction, category_name: str, product_name: str, quantity: int, price: float):
    cats = servers_data[interaction.guild_id]["categories"]
    if category_name not in cats:
        await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)
        return
    cats[category_name][product_name] = {"quantity": quantity, "price": price}
    await interaction.response.send_message(embed=discord.Embed(
        title="📦 تم إضافة منتج",
        description=f"القسم: {category_name}\nالمنتج: {product_name}\nالكمية: {quantity}\nالسعر: {price} ريال",
        color=discord.Color.green()
    ))

@tree.command(name="تحديد_رابط_الدفع", description="تحديد رابط الدفع للطلبات")
async def set_payment_link(interaction: discord.Interaction, link: str):
    servers_data[interaction.guild_id]["payment_link"] = link
    await interaction.response.send_message(embed=discord.Embed(
        title="💳 تم تعيين رابط الدفع",
        description=link,
        color=discord.Color.blue()
    ))

@tree.command(name="حذف_متجر", description="حذف المتجر بالكامل")
async def delete_store(interaction: discord.Interaction):
    servers_data.pop(interaction.guild_id, None)
    await interaction.response.send_message("🗑️ تم حذف المتجر.")

@tree.command(name="حذف_قسم", description="حذف قسم من المتجر")
async def delete_category(interaction: discord.Interaction, category_name: str):
    servers_data[interaction.guild_id]["categories"].pop(category_name, None)
    await interaction.response.send_message("🗑️ تم حذف القسم.")

@tree.command(name="حذف_منتج", description="حذف منتج من قسم")
async def delete_product(interaction: discord.Interaction, category_name: str, product_name: str):
    servers_data[interaction.guild_id]["categories"][category_name].pop(product_name, None)
    await interaction.response.send_message("🗑️ تم حذف المنتج.")

@tree.command(name="حذف_رابط_الدفع", description="حذف رابط الدفع")
async def delete_payment_link(interaction: discord.Interaction):
    servers_data[interaction.guild_id]["payment_link"] = ""
    await interaction.response.send_message("🗑️ تم حذف رابط الدفع.")

# نفس OrderView من الكود السابق بدون تغيير، فقط تابع استخدام نفس الكود الموجود

@tree.command(name="طلب", description="طلب منتج من المتجر")
async def order(interaction: discord.Interaction):
    await interaction.response.send_message("📋 اختر القسم والمنتج:", view=OrderView(interaction.guild_id, interaction.user.id), ephemeral=True)

@bot.event
async def on_ready():
    await tree.sync()
    print(f"{bot.user} جاهز.")

keep_alive()
bot.run(os.getenv("TOKEN"))

