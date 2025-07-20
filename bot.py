import discord
from discord.ext import commands
from discord import app_commands
import os
from keep_alive import keep_alive

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

servers_data = {}

class QuantityModal(discord.ui.Modal, title="🔢 إدخال الكمية المطلوبة"):
    الكمية = discord.ui.TextInput(label="أدخل الكمية (رقم فقط):", style=discord.TextStyle.short)

    def __init__(self, parent, interaction, القسم, المنتج, السعر):
        super().__init__()
        self.parent = parent
        self.interaction = interaction
        self.القسم = القسم
        self.المنتج = المنتج
        self.السعر = السعر

    async def on_submit(self, interaction: discord.Interaction):
        try:
            quantity = int(self.الكمية.value)
            if quantity <= 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ يجب إدخال رقم صالح.", ephemeral=True)
            return

        guild_id = interaction.guild_id
        user = interaction.user
        المتج0631 = servers_data[guild_id]["store_name"]
        رابط_الدفع = servers_data[guild_id].get("payment_link", "لم يتم تحديد رابط دفع بعد.")
        الطلب = f"{self.القسم} - {self.المنتج} - الكمية: {quantity}"

        embed = discord.Embed(title="📜 فاتورتك", color=discord.Color.blue())
        embed.add_field(name="المتج0631", value=المتج0631, inline=False)
        embed.add_field(name="الطلب", value=الطلب, inline=False)
        embed.add_field(name="رابط الدفع", value=رابط_الدفع, inline=False)

        try:
            await user.send(embed=embed)
        except:
            await interaction.followup.send("❌ لا يمكن إرسال فاتورة للخاص. تأكد أن رسائلك الخاصة مفع-لة.", ephemeral=True)
            return

        await interaction.response.send_message("✅ تم تنفيذ الطلب. تم إرسال الفاتورة في الخاص.", ephemeral=True)

        # إرسال التقييم
        view = discord.ui.View()
        for i in range(1, 6):
            view.add_item(discord.ui.Button(label=str(i), style=discord.ButtonStyle.primary, custom_id=f"rating_{i}_{guild_id}_{user.id}_{الطلب}"))

        try:
            await user.send("⭐ قيّم طلبك من 1 إلى 5:", view=view)
        except:
            pass

        # إرسال الطلب إلى روم التاجر
        trader_channel_id = servers_data[guild_id].get("trader_channel")
        if trader_channel_id:
            trader_channel = bot.get_channel(trader_channel_id)
            if trader_channel:
                await trader_channel.send(embed=discord.Embed(
                    title="📦 طلب جديد",
                    description=f"**الطلب:** {الطلب}\n**معرف العميل:** {user.id}",
                    color=discord.Color.orange()
                ))

keep_alive()
bot.run(os.getenv("TOKEN"))
