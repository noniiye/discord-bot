import discord
from discord.ext import commands
from discord import app_commands, ui, Interaction, Embed, ButtonStyle
import sqlite3

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
tree = bot.tree

# ======= إعداد قاعدة البيانات =========
conn = sqlite3.connect("store.db")
c = conn.cursor()

# جدول المتاجر: guild_id, owner_id, store_name, order_channel_id, payment_link
c.execute("""
CREATE TABLE IF NOT EXISTS stores (
    guild_id INTEGER PRIMARY KEY,
    owner_id INTEGER,
    store_name TEXT,
    order_channel_id INTEGER,
    payment_link TEXT
)
""")

# جدول الأقسام: guild_id + category_name
c.execute("""
CREATE TABLE IF NOT EXISTS categories (
    guild_id INTEGER,
    category_name TEXT,
    PRIMARY KEY(guild_id, category_name)
)
""")

# جدول المنتجات: guild_id + category_name + product_name
c.execute("""
CREATE TABLE IF NOT EXISTS products (
    guild_id INTEGER,
    category_name TEXT,
    product_name TEXT,
    price INTEGER,
    quantity INTEGER,
    PRIMARY KEY(guild_id, category_name, product_name)
)
""")

conn.commit()

# ====== دوال مساعدة ======
def get_store(guild_id):
    c.execute("SELECT owner_id, store_name, order_channel_id, payment_link FROM stores WHERE guild_id=?", (guild_id,))
    row = c.fetchone()
    if row:
        return {
            "owner_id": row[0],
            "store_name": row[1],
            "order_channel_id": row[2],
            "payment_link": row[3],
        }
    return None

def is_owner(interaction: Interaction):
    store = get_store(interaction.guild.id)
    return store and store["owner_id"] == interaction.user.id

def get_categories(guild_id):
    c.execute("SELECT category_name FROM categories WHERE guild_id=?", (guild_id,))
    return [row[0] for row in c.fetchall()]

def get_products(guild_id, category):
    c.execute("SELECT product_name, price, quantity FROM products WHERE guild_id=? AND category_name=?", (guild_id, category))
    return [{"name": row[0], "price": row[1], "quantity": row[2]} for row in c.fetchall()]

def update_product_quantity(guild_id, category, product_name, new_quantity):
    c.execute("UPDATE products SET quantity=? WHERE guild_id=? AND category_name=? AND product_name=?", (new_quantity, guild_id, category, product_name))
    conn.commit()

# =========== حدث تشغيل البوت ===========
@bot.event
async def on_ready():
    print(f"✅ Bot ready as {bot.user}")
    await tree.sync()

# =========== إنشاء متجر ===========
class StoreNameModal(ui.Modal, title="🏬 إنشاء متجر جديد"):
    store_name = ui.TextInput(label="اسم المتجر", placeholder="أدخل اسم المتجر هنا", max_length=50)

    async def on_submit(self, interaction: Interaction):
        if get_store(interaction.guild.id):
            await interaction.response.send_message("❌ يوجد متجر بالفعل في هذا السيرفر.", ephemeral=True)
            return
        c.execute("INSERT INTO stores (guild_id, owner_id, store_name) VALUES (?, ?, ?)",
                  (interaction.guild.id, interaction.user.id, self.store_name.value.strip()))
        conn.commit()
        await interaction.response.send_message(f"✅ تم إنشاء المتجر: **{self.store_name.value.strip()}**", ephemeral=True)

@tree.command(name="انشاء_متجر", description="🏬 إنشاء متجر جديد")
async def create_store(interaction: Interaction):
    if get_store(interaction.guild.id):
        await interaction.response.send_message("❌ يوجد متجر بالفعل في هذا السيرفر.", ephemeral=True)
        return
    await interaction.response.send_modal(StoreNameModal())

# =========== تحديد روم الطلبات ===========
class OrderChannelModal(ui.Modal, title="🏢 تحديد روم الطلبات"):
    channel_name = ui.TextInput(label="اسم روم الطلبات", placeholder="اكتب اسم الروم النصي بدقة", max_length=100)

    async def on_submit(self, interaction: Interaction):
        guild = interaction.guild
        name = self.channel_name.value.strip()
        channel = discord.utils.get(guild.text_channels, name=name)
        if channel is None:
            await interaction.response.send_message(f"❌ لم أجد روم نصي باسم **{name}** في السيرفر.", ephemeral=True)
            return
        c.execute("UPDATE stores SET order_channel_id=? WHERE guild_id=?", (channel.id, interaction.guild.id))
        conn.commit()
        await interaction.response.send_message(f"✅ تم تعيين روم الطلبات إلى: {channel.mention}", ephemeral=True)

@tree.command(name="تحديد_روم_الطلبات", description="🏢 تعيين روم استقبال الطلبات")
async def set_order_channel(interaction: Interaction):
    if not is_owner(interaction):
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    await interaction.response.send_modal(OrderChannelModal())

# =========== إضافة قسم ===========
@tree.command(name="اضافه_قسم", description="➕ إضافة قسم جديد")
@app_commands.describe(name="اسم القسم")
async def add_category(interaction: Interaction, name: str):
    if not is_owner(interaction):
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    if name in get_categories(interaction.guild.id):
        await interaction.response.send_message("❌ هذا القسم موجود مسبقاً.", ephemeral=True)
        return
    c.execute("INSERT INTO categories (guild_id, category_name) VALUES (?, ?)", (interaction.guild.id, name))
    conn.commit()
    await interaction.response.send_message(f"✅ تم إنشاء القسم: **{name}**", ephemeral=True)

# =========== إضافة منتج ===========
class AddProductModal(ui.Modal, title="➕ إضافة منتج جديد"):
    product_name = ui.TextInput(label="اسم المنتج", max_length=50)
    price = ui.TextInput(label="السعر (ريال)", placeholder="أدخل السعر كرقم فقط")
    quantity = ui.TextInput(label="الكمية المتوفرة", placeholder="أدخل الكمية كرقم فقط")

    def __init__(self, guild_id, category):
        super().__init__()
        self.guild_id = guild_id
        self.category = category

    async def on_submit(self, interaction: Interaction):
        try:
            price = int(self.price.value)
            quantity = int(self.quantity.value)
            if price < 0 or quantity < 0:
                raise ValueError()
        except ValueError:
            await interaction.response.send_message("❌ السعر والكمية يجب أن يكونوا أعداد صحيحة وموجبة.", ephemeral=True)
            return
        products = get_products(self.guild_id, self.category)
        if any(p["name"] == self.product_name.value.strip() for p in products):
            await interaction.response.send_message("❌ هذا المنتج موجود مسبقاً في هذا القسم.", ephemeral=True)
            return
        c.execute(
            "INSERT INTO products (guild_id, category_name, product_name, price, quantity) VALUES (?, ?, ?, ?, ?)",
            (self.guild_id, self.category, self.product_name.value.strip(), price, quantity))
        conn.commit()
        await interaction.response.send_message(f"✅ تم إضافة المنتج **{self.product_name.value.strip()}** إلى القسم **{self.category}**", ephemeral=True)

@tree.command(name="اضافه_منتج", description="➕ إضافة منتج لقسم معين")
@app_commands.describe(section="اسم القسم")
async def add_product(interaction: Interaction, section: str):
    if not is_owner(interaction):
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    if section not in get_categories(interaction.guild.id):
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    await interaction.response.send_modal(AddProductModal(interaction.guild.id, section))

# =========== طلب المنتجات ===========
class QuantityModal(ui.Modal, title="🛒 تحديد الكمية المطلوبة"):
    quantity = ui.TextInput(label="كمية المنتج", placeholder="أدخل رقم الكمية المطلوبة", max_length=5)

    def __init__(self, guild_id, category, product):
        super().__init__()
        self.guild_id = guild_id
        self.category = category
        self.product = product

    async def on_submit(self, interaction: Interaction):
        try:
            qty = int(self.quantity.value)
            if qty <= 0:
                raise ValueError()
        except ValueError:
            await interaction.response.send_message("❌ أدخل كمية صحيحة أكبر من صفر.", ephemeral=True)
            return
        if qty > self.product["quantity"]:
            await interaction.response.send_message(f"❌ الكمية المطلوبة أكبر من المتوفرة ({self.product['quantity']}).", ephemeral=True)
            return

        new_quantity = self.product["quantity"] - qty
        update_product_quantity(self.guild_id, self.category, self.product["name"], new_quantity)

        # إرسال طلب لصاحب المتجر في روم الطلبات
        store = get_store(interaction.guild.id)
        if store and store["order_channel_id"]:
            channel = interaction.guild.get_channel(store["order_channel_id"])
            if channel:
                embed = Embed(title="🛎️ طلب جديد", color=0xf1c40f)
                embed.add_field(name="العميل", value=interaction.user.mention, inline=False)
                embed.add_field(name="القسم", value=self.category, inline=True)
                embed.add_field(name="المنتج", value=self.product["name"], inline=True)
                embed.add_field(name="الكمية", value=str(qty), inline=True)
                embed.add_field(name="السعر", value=f"{self.product['price']} ريال", inline=True)
                embed.set_footer(text=f"ID العميل: {interaction.user.id}")

                try:
                    await channel.send(embed=embed)
                except Exception as e:
                    await interaction.response.send_message(f"❌ حدث خطأ في إرسال الطلب لروم الطلبات: {e}", ephemeral=True)
                    return
            else:
                await interaction.response.send_message("❌ روم الطلبات غير موجود.", ephemeral=True)
                return
        else:
            await interaction.response.send_message("❌ لم يتم تحديد روم الطلبات، يرجى تحديده أولاً باستخدام /تحديد_روم_الطلبات", ephemeral=True)
            return

        # إرسال الفاتورة للعميل مع رابط الدفع والتنبيه
        payment_link = store.get("payment_link") or "https://payment-link.com"
        total_price = self.product["price"] * qty
        invoice_embed = Embed(title="📄 فاتورة طلبك", color=0x2ecc71)
        invoice_embed.add_field(name="القسم", value=self.category, inline=True)
        invoice_embed.add_field(name="المنتج", value=self.product["name"], inline=True)
        invoice_embed.add_field(name="الكمية", value=str(qty), inline=True)
        invoice_embed.add_field(name="السعر للوحدة", value=f"{self.product['price']} ريال", inline=True)
        invoice_embed.add_field(name="الإجمالي", value=f"{total_price} ريال", inline=True)
        invoice_embed.add_field(name="رابط الدفع", value=f"[اضغط هنا للدفع]({payment_link})", inline=False)
        invoice_embed.add_field(name="ملاحظة", value="الرجاء إرسال إيصال الدفع لتأكيد الطلب. أي تلاعب أو تزوير يعرضك للمساءلة والحظر النهائي.", inline=False)

        try:
            await interaction.user.send(embed=invoice_embed)
            await interaction.response.send_message("✅ تم إرسال الفاتورة على الخاص، تحقق من رسائلك الخاصة.", ephemeral=True)
        except discord.Forbidden:
            await interaction.response.send_message("❌ لا أستطيع إرسال رسالة خاصة لك، يرجى تفعيل خاصية الرسائل الخاصة.", ephemeral=True)

# =========== اختيار الأقسام والمنتجات باستخدام أزرار ===========
class CategorySelectView(ui.View):
    def __init__(self, user_id, guild_id):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_id = guild_id
        categories = get_categories(guild_id)
        for category in categories:
            self.add_item(ui.Button(label=category, style=ButtonStyle.primary, custom_id=f"category_{category}"))

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("🚫 هذا ليس طلبك.", ephemeral=True)
            return False
        return True

    @ui.button(label="إلغاء الطلب", style=ButtonStyle.danger, custom_id="cancel_order")
    async def cancel_order(self, interaction: Interaction, button: ui.Button):
        await interaction.response.edit_message(content="❌ تم إلغاء الطلب.", view=None)

class ProductSelectView(ui.View):
    def __init__(self, user_id, guild_id, category):
        super().__init__(timeout=120)
        self.user_id = user_id
        self.guild_id = guild_id
        self.category = category
        products = get_products(guild_id, category)
        for product in products:
            self.add_item(ui.Button(label=product["name"], style=ButtonStyle.secondary, custom_id=f"product_{category}_{product['name']}"))

    async def interaction_check(self, interaction: Interaction):
        if interaction.user.id != self.user_id:
            await interaction.response.send_message("🚫 هذا ليس طلبك.", ephemeral=True)
            return False
        return True

    @ui.button(label="عودة للأقسام", style=ButtonStyle.primary, custom_id="back_to_categories")
    async def back_to_categories(self, interaction: Interaction, button: ui.Button):
        view = CategorySelectView(interaction.user.id, self.guild_id)
        await interaction.response.edit_message(content="📂 اختر القسم:", view=view)

# =========== أمر طلب ===========
@tree.command(name="طلب", description="🛒 تقديم طلب")
async def order_cmd(interaction: Interaction):
    categories = get_categories(interaction.guild.id)
    if not categories:
        await interaction.response.send_message("❌ لا يوجد أقسام أو منتجات في المتجر حالياً.", ephemeral=True)
        return
    view = CategorySelectView(interaction.user.id, interaction.guild.id)
    await interaction.response.send_message(f"🏬 متجر: **{get_store(interaction.guild.id)['store_name'] or 'غير محدد'}**\n📂 اختر القسم:", view=view, ephemeral=True)

# =========== التعامل مع الأزرار ===========
@bot.event
async def on_interaction(interaction: Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data.get("custom_id", "")
    if custom_id.startswith("category_"):
        category = custom_id[len("category_"):]
        guild_id = interaction.guild.id
        categories = get_categories(guild_id)
        if category not in categories:
            await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
            return
        view = ProductSelectView(interaction.user.id, guild_id, category)
        await interaction.response.edit_message(content=f"📂 اختر منتج من قسم **{category}**:", view=view)

    elif custom_id.startswith("product_"):
        parts = custom_id.split("_", 2)
        if len(parts) < 3:
            await interaction.response.send_message("❌ خطأ في اختيار المنتج.", ephemeral=True)
            return
        category = parts[1]
        product_name = parts[2]
        guild_id = interaction.guild.id
        products = get_products(guild_id, category)
        product = next((p for p in products if p["name"] == product_name), None)
        if not product:
            await interaction.response.send_message("❌ المنتج غير موجود.", ephemeral=True)
            return
        modal = QuantityModal(guild_id, category, product)
        await interaction.response.send_modal(modal)

    elif custom_id == "cancel_order":
        await interaction.response.edit_message(content="❌ تم إلغاء الطلب.", view=None)

    elif custom_id == "back_to_categories":
        guild_id = interaction.guild.id
        view = CategorySelectView(interaction.user.id, guild_id)
        await interaction.response.edit_message(content=f"🏬 متجر: **{get_store(guild_id)['store_name'] or 'غير محدد'}**\n📂 اختر القسم:", view=view)

# =========== أمر تعيين رابط الدفع ===========
@tree.command(name="رابط_الدفع", description="🔗 تحديد رابط الدفع")
@app_commands.describe(url="رابط الدفع الخاص بك")
async def set_payment_link(interaction: Interaction, url: str):
    if not is_owner(interaction):
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    c.execute("UPDATE stores SET payment_link=? WHERE guild_id=?", (url, interaction.guild.id))
    conn.commit()
    await interaction.response.send_message(f"✅ تم تحديث رابط الدفع إلى: {url}", ephemeral=True)

# =========== أمر حذف قسم ===========
@tree.command(name="حذف_قسم", description="🗑️ حذف قسم بالكامل")
@app_commands.describe(name="اسم القسم")
async def delete_category(interaction: Interaction, name: str):
    if not is_owner(interaction):
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    categories = get_categories(interaction.guild.id)
    if name not in categories:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    c.execute("DELETE FROM categories WHERE guild_id=? AND category_name=?", (interaction.guild.id, name))
    c.execute("DELETE FROM products WHERE guild_id=? AND category_name=?", (interaction.guild.id, name))
    conn.commit()
    await interaction.response.send_message(f"✅ تم حذف القسم: **{name}**", ephemeral=True)

# =========== أمر حذف منتج ===========
@tree.command(name="حذف_منتج", description="🗑️ حذف منتج من قسم")
@app_commands.describe(section="اسم القسم", product_name="اسم المنتج")
async def delete_product(interaction: Interaction, section: str, product_name: str):
    if not is_owner(interaction):
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    categories = get_categories(interaction.guild.id)
    if section not in categories:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    products = get_products(interaction.guild.id, section)
    if not any(p["name"] == product_name for p in products):
        await interaction.response.send_message("❌ المنتج غير موجود.", ephemeral=True)
        return
    c.execute("DELETE FROM products WHERE guild_id=? AND category_name=? AND product_name=?",
              (interaction.guild.id, section, product_name))
    conn.commit()
    await interaction.response.send_message(f"✅ تم حذف المنتج **{product_name}** من القسم **{section}**", ephemeral=True)

# =========== أمر تعديل منتج ===========
class EditProductModal(ui.Modal, title="✏️ تعديل منتج"):
    price = ui.TextInput(label="السعر", placeholder="أدخل السعر (رقم فقط)")
    quantity = ui.TextInput(label="الكمية المتوفرة", placeholder="أدخل الكمية (رقم فقط)")

    def __init__(self, guild_id, category, product_name):
        super().__init__()
        self.guild_id = guild_id
        self.category = category
        self.product_name = product_name

    async def on_submit(self, interaction: Interaction):
        try:
            price = int(self.price.value)
            quantity = int(self.quantity.value)
            if price < 0 or quantity < 0:
                raise ValueError
        except ValueError:
            await interaction.response.send_message("❌ السعر والكمية يجب أن يكونا أعداد صحيحة موجبة.", ephemeral=True)
            return
        c.execute("UPDATE products SET price=?, quantity=? WHERE guild_id=? AND category_name=? AND product_name=?",
                  (price, quantity, self.guild_id, self.category, self.product_name))
        conn.commit()
        await interaction.response.send_message(f"✅ تم تحديث المنتج **{self.product_name}**.", ephemeral=True)

@tree.command(name="تعديل_منتج", description="✏️ تعديل سعر وكمية منتج")
@app_commands.describe(section="اسم القسم", product_name="اسم المنتج")
async def edit_product(interaction: Interaction, section: str, product_name: str):
    if not is_owner(interaction):
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    categories = get_categories(interaction.guild.id)
    if section not in categories:
        await interaction.response.send_message("❌ القسم غير موجود.", ephemeral=True)
        return
    products = get_products(interaction.guild.id, section)
    if not any(p["name"] == product_name for p in products):
        await interaction.response.send_message("❌ المنتج غير موجود.", ephemeral=True)
        return
    modal = EditProductModal(interaction.guild.id, section, product_name)
    await interaction.response.send_modal(modal)

# =========== أمر مسح الأوامر القديمة ===========
@tree.command(name="مسح_الاوامر", description="❌ مسح جميع الأوامر القديمة")
async def clear_commands(interaction: Interaction):
    store = get_store(interaction.guild.id)
    if not store or store["owner_id"] != interaction.user.id:
        await interaction.response.send_message("🚫 فقط مالك المتجر يمكنه استخدام هذا الأمر.", ephemeral=True)
        return
    await tree.clear_commands(guild=interaction.guild)
    await tree.sync()
    await interaction.response.send_message("✅ تم مسح الأوامر بنجاح.", ephemeral=True)

# ======= تشغيل البوت =======
import discord
from discord.ext import commands
from keep_alive import keep_alive
import os

# تشغيل السيرفر الصغير (مهم عشان Render ما يطفي)
keep_alive()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")

@bot.command()
async def ping(ctx):
    await ctx.send("pong!")

# تشغيل البوت باستخدام التوكن من متغير البيئة
bot.run(os.getenv("TOKEN"))




