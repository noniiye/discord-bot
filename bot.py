import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from discord.ui import Button, View, Modal, TextInput
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

servers_data = {}
if os.path.exists("data.json"):
    with open("data.json", "r") as f:
        servers_data = json.load(f)

def save_data():
    with open("data.json", "w") as f:
        json.dump(servers_data, f, indent=4)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    try:
        synced = await tree.sync()
        print(f"✅ Synced {len(synced)} command(s)")
    except Exception as e:
        print(f"❌ Sync error: {e}")

@tree.command(name="إنشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def create_store(interaction: discord.Interaction, الاسم: str):
    guild_id = str(interaction.guild_id)
    servers_data[guild_id] = {"store_name": الاسم, "categories": {}, "payment_link": "", "orders_channel": None}
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: **{الاسم}**", color=0x00ff00), ephemeral=True)

@tree.command(name="إضافة_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def add_category(interaction: discord.Interaction, الاسم: str):
    guild_id = str(interaction.guild_id)
    if guild_id not in servers_data:
        return await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد", ephemeral=True)
    servers_data[guild_id]["categories"][الاسم] = {}
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة القسم", description=الاسم, color=0x00ff00), ephemeral=True)

@tree.command(name="إضافة_منتج")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج", الكمية="الكمية المتاحة", السعر="سعر المنتج")
async def add_product(interaction: discord.Interaction, القسم: str, الاسم: str, الكمية: int, السعر: float):
    guild_id = str(interaction.guild_id)
    if guild_id not in servers_data or القسم not in servers_data[guild_id]["categories"]:
        return await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)
    servers_data[guild_id]["categories"][القسم][الاسم] = {"quantity": الكمية, "price": السعر}
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة المنتج", description=f"{الاسم} في قسم {القسم}", color=0x00ff00), ephemeral=True)

@tree.command(name="رابط_الدفع")
@app_commands.describe(الرابط="ضع رابط الدفع")
async def set_payment_link(interaction: discord.Interaction, الرابط: str):
    guild_id = str(interaction.guild_id)
    if guild_id not in servers_data:
        return await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد", ephemeral=True)
    servers_data[guild_id]["payment_link"] = الرابط
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديث رابط الدفع", description=الرابط, color=0x00ff00), ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات")
@app_commands.describe(الروم="حدد روم الطلبات")
async def set_orders_channel(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild_id)
    if guild_id not in servers_data:
        return await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد", ephemeral=True)
    servers_data[guild_id]["orders_channel"] = الروم.id
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد روم الطلبات", description=الروم.mention, color=0x00ff00), ephemeral=True)

class QuantityModal(Modal, title="أدخل الكمية"):
    quantity = TextInput(label="الكمية", placeholder="مثال: 1", required=True)

    def __init__(self, callback):
        super().__init__()
        self.callback_fn = callback

    async def on_submit(self, interaction: discord.Interaction):
        await self.callback_fn(interaction, self.quantity.value)

@tree.command(name="طلب")
async def order(interaction: discord.Interaction):
    guild_id = str(interaction.guild_id)
    data = servers_data.get(guild_id)
    if not data:
        return await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد", ephemeral=True)

    categories = list(data["categories"].keys())
    if not categories:
        return await interaction.response.send_message("❌ لا توجد أقسام مضافة", ephemeral=True)

    async def choose_category_callback(inter: discord.Interaction):
        category = inter.data["custom_id"].split("category_")[1]
        products = list(data["categories"][category].keys())
        if not products:
            return await inter.response.send_message("❌ لا توجد منتجات في هذا القسم", ephemeral=True)

        view = View(timeout=60)
        for prod in products:
            btn = Button(label=prod, style=discord.ButtonStyle.blurple, custom_id=f"product_{category}_{prod}")
            view.add_item(btn)

        async def product_callback(i: discord.Interaction):
            parts = i.data["custom_id"].split("product_")[1].split("_")
            selected_cat = parts[0]
            selected_prod = "_".join(parts[1:])

            async def after_quantity_submit(inter_modal: discord.Interaction, quantity_value):
                prod_data = data["categories"][selected_cat][selected_prod]
                total_price = float(prod_data["price"]) * int(quantity_value)
                embed = discord.Embed(title="💰 فاتورتك", color=0x3498db)
                embed.add_field(name="المتجر", value=data["store_name"], inline=False)
                embed.add_field(name="المنتج", value=selected_prod, inline=True)
                embed.add_field(name="القسم", value=selected_cat, inline=True)
                embed.add_field(name="الكمية", value=quantity_value, inline=True)
                embed.add_field(name="السعر الإجمالي", value=f"{total_price} ريال", inline=True)
                embed.add_field(name="رابط الدفع", value=data["payment_link"], inline=False)
                await inter_modal.user.send(embed=embed)

                order_channel_id = data.get("orders_channel")
                if order_channel_id:
                    ch = bot.get_channel(order_channel_id)
                    await ch.send(embed=discord.Embed(title="📦 طلب جديد", description=f"**{selected_prod}** من قسم **{selected_cat}**\nالكمية: {quantity_value}\nالعميل: {inter_modal.user.mention}", color=0x2ecc71))

                    view = View()
                    for emoji in ["👍", "👎"]:
                        view.add_item(Button(label=emoji, style=discord.ButtonStyle.secondary, custom_id=f"rate_{emoji}"))

                    await inter_modal.user.send("يرجى تقييم الطلب:", view=view)

            await i.response.send_modal(QuantityModal(after_quantity_submit))

        for btn in view.children:
            btn.callback = product_callback

        await inter.response.send_message("اختر المنتج:", view=view, ephemeral=True)

    view = View(timeout=60)
    for cat in categories:
        btn = Button(label=cat, style=discord.ButtonStyle.primary, custom_id=f"category_{cat}")
        view.add_item(btn)
    for btn in view.children:
        btn.callback = choose_category_callback
    await interaction.response.send_message("اختر القسم:", view=view, ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type.name == "component":
        if interaction.data["custom_id"].startswith("rate_"):
            rate = interaction.data["custom_id"].split("rate_")[1]
            await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
            for guild_id, data in servers_data.items():
                if data.get("orders_channel"):
                    ch = bot.get_channel(data["orders_channel"])
                    await ch.send(f"⭐ تقييم جديد من {interaction.user.mention}: {rate}")
    await bot.process_application_commands(interaction)

@tree.command(name="حذف_متجر")
async def delete_store(interaction: discord.Interaction):
    if str(interaction.guild_id) in servers_data:
        del servers_data[str(interaction.guild_id)]
        save_data()
        await interaction.response.send_message("🗑️ تم حذف المتجر", ephemeral=True)
    else:
        await interaction.response.send_message("❌ لا يوجد متجر محلي لحذفه", ephemeral=True)

@tree.command(name="حذف_قسم")
@app_commands.describe(الاسم="اسم القسم")
async def delete_category(interaction: discord.Interaction, الاسم: str):
    if str(interaction.guild_id) in servers_data and الاسم in servers_data[str(interaction.guild_id)]["categories"]:
        del servers_data[str(interaction.guild_id)]["categories"][الاسم]
        save_data()
        await interaction.response.send_message("🗑️ تم حذف القسم", ephemeral=True)
    else:
        await interaction.response.send_message("❌ القسم غير موجود", ephemeral=True)

@tree.command(name="حذف_منتج")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج")
async def delete_product(interaction: discord.Interaction, القسم: str, المنتج: str):
    if str(interaction.guild_id) in servers_data and القسم in servers_data[str(interaction.guild_id)]["categories"] and المنتج in servers_data[str(interaction.guild_id)]["categories"][القسم]:
        del servers_data[str(interaction.guild_id)]["categories"][القسم][المنتج]
        save_data()
        await interaction.response.send_message("🗑️ تم حذف المنتج", ephemeral=True)
    else:
        await interaction.response.send_message("❌ المنتج أو القسم غير موجود", ephemeral=True)

@tree.command(name="حذف_رابط")
async def delete_link(interaction: discord.Interaction):
    if str(interaction.guild_id) in servers_data:
        servers_data[str(interaction.guild_id)]["payment_link"] = ""
        save_data()
        await interaction.response.send_message("🗑️ تم حذف رابط الدفع", ephemeral=True)
    else:
        await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))
