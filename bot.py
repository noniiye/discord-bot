import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction
import json
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

data = {}
try:
    with open("data.json", "r") as f:
        data = json.load(f)
except FileNotFoundError:
    pass

def حفظ_البيانات():
    with open("data.json", "w") as f:
        json.dump(data, f, indent=4)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f"✅ Logged in as {bot.user}")

# ===================== أوامر التاجر =====================
@bot.tree.command(name="انشاء_متجر")
@app_commands.describe(الاسم="اسم المتجر")
async def انشاء_متجر(interaction: Interaction, الاسم: str):
    guild_id = str(interaction.guild.id)
    data[guild_id] = {"store_name": الاسم, "categories": {}, "trader_channel_id": None, "payment_link": None, "order_channel_id": None}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إنشاء المتجر باسم **{الاسم}**", ephemeral=True)

@bot.tree.command(name="اضافة_قسم")
@app_commands.describe(القسم="اسم القسم")
async def اضافة_قسم(interaction: Interaction, القسم: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    data[guild_id]["categories"][القسم] = {}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إضافة القسم **{القسم}**", ephemeral=True)

@bot.tree.command(name="اضافة_منتج")
@app_commands.describe(القسم="القسم", الاسم="اسم المنتج", الكمية="الكمية", السعر="السعر")
async def اضافة_منتج(interaction: Interaction, القسم: str, الاسم: str, الكمية: int, السعر: int):
    guild_id = str(interaction.guild.id)
    if القسم not in data.get(guild_id, {}).get("categories", {}):
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    data[guild_id]["categories"][القسم][الاسم] = {"الكمية": الكمية, "السعر": السعر}
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم إضافة المنتج **{الاسم}** في القسم **{القسم}**", ephemeral=True)

@bot.tree.command(name="رابط_دفع")
@app_commands.describe(الرابط="الرابط")
async def رابط_دفع(interaction: Interaction, الرابط: str):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ لم يتم إنشاء متجر بعد.", ephemeral=True)
        return
    data[guild_id]["payment_link"] = الرابط
    حفظ_البيانات()
    await interaction.response.send_message("✅ تم حفظ رابط الدفع بنجاح.", ephemeral=True)

@bot.tree.command(name="روم_التاجر")
@app_commands.describe(الروم="روم الطلبات للتاجر")
async def روم_التاجر(interaction: Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    data[guild_id]["trader_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم التاجر إلى {الروم.mention}", ephemeral=True)

@bot.tree.command(name="روم_الطلبات")
@app_commands.describe(الروم="الروم المسموح فيه الطلب")
async def روم_الطلبات(interaction: Interaction, الروم: discord.TextChannel):
    guild_id = str(interaction.guild.id)
    data[guild_id]["order_channel_id"] = الروم.id
    حفظ_البيانات()
    await interaction.response.send_message(f"✅ تم تعيين روم الطلبات إلى {الروم.mention}", ephemeral=True)

# ===================== أمر /طلب =====================

class تاكيدطلب(ui.View):
    def __init__(self, interaction: Interaction, القسم, المنتج, الكمية, السعر_الوحدة):
        super().__init__(timeout=None)
        self.interaction = interaction
        self.القسم = القسم
        self.المنتج = المنتج
        self.الكمية = الكمية
        self.السعر_الوحدة = السعر_الوحدة

    @ui.button(label="✅ تأكيد الطلب", style=discord.ButtonStyle.green)
    async def تأكيد(self, interaction: Interaction, button: ui.Button):
        guild_id = str(interaction.guild.id)
        المستخدم = interaction.user
        السعر_الاجمالي = self.الكمية * self.السعر_الوحدة

        embed = discord.Embed(title="🧾 فاتورتك", color=0x2ecc71)
        embed.add_field(name="📦 المنتج", value=f"{self.المنتج}", inline=True)
        embed.add_field(name="📁 القسم", value=f"{self.القسم}", inline=True)
        embed.add_field(name="🔢 الكمية", value=str(self.الكمية), inline=True)
        embed.add_field(name="💰 السعر الإجمالي", value=f"{السعر_الاجمالي} ريال", inline=True)
        embed.add_field(name="🔗 رابط الدفع", value=data[guild_id].get("payment_link", "❌ لا يوجد"), inline=False)
        embed.set_footer(text="يرجى إرسال الإيصال للتاجر بعد الدفع")

        زر_الغاء = ui.View()
        زر_الغاء.add_item(ui.Button(label="❌ إلغاء الطلب", style=discord.ButtonStyle.danger, custom_id="cancel_order"))

        await المستخدم.send(embed=embed, view=زر_الغاء)

        trader_channel_id = data[guild_id].get("trader_channel_id")
        if trader_channel_id:
            channel = bot.get_channel(trader_channel_id)
            if channel:
                await channel.send(f"📥 طلب جديد من <@{المستخدم.id}>:\n• القسم: {self.القسم}\n• المنتج: {self.المنتج}\n• الكمية: {self.الكمية}")

        تقييم = ui.View()
        for i in range(1, 6):
            تقييم.add_item(ui.Button(label="⭐" * i, style=discord.ButtonStyle.secondary, custom_id=f"rate_{i}"))
        await المستخدم.send("📊 يرجى تقييم الطلب:", view=تقييم)
        await interaction.response.send_message("✅ تم تنفيذ الطلب! تم إرسال الفاتورة والتقييم في الخاص.", ephemeral=True)

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type == discord.InteractionType.component:
        if interaction.data.get("custom_id", "").startswith("rate_"):
            rating = interaction.data["custom_id"].split("_")[-1]
            await interaction.response.send_message("✅ شكرًا لتقييمك!", ephemeral=True)
            guild_id = str(interaction.guild.id)
            ch_id = data[guild_id].get("trader_channel_id")
            if ch_id:
                channel = bot.get_channel(ch_id)
                if channel:
                    await channel.send(f"⭐ تم تقييم الطلب من <@{interaction.user.id}> بعدد نجوم: {rating}")
        elif interaction.data.get("custom_id") == "cancel_order":
            await interaction.response.send_message("❌ تم إلغاء الطلب بنجاح.", ephemeral=True)
            return
    await bot.process_application_commands(interaction)

@bot.tree.command(name="طلب")
async def طلب(interaction: Interaction):
    guild_id = str(interaction.guild.id)
    if guild_id not in data:
        await interaction.response.send_message("❌ المتجر غير موجود.", ephemeral=True)
        return
    allowed_channel = data[guild_id].get("order_channel_id")
    if allowed_channel and interaction.channel.id != allowed_channel:
        await interaction.response.send_message("❌ لا يمكنك تنفيذ هذا الأمر في هذا الروم.", ephemeral=True)
        return

    الأقسام = list(data[guild_id]["categories"].keys())
    if not الأقسام:
        await interaction.response.send_message("❌ لا يوجد أقسام متاحة حالياً.", ephemeral=True)
        return

    class قائمة_الأقسام(ui.Select):
        def __init__(self):
            options = [discord.SelectOption(label=قسم) for قسم in الأقسام]
            super().__init__(placeholder="اختر القسم", options=options)

        async def callback(self, interaction2: Interaction):
            القسم = self.values[0]
            المنتجات = data[guild_id]["categories"][القسم]
            if not المنتجات:
                await interaction2.response.send_message("❌ لا يوجد منتجات في هذا القسم.", ephemeral=True)
                return

            class قائمة_المنتجات(ui.Select):
                def __init__(self):
                    options = [discord.SelectOption(label=منتج) for منتج in المنتجات]
                    super().__init__(placeholder="اختر المنتج", options=options)

                async def callback(self, interaction3: Interaction):
                    المنتج = self.values[0]
                    السعر = المنتجات[المنتج]["السعر"]

                    class كمية(ui.Modal, title="أدخل الكمية"):
                        الكمية = ui.TextInput(label="الكمية المطلوبة", placeholder="مثال: 2", required=True)

                        async def on_submit(self, interaction4: Interaction):
                            try:
                                num = int(self.الكمية.value)
                                if num <= 0:
                                    raise ValueError
                            except:
                                await interaction4.response.send_message("❌ الكمية غير صالحة.", ephemeral=True)
                                return

                            await interaction4.response.defer(ephemeral=True)
                            await interaction4.followup.send(view=تاكيدطلب(interaction, القسم, المنتج, num, السعر))

                    await interaction3.response.send_modal(كمية())

            await interaction2.response.send_message("🛒 اختر المنتج:", view=ui.View().add_item(قائمة_المنتجات()), ephemeral=True)

    await interaction.response.send_message("📁 اختر القسم:", view=ui.View().add_item(قائمة_الأقسام()), ephemeral=True)

keep_alive()
bot.run(os.getenv("TOKEN"))
