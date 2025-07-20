import discord
from discord.ext import commands
from discord import app_commands
import os
import json
from flask import Flask
from threading import Thread

intents = discord.Intents.default()
intents.guilds = True
intents.members = True

bot = commands.Bot(command_prefix="!", intents=intents)

servers_data = {}

def save_data():
    with open("data.json", "w") as f:
        json.dump(servers_data, f)

def load_data():
    global servers_data
    if os.path.exists("data.json"):
        with open("data.json", "r") as f:
            servers_data = json.load(f)

load_data()

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

@bot.tree.command(name="إنشاء_متجر", description="أنشئ متجر باسم مخصص")
@app_commands.describe(اسم="اسم المتجر")
async def create_store(interaction: discord.Interaction, اسم: str):
    gid = str(interaction.guild_id)
    servers_data[gid] = {
        "store_name": اسم,
        "sections": {},
        "payment_link": "",
        "order_channel": None,
        "seller_channel": None
    }
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: {اسم}", color=0x00ff00))

@bot.tree.command(name="إضافة_قسم", description="أضف قسم داخل المتجر")
@app_commands.describe(اسم="اسم القسم")
async def add_section(interaction: discord.Interaction, اسم: str):
    gid = str(interaction.guild_id)
    if gid not in servers_data:
        await interaction.response.send_message("❌ يجب إنشاء المتجر أولاً.")
        return
    servers_data[gid]["sections"][اسم] = []
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة القسم", description=اسم, color=0x00ff00))

@bot.tree.command(name="إضافة_منتج", description="أضف منتج داخل قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def add_product(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    gid = str(interaction.guild_id)
    if القسم not in servers_data[gid]["sections"]:
        await interaction.response.send_message("❌ القسم غير موجود.")
        return
    servers_data[gid]["sections"][القسم].append({"name": المنتج, "qty": الكمية, "price": السعر})
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة المنتج", description=f"{المنتج} - {السعر} ريال - {الكمية} قطعة", color=0x00ff00))

@bot.tree.command(name="تحديد_رابط", description="حدد رابط الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def set_payment(interaction: discord.Interaction, الرابط: str):
    gid = str(interaction.guild_id)
    servers_data[gid]["payment_link"] = الرابط
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد رابط الدفع", description=الرابط, color=0x00ff00))

@bot.tree.command(name="تحديد_روم_الطلبات", description="حدد الروم اللي توصل فيه الطلبات")
@app_commands.describe(الروم="الروم")
async def set_order_room(interaction: discord.Interaction, الروم: discord.TextChannel):
    gid = str(interaction.guild_id)
    servers_data[gid]["order_channel"] = الروم.id
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد روم الطلبات", description=الروم.mention, color=0x00ff00))

@bot.tree.command(name="روم_التاجر", description="حدد الروم الخاص بالتاجر")
@app_commands.describe(الروم="روم التاجر")
async def set_seller_room(interaction: discord.Interaction, الروم: discord.TextChannel):
    gid = str(interaction.guild_id)
    servers_data[gid]["seller_channel"] = الروم.id
    save_data()
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد روم التاجر", description=الروم.mention, color=0x00ff00))

@bot.tree.command(name="طلب", description="طلب منتج من المتجر")
async def make_order(interaction: discord.Interaction):
    gid = str(interaction.guild_id)
    data = servers_data.get(gid)
    if not data or not data["sections"]:
        await interaction.response.send_message("❌ لا يوجد أقسام أو متجر.")
        return

    class القسمMenu(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=sec) for sec in data["sections"]]
            super().__init__(placeholder="اختر القسم", options=options)

        async def callback(self, interaction2):
            section = self.values[0]
            products = data["sections"][section]
            if not products:
                await interaction2.response.send_message("❌ لا يوجد منتجات.", ephemeral=True)
                return

            class المنتجMenu(discord.ui.Select):
                def __init__(self):
                    options = [discord.SelectOption(label=p["name"]) for p in products]
                    super().__init__(placeholder="اختر المنتج", options=options)

                async def callback(self2, interaction3):
                    product_name = self2.values[0]
                    await interaction3.response.send_modal(كميةModal(section, product_name))

            view2 = discord.ui.View()
            view2.add_item(المنتجMenu())
            await interaction2.response.send_message("اختر المنتج:", view=view2, ephemeral=True)

    class كميةModal(discord.ui.Modal, title="كمية المنتج"):
        def __init__(self, القسم, المنتج):
            super().__init__()
            self.القسم = القسم
            self.المنتج = المنتج
            self.كمية = discord.ui.TextInput(label="الكمية المطلوبة", placeholder="مثلاً: 2", required=True)
            self.add_item(self.كمية)

        async def on_submit(self, interaction4):
            qty = int(self.كمية.value)
            for p in data["sections"][self.القسم]:
                if p["name"] == self.المنتج and p["qty"] >= qty:
                    p["qty"] -= qty
                    desc = f"المنتج: {self.المنتج}\nالكمية: {qty}\nالقسم: {self.القسم}"
                    embed = discord.Embed(title=f"فاتورة من متجر {data['store_name']}", description=desc, color=0x00ff00)
                    embed.add_field(name="رابط الدفع", value=data["payment_link"], inline=False)
                    await interaction.user.send(embed=embed)

                    class تقييمView(discord.ui.View):
                        @discord.ui.button(label="⭐", style=discord.ButtonStyle.primary)
                        async def تقييم1(self, button, i):
                            await i.response.send_message("شكرًا لتقييمك ⭐", ephemeral=True)
                            await send_rating(i.user, desc, "⭐")

                        @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.primary)
                        async def تقييم2(self, button, i):
                            await i.response.send_message("شكرًا لتقييمك ⭐⭐", ephemeral=True)
                            await send_rating(i.user, desc, "⭐⭐")

                    await interaction.user.send("يرجى تقييم الطلب:", view=تقييمView())
                    ch = bot.get_channel(data["order_channel"])
                    if ch:
                        await ch.send(embed=discord.Embed(title="📦 طلب جديد", description=f"{desc}\nID: {interaction.user.id}", color=0x3498db))
                    save_data()
                    await interaction4.response.send_message("✅ تم تنفيذ الطلب!", ephemeral=True)
                    return

            await interaction4.response.send_message("❌ المنتج غير متوفر بهذه الكمية.", ephemeral=True)

    view = discord.ui.View()
    view.add_item(القسمMenu())
    await interaction.response.send_message("اختر القسم:", view=view, ephemeral=True)

async def send_rating(user, desc, stars):
    gid = str(user.guild.id)
    ch_id = servers_data[gid].get("seller_channel") or servers_data[gid].get("order_channel")
    ch = bot.get_channel(ch_id)
    if ch:
        await ch.send(embed=discord.Embed(title="⭐ تقييم جديد", description=f"{desc}\nالتقييم: {stars}\nID: {user.id}", color=0xf1c40f))

@bot.tree.command(name="حذف_متجر", description="حذف المتجر بالكامل")
async def delete_store(interaction: discord.Interaction):
    gid = str(interaction.guild_id)
    servers_data.pop(gid, None)
    save_data()
    await interaction.response.send_message("🗑️ تم حذف المتجر.")

@bot.tree.command(name="حذف_قسم", description="حذف قسم من المتجر")
@app_commands.describe(القسم="اسم القسم")
async def delete_section(interaction: discord.Interaction, القسم: str):
    gid = str(interaction.guild_id)
    if القسم in servers_data.get(gid, {}).get("sections", {}):
        del servers_data[gid]["sections"][القسم]
        save_data()
        await interaction.response.send_message("🗑️ تم حذف القسم.")
    else:
        await interaction.response.send_message("❌ القسم غير موجود.")

@bot.tree.command(name="حذف_منتج", description="حذف منتج من قسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج")
async def delete_product(interaction: discord.Interaction, القسم: str, المنتج: str):
    gid = str(interaction.guild_id)
    section = servers_data.get(gid, {}).get("sections", {}).get(القسم)
    if section:
        servers_data[gid]["sections"][القسم] = [p for p in section if p["name"] != المنتج]
        save_data()
        await interaction.response.send_message("🗑️ تم حذف المنتج.")
    else:
        await interaction.response.send_message("❌ القسم غير موجود.")

@bot.tree.command(name="حذف_رابط", description="حذف رابط الدفع")
async def delete_link(interaction: discord.Interaction):
    gid = str(interaction.guild_id)
    servers_data[gid]["payment_link"] = ""
    save_data()
    await interaction.response.send_message("🗑️ تم حذف رابط الدفع.")

app = Flask('')

@app.route('/')
def home():
    return "بوت المتجر شغال."

def run():
    app.run(host='0.0.0.0', port=8080)

def keep_alive():
    Thread(target=run).start()

keep_alive()

TOKEN = os.environ.get("TOKEN")
bot.run(TOKEN)
