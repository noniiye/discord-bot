import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
import json
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# تحميل البيانات من ملف JSON
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    data = {}

# حفظ البيانات في ملف JSON
def حفظ_البيانات():
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# أوامر التاجر ======================

@bot.tree.command(name="انشاء_متجر", description="إنشاء متجر باسم معين")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: discord.Interaction, الاسم: str):
    guild_id = str(interaction.guild.id)
    data[guild_id] = {"store_name": الاسم, "categories": {}, "trader_channel_id": None, "payment_link": None, "order_channel_id": None}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم: **{الاسم}**", ephemeral=True)

@bot.tree.command(name="رابط_دفع", description="تحديد رابط الدفع ليظهر في الفاتورة")
@app_commands.describe(الرابط="رابط الدفع")
async def رابط_دفع(interaction: discord.Interaction, الرابط: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["payment_link"] = الرابط
    حفظ_البيانات()
    await interaction.response.send_message("✅ تم حفظ رابط الدفع بنجاح.", ephemeral=True)

@bot.tree.command(name="روم_التاجر", description="تحديد روم استقبال الطلبات")
@app_commands.describe(الروم="روم الطلبات")
async def روم_التاجر(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["trader_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم التاجر إلى: {الروم.mention}", ephemeral=True)

@bot.tree.command(name="روم_الطلبات", description="تحديد الروم الذي يُسمح فيه بتنفيذ أمر /طلب")
@app_commands.describe(الروم="روم الطلبات")
async def روم_الطلبات(interaction: discord.Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    data[guild_id]["order_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم الطلبات إلى: {الروم.mention}", ephemeral=True)

# إضافة قسم
@bot.tree.command(name="اضافة_قسم", description="إضافة قسم جديد إلى المتجر")
@app_commands.describe(القسم="اسم القسم")
async def اضافة_قسم(interaction: discord.Interaction, القسم: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    if القسم in data[guild_id]["categories"]:
        await interaction.response.send_message("⚠️ القسم موجود مسبقًا.", ephemeral=True)
        return
    data[guild_id]["categories"][القسم] = {}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إضافة القسم: {القسم}", ephemeral=True)

# إضافة منتج إلى قسم
@bot.tree.command(name="اضافة_منتج", description="إضافة منتج إلى قسم معين")
@app_commands.describe(القسم="اسم القسم", الاسم="اسم المنتج", الكمية="الكمية", السعر="سعر المنتج")
async def اضافة_منتج(interaction: discord.Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    guild_id = str(interaction.guild.id)
    if القسم not in data.get(guild_id, {}).get("categories", {}):
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    data[guild_id]["categories"][القسم][الاسم] = {"الكمية": الكمية, "السعر": السعر}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إضافة المنتج: {الاسم} إلى القسم: {القسم}", ephemeral=True)

# عرض الأقسام
@bot.tree.command(name="الاقسام", description="عرض أقسام المتجر")
async def الاقسام(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in data or not data[guild_id]["categories"]:
        await interaction.response.send_message("❌ لا توجد أقسام حالياً.", ephemeral=True)
        return
    اقسام = list(data[guild_id]["categories"].keys())
    embed = discord.Embed(title="📦 أقسام المتجر", description="\n".join(اقسام), color=0x00ff00)
    await interaction.response.send_message(embed=embed, ephemeral=True)

# عرض منتجات قسم
@bot.tree.command(name="عرض", description="عرض منتجات قسم معين")
@app_commands.describe(القسم="اسم القسم")
async def عرض(interaction: discord.Interaction, القسم: str):
    guild_id = str(interaction.guild.id)
    المنتجات = data.get(guild_id, {}).get("categories", {}).get(القسم)
    if not المنتجات:
        await interaction.response.send_message("❌ هذا القسم غير موجود أو لا يحتوي على منتجات.", ephemeral=True)
        return

    embed = discord.Embed(title=f"📋 منتجات قسم: {القسم}", color=0x00ff00)
    for اسم, تفاصيل in المنتجات.items():
        embed.add_field(name=اسم, value=f"الكمية: {تفاصيل['الكمية']}\nالسعر: {تفاصيل['السعر']} ريال", inline=False)

    await interaction.response.send_message(embed=embed, ephemeral=True)

# أمر طلب تفاعلي
@bot.tree.command(name="طلب", description="تنفيذ طلب عبر اختيار القسم والمنتج")
async def طلب(interaction: discord.Interaction):
    guild_id = str(interaction.guild.id)
    user = interaction.user
    channel = interaction.channel

    if guild_id not in data or not data[guild_id].get("categories"):
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return

    order_channel_id = data[guild_id].get("order_channel_id")
    if order_channel_id and channel.id != order_channel_id:
        await interaction.response.send_message("❌ لا يمكنك تنفيذ الطلب هنا.", ephemeral=True)
        return

    class اخترالقسم(discord.ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=cat) for cat in data[guild_id]["categories"]]
            super().__init__(placeholder="اختر القسم", options=options)

        async def callback(self, interaction2: Interaction):
            القسم = self.values[0]
            await interaction2.response.send_message(view=اخترمنتجView(القسم), ephemeral=True)

    class اخترالقسمView(discord.ui.View):
        def __init__(self):
            super().__init__()
            self.add_item(اخترالقسم())

    await interaction.response.send_message("📂 اختر القسم:", view=اخترالقسمView(), ephemeral=True)

    class اخترمنتج(discord.ui.Select):
        def __init__(self, القسم):
            المنتجات = data[guild_id]["categories"][القسم]
            options = [discord.SelectOption(label=اسم) for اسم in المنتجات]
            super().__init__(placeholder="اختر المنتج", options=options)
            self.القسم = القسم

        async def callback(self, interaction3: Interaction):
            المنتج = self.values[0]
            await interaction3.response.send_modal(كميةModal(self.القسم, المنتج))

    class اخترمنتجView(discord.ui.View):
        def __init__(self, القسم):
            super().__init__()
            self.add_item(اخترمنتج(القسم))

    class كميةModal(discord.ui.Modal, title="أدخل الكمية"):
        كمية = ui.TextInput(label="الكمية المطلوبة", placeholder="مثال: 2", required=True)

        def __init__(self, القسم, المنتج):
            super().__init__()
            self.القسم = القسم
            self.المنتج = المنتج

        async def on_submit(self, interaction4: Interaction):
            try:
                الكمية = int(self.كمية.value)
            except:
                await interaction4.response.send_message("❌ الكمية غير صحيحة.", ephemeral=True)
                return

            تفاصيل = data[guild_id]["categories"][self.القسم][self.المنتج]
            if الكمية > تفاصيل["الكمية"]:
                await interaction4.response.send_message("❌ الكمية المطلوبة غير متوفرة.", ephemeral=True)
                return

            السعر_الاجمالي = تفاصيل["السعر"] * الكمية

            embed = discord.Embed(title="🧾 فاتورة الطلب", color=0x2ecc71)
            embed.add_field(name="🛍️ المتجر", value=data[guild_id]["store_name"], inline=False)
            embed.add_field(name="📁 القسم", value=self.القسم, inline=True)
            embed.add_field(name="📦 المنتج", value=self.المنتج, inline=True)
            embed.add_field(name="🔢 الكمية", value=str(الكمية), inline=True)
            embed.add_field(name="💰 السعر الإجمالي", value=f"{السعر_الاجمالي} ريال", inline=True)
            embed.add_field(name="🔗 رابط الدفع", value=data[guild_id].get("payment_link", "❌ لا يوجد"), inline=False)
            embed.set_footer(text="📩 شكراً لطلبك!")

            class تقييمView(discord.ui.View):
                @discord.ui.button(label="⭐ ⭐ ⭐ ⭐ ⭐", style=discord.ButtonStyle.primary)
                async def تقييم(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                    await interaction_button.response.send_message("✅ شكراً لتقييمك!", ephemeral=True)
                    trader_channel_id = data[guild_id].get("trader_channel_id")
                    if trader_channel_id:
                        trader_channel = bot.get_channel(trader_channel_id)
                        if trader_channel:
                            await trader_channel.send(f"📢 تقييم جديد من {user.mention} على طلبه: ⭐⭐⭐⭐⭐")

                @discord.ui.button(label="❌ إلغاء الطلب", style=discord.ButtonStyle.danger)
                async def الغاء(self, interaction_button: discord.Interaction, button: discord.ui.Button):
                    await interaction_button.response.send_message("🗑️ تم إلغاء الطلب.", ephemeral=True)
                    trader_channel_id = data[guild_id].get("trader_channel_id")
                    if trader_channel_id:
                        trader_channel = bot.get_channel(trader_channel_id)
                        if trader_channel:
                            await trader_channel.send(f"❌ {user.mention} قام بإلغاء الطلب الذي كان يحتوي على المنتج: {self.المنتج} - الكمية: {الكمية}")

            try:
                await user.send(embed=embed)
                await user.send("🎉 هل ترغب في تقييم تجربتك؟", view=تقييمView())
            except:
                await interaction4.response.send_message("❌ لم أستطع إرسال الفاتورة في الخاص.", ephemeral=True)
                return

            trader_channel_id = data[guild_id].get("trader_channel_id")
            if trader_channel_id:
                trader_channel = bot.get_channel(trader_channel_id)
                if trader_channel:
                    await trader_channel.send(f"📥 طلب جديد من {user.mention}\n📦 المنتج: {self.المنتج}\n📁 القسم: {self.القسم}\n🔢 الكمية: {الكمية}\n💰 السعر: {السعر_الاجمالي} ريال")

            await interaction4.response.send_message("✅ تم إرسال الفاتورة في الخاص.", ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))
