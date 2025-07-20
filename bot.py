import discord
from discord.ext import commands
from discord import app_commands
import os
import asyncio
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

servers_data = {}

@bot.event
async def on_ready():
    await tree.sync()
    print(f"✅ تم تسجيل الدخول كـ {bot.user}")

@tree.command(name="إنشاء_متجر", description="إنشاء متجر باسم مخصص")
@app_commands.describe(اسم="اسم المتجر")
async def create_store(interaction: discord.Interaction, اسم: str):
    gid = str(interaction.guild.id)
    if gid in servers_data:
        return await interaction.response.send_message(embed=discord.Embed(title="⚠️ يوجد متجر بالفعل", color=0xffcc00), ephemeral=True)
    servers_data[gid] = {"store_name": اسم, "categories": {}, "payment_link": None, "order_channel": None}
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إنشاء المتجر", description=f"اسم المتجر: **{اسم}**", color=0x00ff00), ephemeral=True)

@tree.command(name="إضافة_قسم", description="إضافة قسم داخل المتجر")
@app_commands.describe(اسم="اسم القسم")
async def add_category(interaction: discord.Interaction, اسم: str):
    gid = str(interaction.guild.id)
    if gid not in servers_data:
        return await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)
    servers_data[gid]["categories"][اسم] = {}
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة القسم", description=اسم, color=0x00ff00), ephemeral=True)

@tree.command(name="إضافة_منتج", description="إضافة منتج للقسم")
@app_commands.describe(القسم="اسم القسم", المنتج="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def add_product(interaction: discord.Interaction, القسم: str, المنتج: str, الكمية: int, السعر: float):
    gid = str(interaction.guild.id)
    data = servers_data.get(gid)
    if not data or القسم not in data["categories"]:
        return await interaction.response.send_message("❌ تحقق من وجود القسم", ephemeral=True)
    data["categories"][القسم][المنتج] = {"quantity": الكمية, "price": السعر}
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم إضافة المنتج", description=f"{المنتج} - {السعر}$ × {الكمية}", color=0x00ff00), ephemeral=True)

@tree.command(name="تحديد_رابط", description="تحديد رابط الدفع")
@app_commands.describe(الرابط="رابط الدفع")
async def set_payment(interaction: discord.Interaction, الرابط: str):
    gid = str(interaction.guild.id)
    if gid not in servers_data:
        return await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)
    servers_data[gid]["payment_link"] = الرابط
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد الرابط", description=رابط, color=0x00ff00), ephemeral=True)

@tree.command(name="تحديد_روم", description="تحديد روم استلام الطلبات")
@app_commands.describe(channel="الروم")
async def set_channel(interaction: discord.Interaction, channel: discord.TextChannel):
    gid = str(interaction.guild.id)
    if gid not in servers_data:
        return await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)
    servers_data[gid]["order_channel"] = channel.id
    await interaction.response.send_message(embed=discord.Embed(title="✅ تم تحديد روم الطلبات", description=channel.mention, color=0x00ff00), ephemeral=True)

@tree.command(name="حذف", description="حذف متجر أو قسم أو منتج أو رابط")
@app_commands.describe(نوع="ما الذي تريد حذفه", اسم="اسم العنصر")
async def delete(interaction: discord.Interaction, نوع: str, اسم: str = None):
    gid = str(interaction.guild.id)
    data = servers_data.get(gid)
    if not data:
        return await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)

    msg = "❌ لم يتم العثور"
    if نوع == "متجر":
        servers_data.pop(gid)
        msg = "✅ تم حذف المتجر"
    elif نوع == "قسم" and اسم in data["categories"]:
        data["categories"].pop(اسم)
        msg = f"✅ تم حذف القسم {اسم}"
    elif نوع == "منتج":
        for قسم, منتجات in data["categories"].items():
            if اسم in منتجات:
                منتجات.pop(اسم)
                msg = f"✅ تم حذف المنتج {اسم}"
                break
    elif نوع == "رابط":
        data["payment_link"] = None
        msg = "✅ تم حذف رابط الدفع"

    await interaction.response.send_message(embed=discord.Embed(title=msg, color=0xff0000), ephemeral=True)

@tree.command(name="طلب", description="تنفيذ طلب")
async def order(interaction: discord.Interaction):
    gid = str(interaction.guild.id)
    user = interaction.user
    data = servers_data.get(gid)
    if not data:
        return await interaction.response.send_message("❌ لا يوجد متجر", ephemeral=True)

    categories = list(data["categories"].keys())
    if not categories:
        return await interaction.response.send_message("❌ لا يوجد أقسام", ephemeral=True)

    async def ask_dropdown(options, placeholder):
        class Select(discord.ui.Select):
            def __init__(self):
                super().__init__(placeholder=placeholder, options=[discord.SelectOption(label=opt) for opt in options])
            async def callback(self, interaction2):
                self.view.value = self.values[0]
                self.view.stop()

        class Dropdown(discord.ui.View):
            def __init__(self):
                super().__init__(timeout=60)
                self.value = None
                self.add_item(Select())

        view = Dropdown()
        await interaction.followup.send("اختر:", view=view, ephemeral=True)
        await view.wait()
        return view.value

    await interaction.response.defer(ephemeral=True)
    القسم = await ask_dropdown(categories, "اختر القسم")
    if not القسم:
        return

    المنتجات = list(data["categories"][القسم].keys())
    المنتج = await ask_dropdown(المنتجات, "اختر المنتج")
    if not المنتج:
        return

    الكميات = [str(i) for i in range(1, data["categories"][القسم][المنتج]["quantity"] + 1)]
    الكمية = await ask_dropdown(الكميات, "اختر الكمية")
    if not الكمية:
        return

    السعر = data["categories"][القسم][المنتج]["price"]
    رابط = data.get("payment_link") or "غير محدد"
    الوصف = f"**{المنتج}** × {الكمية} = {int(الكمية) * السعر}$"

    order_channel_id = data.get("order_channel")
    if order_channel_id:
        order_embed = discord.Embed(title="📦 طلب جديد", description=الوصف, color=0x3498db)
        order_embed.add_field(name="المستخدم", value=f"{user.mention} ({user.id})", inline=False)
        await bot.get_channel(order_channel_id).send(embed=order_embed)

    invoice = discord.Embed(title=f"🧾 فاتورة من متجر {data['store_name']}", description=الوصف, color=0x2ecc71)
    invoice.add_field(name="رابط الدفع", value=رابط)
    await user.send(embed=invoice)

    class Rate(discord.ui.View):
        def __init__(self):
            super().__init__(timeout=120)

        @discord.ui.button(label="⭐", style=discord.ButtonStyle.secondary)
        async def star1(self, interaction2, _):
            await interaction2.response.send_message("✅ شكرًا لتقييمك ⭐", ephemeral=True)
            await send_rating(1)

        @discord.ui.button(label="⭐⭐", style=discord.ButtonStyle.secondary)
        async def star2(self, interaction2, _):
            await interaction2.response.send_message("✅ شكرًا لتقييمك ⭐⭐", ephemeral=True)
            await send_rating(2)

        @discord.ui.button(label="⭐⭐⭐", style=discord.ButtonStyle.secondary)
        async def star3(self, interaction2, _):
            await interaction2.response.send_message("✅ شكرًا لتقييمك ⭐⭐⭐", ephemeral=True)
            await send_rating(3)

    async def send_rating(stars):
        if order_channel_id:
            embed = discord.Embed(title="⭐ تقييم جديد", description=f"{stars} نجوم\n{الوصف}\nID: {user.id}", color=0xf1c40f)
            await bot.get_channel(order_channel_id).send(embed=embed)

    await user.send("📝 كيف تقيم طلبك؟", view=Rate())

keep_alive()
bot.run(os.getenv("TOKEN"))
