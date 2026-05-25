import discord
from discord.ext import commands
from discord import app_commands
import random
import time
import json
import os
import ollama
import config

# НАСТРОЙКА БОТА
TOKEN = config.TOKEN
YOUR_GUILD_ID = 1280747209247428693

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)
ai_client = ollama

DB_FILE = "database.json"
users_data = {}

AI_PERSONALITY = (
    "Ты — личный ИИ-помощник Кокосовой Империи в Дискорде. "
    "Твой создатель и хозяин — Kseosn, он парень. Обращайся к нему уважительно и в мужском роде! "
    "Ты обожаешь кокосы, фермы, плантации и тему тропиков. "
    "Общайся дружелюбно, с юмором, иногда используй тему кокосов и РП-атмосферу сервера. "
    "Отвечай строго на русском языке, коротко и по делу, не пиши огромные тексты."
)

def load_data():
    global users_data
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                users_data = json.load(f)
                users_data = {int(k): v for k, v in users_data.items()}
            print("--- База данных кокосов и памяти ИИ успешно загружена! ---")
        except Exception as e:
            print(f"Ошибка при чтении базы данных: {e}")
            users_data = {}
    else:
        users_data = {}

def save_data():
    try:
        with open(DB_FILE, "w", encoding="utf-8") as f:
            json.dump(users_data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Ошибка при сохранении базы данных: {e}")

def update_passive_income(user_id):
    if user_id not in users_data:
        users_data[user_id] = {
            "баланс": 0, "пальма": 0, "завод": 0, "корпорация": 0, 
            "prestige": 0, "marriage": None, "duels_won": 0, "время_сбора": time.time(), "history": []
        }
        save_data()
        return

    data = users_data[user_id]
    if "history" not in data: data["history"] = []
    if "prestige" not in data: data["prestige"] = 0
    if "marriage" not in data: data["marriage"] = None
    if "duels_won" not in data: data["duels_won"] = 0
        
    tekucee_vremya = time.time()
    if "время_сбора" not in data: data["время_сбора"] = tekucee_vremya
    proslo_secund = tekucee_vremya - data["время_сбора"]
    
    if proslo_secund > 0:
        base_income_per_hour = (
            data.get("пальма", 0) * SHOP_ITEMS["пальма"]["income_per_hour"] +
            data.get("завод", 0) * SHOP_ITEMS["завод"]["income_per_hour"] +
            data.get("корпорация", 0) * SHOP_ITEMS["корпорация"]["income_per_hour"]
        )
        multiplier = 1 + data["prestige"]
        total_income_per_second = (base_income_per_hour / 3600) * multiplier
        zarabotano = proslo_secund * total_income_per_second
        data["баланс"] = round(data["баланс"] + zarabotano, 2)
        data["время_сбора"] = tekucee_vremya
        save_data()

SHOP_ITEMS = {
    "пальма": {"name": "🌴 Кокосовая Пальма", "price": 100, "income_per_hour": 67},
    "завод": {"name": "🏭 Перерабатывающий Завод", "price": 1000, "income_per_hour": 960},
    "корпорация": {"name": "🚀 Кокосовая Корпорация", "price": 10000, "income_per_hour": 12000}
}

class FarmShopView(discord.ui.View):
    def __init__(self, author):
        super().__init__(timeout=60)
        self.author = author

    async def buy_item(self, interaction: discord.Interaction, item_key: str):
        user_id = self.author.id
        update_passive_income(user_id)
        data = users_data[user_id]
        item = SHOP_ITEMS[item_key]
        
        if data["баланс"] < item["price"]:
            await interaction.response.send_message(f"❌ Тебе не хватает кокосов! {item['name']} стоит **{item['price']}** 🥥.", ephemeral=True)
            return
            
        data["баланс"] -= item["price"]
        data["пальма" if item_key == "пальма" else "завод" if item_key == "завод" else "корпорация"] += 1
        update_passive_income(user_id)
        save_data()
        
        embed = create_embed_profile(self.author, data)
        await interaction.response.edit_message(embed=embed, view=self)

    @discord.ui.button(label="Купить Пальму (100 🥥)", style=discord.ButtonStyle.blurple, emoji="🌴")
    async def buy_palm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy_item(interaction, "пальма")

    @discord.ui.button(label="Купить Завод (1000 🥥)", style=discord.ButtonStyle.green, emoji="🏭")
    async def buy_factory(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy_item(interaction, "завод")

    @discord.ui.button(label="Купить Корпорацию (10k 🥥)", style=discord.ButtonStyle.red, emoji="🚀")
    async def buy_corp(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.buy_item(interaction, "корпорация")

def create_embed_profile(author, data):
    multiplier = (1 + data["prestige"]) * 100
    partner = f"<@{data['marriage']}>" if data.get("marriage") else "Нет брака"
    embed = discord.Embed(title="🚜 Твоя Кокосовая Ферма", color=discord.Color.dark_orange())
    embed.description = (
        f"👤 Игрок: {author.mention}\n"
        f"🥥 Текущий Баланс: **{data['баланс']}** 🥥\n"
        f"🌟 Золотые Кокосы (Престиж): **{data['prestige']}** шт. (Доход: **{multiplier}%**)\n"
        f"💍 Семья: **{partner}**\n"
        f"⚔️ Выиграно дуэлей: **{data.get('duels_won', 0)}**\n\n"
        f"🌴 Пальм: **{data.get('пальма', 0)}** шт. (+{data.get('пальма', 0) * SHOP_ITEMS['пальма']['income_per_hour']} 🥥/час)\n"
        f"🏭 Заводов: **{data.get('завод', 0)}** шт. (+{data.get('завод', 0) * SHOP_ITEMS['завод']['income_per_hour']} 🥥/час)\n"
        f"🚀 Корпораций: **{data.get('корпорация', 0)}** шт. (+{data.get('корпорация', 0) * SHOP_ITEMS['корпорация']['income_per_hour']} 🥥/час)"
    )
    return embed

@bot.event
async def on_ready():
    load_data()
    try:
        guild = discord.Object(id=1280747209247428693)
        
        # Копируем свежие команды из вашего кода в дерево сервера
        bot.tree.copy_global_to(guild=guild)
        synced = await bot.tree.sync(guild=guild)
        
        print(f"--- Слэш-команды привязаны к серверу: {len(synced)} шт. ---")
    except Exception as e:
        print(f"Ошибка мгновенной синхронизации: {e}")
    print(f"--- Кокосовая Империя {bot.user.name} полностью готова! ---")

# --- ВРЕМЕННАЯ АДМИН-КОМАНДА ДЛЯ УДАЛЕНИЯ СТАРОЙ КОМАНДЫ ---
@bot.command(name="делейт")
async def delete_old_slot(ctx):
    # Жесткая проверка: команда сработает ТОЛЬКО для Императора kseosn
    if ctx.author.id != 921707952002453504:
        await ctx.send("❌ У вас нет прав Императора для этой команды!")
        return
        
    await ctx.send("⏳ Имперские маги стирают старую глобальную команду из памяти Дискорда...")
    try:
        # Удаляем именно 'слоты' из глобального кэша
        bot.tree.remove_command("слоты", guild=None)
        # Отправляем обновление в Discord
        await bot.tree.sync(guild=None)
        await ctx.send("✅ Старая глобальная команда `/слоты` успешно уничтожена!")
    except Exception as e:
        await ctx.send(f"❌ Ошибка при удалении: {e}")

# --- СЛЭШ-КОМАНДЫ (СКРЫТЫЕ) ---

@bot.tree.command(name="баланс", description="Показать твою кокосовую ферму скрытно")
async def slash_balance(interaction: discord.Interaction):
    user_id = interaction.user.id
    update_passive_income(user_id)
    data = users_data[user_id]
    embed = create_embed_profile(interaction.user, data)
    view = FarmShopView(interaction.user)
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="топ", description="Показать топ кокосовых магнатов сервера")
async def slash_top(interaction: discord.Interaction):
    for uid in users_data.keys():
        update_passive_income(uid)
    # ПОЧИНИЛИ СОРТИРОВКУ БАЗЫ ДАННЫХ
    sorted_users = sorted(users_data.items(), key=lambda x: (x[1].get("prestige", 0), x[1].get("баланс", 0)), reverse=True)
    embed = discord.Embed(title="🏆 ТОП КОКОСОВЫХ МАГНАТОВ СЕРВЕРА 🏆", color=discord.Color.gold())
    description_text = ""
    for index, (uid, data) in enumerate(sorted_users[:10], start=1):
        user_mention = f"<@{uid}>"
        prestige = data.get("prestige", 0)
        balance = data.get("баланс", 0)
        medal = "🥇" if index == 1 else "🥈" if index == 2 else "🥉" if index == 3 else f"#{index}"
        description_text += f"{medal} {user_mention} — **{balance}** 🥥 | 🌟 **{prestige}** Золотых\n"
    if not description_text:
        description_text = "Плантации пока пустуют, лидеров нет!"
    embed.description = description_text
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="рулетка", description="Ставка на рулетку (красное, черное, зеро) (скрытно)")
@app_commands.choices(выбор=[
    app_commands.Choice(name="🔴 Красное (Множитель x2)", value="красное"),
    app_commands.Choice(name="⚫ Черное (Множитель x2)", value="черное"),
    app_commands.Choice(name="🟢 Зеро (Множитель x35)", value="зеро")
])
# ПОЧИНИЛИ: ВЕРНУЛИ СЛОВО ASYNC
async def slash_roulette(interaction: discord.Interaction, выбор: app_commands.Choice[str], ставка: float):
    user_id = interaction.user.id
    update_passive_income(user_id)
    data = users_data[user_id]
    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка должна быть больше 0!", ephemeral=True)
        return
    if data["баланс"] < ставка:
        await interaction.response.send_message(f"❌ Не хватает кокосов! Баланс: **{data['баланс']}** 🥥", ephemeral=True)
        return

    data["баланс"] -= ставка
    spin_result = random.randint(0, 36)
    
    if spin_result == 0: color_result = "зеро"
    elif spin_result % 2 == 0: color_result = "черное"
    else: color_result = "красное"

    color_emoji = "🟢" if color_result == "зеро" else "⚫" if color_result == "черное" else "🔴"

    if выбор.value == color_result:
        mult = 35 if color_result == "зеро" else 2
        win_amount = round(ставка * mult, 2)
        data["баланс"] = round(data["баланс"] + win_amount, 2)
        msg = f"🎡 Выпало: {color_emoji} **{spin_result} ({color_result})**!\n\n🎉 Угадал! Ты забираешь **{win_amount}** 🥥!"
    else:
        msg = f"🎡 Выпало: {color_emoji} **{spin_result} ({color_result})**!\n\n😭 Не угадал. Минус **{ставка}** 🥥."

    save_data()
    await interaction.response.send_message(msg, ephemeral=True)

# --- ТЕКСТОВЫЕ КОМАНДЫ (ОТКРЫТЫЕ, С АВТОУДАЛЕНИЕМ ЧЕРЕЗ 30 СЕК) ---

@commands.cooldown(1, 300, commands.BucketType.user)
@bot.command(aliases=["лутать", "кокос", "мешочек", "Baq"])
async def мешок(ctx):
    user_id = ctx.author.id
    update_passive_income(user_id)
    found_cocos = random.randint(10, 50)
    users_data[user_id]["баланс"] += found_cocos
    save_data()
    try: await ctx.message.delete()
    except: pass
    await ctx.send(f"🥥 {ctx.author.mention}, ты нашел мешок! Внутри оказалось **{found_cocos}** кокосов!", delete_after=30)

@bot.command(aliases=["престиж", "reset"])
async def перерождение(ctx):
    user_id = ctx.author.id
    update_passive_income(user_id)
    try: 
        await ctx.message.delete()
    except: 
        pass
    
    data = users_data[user_id]
    
    # --- ДИНАМИЧЕСКАЯ СТОИМОСТЬ ПРЕСТИЖА ---
    current_prestige = data.get("prestige", 0)
    
    # Стартовая цена 150 000 кокосов, каждый следующий престиж дороже в 5 раз
    required_cocos = int(150000 * (5 ** current_prestige))
    # ----------------------------------------

    if data["баланс"] < required_cocos:
        await ctx.send(f"❌ {ctx.author.mention}, нужно накопить как минимум **{required_cocos}** 🥥. Твой баланс: **{data['баланс']}**")
        return
        
    data["prestige"] += 1
    data["баланс"] = 0
    data["пальма"] = 0
    data["завод"] = 0
    data["корпорация"] = 0
    data["время_сбора"] = time.time()
    save_data()
    
    await ctx.send(f"⭐ **ВЕЛИКОЕ ПЕРЕРОЖДЕНИЕ!** ⭐ \n✨ {ctx.author.mention} получил **+1 Золотой Кокос** 🌟! Весь доход увеличен навсегда!")


    @discord.ui.button(label="Согласен(а) 💍", style=discord.ButtonStyle.green)
    async def accept(self, interaction: discord.Interaction, button: discord.ui.Button):
        if interaction.user.id != self.target.id:
            await interaction.response.send_message("❌ Это предложение сделано не тебе!", ephemeral=True)
            return
        users_data[self.proposer.id]["marriage"] = self.target.id
        users_data[self.target.id]["marriage"] = self.proposer.id
        save_data()
        await interaction.response.edit_message(content=f"💖 **ОФИЦИАЛЬНЫЙ БРАК!** {self.proposer.mention} и {self.target.mention} теперь женаты! 🎉💍", view=None)

@bot.command()
async def брак(ctx, member: discord.Member):
    user_id = ctx.author.id
    update_passive_income(user_id)
    update_passive_income(member.id)
    
    if member.id == user_id:
        await ctx.send("❌ Нельзя жениться на самом себе!", delete_after=10)
        return
    if users_data[user_id]["marriage"] or users_data[member.id]["marriage"]:
        await ctx.send("❌ Кто-то из вас уже состоит в браке!", delete_after=10)
        return

    view = MarriageView(ctx.author, member)
    await ctx.send(f"💍 {member.mention}, пользователь {ctx.author.mention} делает тебе предложение руки и кокоса! Ты согласен?", view=view, delete_after=60)

@bot.command()
async def развод(ctx):
    user_id = ctx.author.id
    update_passive_income(user_id)
    partner_id = users_data[user_id]["marriage"]
    if not partner_id:
        await ctx.send("❌ Ты и так не в браке!", delete_after=10)
        return
    users_data[user_id]["marriage"] = None
    if partner_id in users_data: users_data[partner_id]["marriage"] = None
    save_data()
    await ctx.send(f"💔 {ctx.author.mention} разорвал брак. Свободный кокос одиночества!", delete_after=30)

@bot.command()
async def кусь(ctx, member: discord.Member):
    try: await ctx.message.delete()
    except: pass
    await ctx.send(f"🥥 {ctx.author.mention} **сделал кусь за бочок** {member.mention}! 🦷", delete_after=30)

# КОМАНДА: ПОСМОТРЕТЬ ЧУЖОЙ ИЛИ СВОЙ ПРОФИЛЬ В ОТКРЫТОМ ЧАТЕ
@bot.command(aliases=["проф", "стата"])
async def профиль(ctx, member: discord.Member = None):
    # Если ты не тегнул никого (!профиль), бот покажет тебя самого
    if member is None:
        member = ctx.author
        
    user_id = member.id
    update_passive_income(user_id) # Начисляем доход игроку перед проверкой
    data = users_data[user_id]
    
    # Сразу удаляем текстовую команду от пользователя для чистоты
    try:
        await ctx.message.delete()
    except:
        pass
        
    # Вытаскиваем инфу о браке, дуэлях и постройках
    partner = f"<@{data.get('marriage')}>" if data.get("marriage") else "Нет брака"
    multiplier = (1 + data.get("prestige", 0)) * 100
    
    # Создаем красивую карточку, которую УВИДЯТ ВСЕ на сервере
    embed = discord.Embed(title=f"📈 Досье плантатора: {member.name}", color=discord.Color.green())
    embed.description = (
        f"👤 Игрок: {member.mention}\n"
        f"🥥 Баланс: **{data['баланс']}** 🥥\n"
        f"🌟 Золотые Кокосы: **{data.get('prestige', 0)}** шт. (Доход: **{multiplier}%**)\n"
        f"💍 Семья: **{partner}**\n"
        f"⚔️ Выиграно дуэлей: **{data.get('duels_won', 0)}**\n\n"
        f"🌴 Пальм: **{data.get('пальма', 0)}** шт.\n"
        f"🏭 Заводов: **{data.get('завод', 0)}** шт.\n"
        f"🚀 Корпораций: **{data.get('корпорация', 0)}** шт."
    )
    
    # Карточка повисит 30 секунд, чтобы все оценили богатство игрока, и удалится
    await ctx.send(embed=embed, delete_after=30)


@bot.command()
async def обнять(ctx, member: discord.Member):
    try: await ctx.message.delete()
    except: pass
    await ctx.send(f"🥥 {ctx.author.mention} **крепко обнял** {member.mention}! 🤗", delete_after=30)

@bot.command()
async def дуэль(ctx, member: discord.Member, ставка: float):
    user_id = ctx.author.id
    update_passive_income(user_id)
    update_passive_income(member.id)

    if member.id == user_id:
        await ctx.send("❌ Нельзя вызвать на дуэль самого себя!", delete_after=10)
        return
    if ставка <= 0:
        await ctx.send("❌ Ставка должна быть больше 0!", delete_after=10)
        return
    if users_data[user_id]["баланс"] < ставка:
        await ctx.send("❌ У тебя не хватает кокосов для такой ставки!", delete_after=10)
        return
    if users_data[member.id]["баланс"] < ставка:
        await ctx.send("❌ У твоего оппонента маловато кокосов для дуэли!", delete_after=10)
        return

    class DuelView(discord.ui.View):
        def __init__(self): super().__init__(timeout=60)
        @discord.ui.button(label="Принять вызов ⚔️", style=discord.ButtonStyle.danger)
        async def accept_duel(self, interaction: discord.Interaction, button: discord.ui.Button):
            if interaction.user.id != member.id:
                await interaction.response.send_message("❌ Этот вызов брошен не тебе!", ephemeral=True)
                return
            if users_data[user_id]["баланс"] < ставка or users_data[member.id]["баланс"] < ставка:
                await interaction.response.edit_message(content="❌ Дуэль отменена, у кого-то кончились кокосы!", view=None)
                return

            winner = random.choice([ctx.author, member])
            loser = member if winner == ctx.author else ctx.author

            users_data[winner.id]["баланс"] = round(users_data[winner.id]["баланс"] + ставка, 2)
            users_data[loser.id]["баланс"] = round(users_data[loser.id]["баланс"] - ставка, 2)
            users_data[winner.id]["duels_won"] += 1
            save_data()

            await interaction.response.edit_message(
                content=f"⚔️ **ДУЭЛЬ СОСТОЯЛАСЬ!** ⚔️\n💀 {winner.mention} победил в жесткой схватке и забирает **{ставка}** 🥥 у {loser.mention}!", 
                view=None
            )

    await ctx.send(f"⚔️ {member.mention}, пользователь {ctx.author.mention} вызывает тебя на кокосовую дуэль! Ставка: **{ставка}** 🥥. Примешь бой?", view=DuelView(), delete_after=60)

@bot.command()
async def гпт(ctx, *, question: str):
    user_id = ctx.author.id
    update_passive_income(user_id)
    data = users_data[user_id]
    async with ctx.typing():
        try:
            messages_to_send = [{"role": "system", "content": AI_PERSONALITY}]
            for msg in data["history"]: messages_to_send.append(msg)
            messages_to_send.append({"role": "user", "content": question})
            response = ai_client.chat(model="llama3", messages=messages_to_send)
            answer = response["message"]["content"]
            data["history"].append({"role": "user", "content": question})
            data["history"].append({"role": "assistant", "content": answer})
            if len(data["history"]) > 12: data["history"] = data["history"][-12:]
            save_data()
            await ctx.send(f"🥥 **Ответ локального ИИ для {ctx.author.mention}:**\n\n{answer}")
        except Exception as e:
            await ctx.send("❌ Прости, ИИ сейчас задумался. Попробуй еще раз!", delete_after=10)
            print(f"Ошибка локального ИИ: {e}")

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandOnCooldown):
        try: await ctx.message.delete()
        except: pass
        seconds = round(error.retry_after)
        await ctx.send(f"⏱️ {ctx.author.mention}, кокосы еще не созрели! Подожди еще **{seconds}** сек.", delete_after=10)

# --- КОМАНДА: УГОЛОВНАЯ СТАТЬЯ В СТИЛЕ ИРИСА ---
@bot.command(name="статья")
async def generate_article(ctx, target: discord.Member = None):
    # Если никто не тегнут, обвиняем того, кто вызвал команду
    if target is None:
        target = ctx.author
        
    user_id = ctx.author.id
    
    if user_id not in users_data:
        users_data[user_id] = {
            "баланс": 0, "prestige": 0, "пальма": 0, "завод": 0, "корпорация": 0,
            "время_сбора": time.time(), "последняя_статья": 0
        }
    
    data = users_data[user_id]
    current_time = time.time()
    last_article_time = data.get("последняя_статья", 0)
    cooldown = 86400
    
    if current_time - last_article_time < cooldown:
        time_left = int(cooldown - (current_time - last_article_time))
        hours = time_left // 3600
        minutes = (time_left % 3600) // 60
        await ctx.send(f"🥥 {ctx.author.mention}, имперские судьи еще отдыхают! Новое дело можно завести через **{hours} ч. {minutes} мин.**")
        return

    loading_msg = await ctx.send("🥥 *Имперский суд рассматривает личное дело, подождите...*")
    
    try:
        # Промпт для генерации обвинения в стиле Ириса
        prompt = (
            f"Придумай случайное шуточное уголовное обвинение для участника дискорд-сервера по имени {target.display_name}. "
            "Преступление НЕ должно быть связано с кокосами. Придумывай обычные, геймерские, бытовые или абсурдные криминальные статьи. "
            "Примеры тем: кража чужих пельменей из холодильника, спам глупыми мемами, игнорирование пингов, сидение в дискорде без трусов, "
            "уничтожение чужой базы в майнкрафте, токсичность в катке, кража аватарки, симулирование сна, поедание пиццы с ананасами.\n\n"
            "Строго сопоставляй тяжесть (cruelty) преступления:\n"
            "- Мелкие шалости (украл мем, пукнул в войсе, не ответил на смс): cruelty от 5 до 30.\n"
            "- Средние нарушения (токсичность, забанил друга, съел чужую еду): cruelty от 31 до 65.\n"
            "- Жесткий криминал / абсурдная жесть (уничтожение трупа, измена родине в Майнкрафте, продажа друзей в рабство цыганам): cruelty от 66 до 100.\n\n"
            "Ты должен ответить СТРОГО в формате JSON с двумя ключами:\n"
            "'text' (строка на русском языке, которая начинается со слова 'приговорен...' или 'обвиняется...'. "
            "Пример: 'приговорен к статье 228: Незаконное хранение аниме-картинок и совращение админа сервера.').\n"
            "'cruelty' (число от 0 до 100, соответствующее тяжести преступления).\n\n"
            "Ничего, кроме JSON, в ответе быть не должно. Не пиши никаких пояснений."
        )

        response = ollama.generate(
            model='llama3', 
            prompt=prompt,
            system=str(AI_PERSONALITY),
            format='json'
        )
        
        result = json.loads(response['response'])
        article_text = result.get("text", "приговорен к неизвестной статье...")
        cruelty_score = int(result.get("cruelty", 0))
        cruelty_score = max(0, min(100, cruelty_score))
        
        # Награда: чем тяжелее статья, тем больше кокосов (до 1000)
        reward = cruelty_score * 10
        
        data["баланс"] += reward
        data["последняя_статья"] = current_time
        save_data()
        
        # Строим Embed в стиле Ириса
        embed = discord.Embed(
            title="⚖️ СУДЕБНЫЙ ПРИГОВОР ИМПЕРИИ", 
            description=f"👤 **Обвиняемый:** {target.mention}\n\n📢 {target.display_name} {article_text}", 
            color=0x9B59B6 # Фиолетовый цвет суда
        )
        
        embed.add_field(
            name="😈 Тяжесть статьи", 
            value=f"`{cruelty_score} из 100`", 
            inline=True
        )
        embed.add_field(
            name="💰 Награда за поимку", 
            value=f"**+{reward}** 🥥", 
            inline=True
        )
        
        embed.set_footer(text=f"Судья: Император kseosn • Дело закрыто")
        
        await loading_msg.edit(content=None, embed=embed)
        
    except Exception as e:
        try:
            await loading_msg.edit(content=f"❌ Суд перенесен из-за ошибки: {e}")
        except:
            await ctx.send(f"❌ Суд перенесен из-за ошибки: {e}")

# --- КОМАНДА: ГРАБЕЖ (СЛУЧАЙНЫЙ ВЫБОР ЖЕРТВЫ ИЛИ ПО ПИНГУ) ---
@bot.command(aliases=["украсть", "steal", "rob"])
@commands.cooldown(1, 3600, commands.BucketType.user) # КД вора — 1 час
async def грабеж(ctx, target: discord.Member = None):
    user_id = ctx.author.id
    current_time = time.time()
    victim_cooldown = 86400 # 24 часа

    # Обновляем пассивный доход вора
    update_passive_income(user_id)
    
    if user_id not in users_data:
        users_data[user_id] = {
            "баланс": 0, "prestige": 0, "пальма": 0, "завод": 0, "корпорация": 0,
            "время_сбора": current_time, "последняя_статья": 0, "последний_грабеж": 0
        }

    thief_data = users_data[user_id]

    # Проверка: есть ли у самого вора 1000 кокосов на штраф
    if thief_data["баланс"] < 1000:
        ctx.command.reset_cooldown(ctx)
        await ctx.send(f"❌ {ctx.author.mention}, ты слишком беден для криминала! На твоем балансе должно быть хотя бы **1000** 🥥.")
        return

    # --- ЛОГИКА АВТОМАТИЧЕСКОГО ВЫБОРА ЖЕРТВЫ ---
    if target is None:
        # Ищем всех подходящих кандидатов из базы данных
        valid_victims = []
        for uid, udata in users_data.items():
            # Жертва не должна быть самим вором
            if int(uid) == user_id:
                continue
                
            # Обновляем доход кандидата перед проверкой баланса
            update_passive_income(int(uid))
            
            # Проверяем условия: баланс >= 1000 и КД на ограбление прошло
            if udata.get("баланс", 0) >= 1000 and (current_time - udata.get("последний_грабеж", 0) >= victim_cooldown):
                valid_victims.append(int(uid))
        
        # Если грабить некого
        if not valid_victims:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("🥥 В Империи затишье... Не удалось найти богатых игроков со слабой стражей для случайного ограбления.")
            return
            
        # Выбираем случайного ID из списка подходящих
        target_id = random.choice(valid_victims)
        target = ctx.guild.get_member(target_id)
        
        # Если пользователя нет на сервере, берем объект из кэша бота
        if target is None:
            try: target = await bot.fetch_user(target_id)
            except: pass

        if target is None:
            ctx.command.reset_cooldown(ctx)
            await ctx.send("❌ Произошла ошибка при поиске случайной жертвы. Попробуй еще раз.")
            return
    else:
        # Если жертву указали через пинг
        target_id = target.id
        
        if target_id == user_id:
            ctx.command.make_cooldown_invalid(ctx) # Наказание за глупость — КД не сбрасываем
            await ctx.send(f"🥥 {ctx.author.mention}, грабить самого себя? Имперские лекари уже едут за тобой...")
            return
            
        if target.bot:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ {ctx.author.mention}, у ботов нет кокосов, только микросхемы!")
            return
            
        update_passive_income(target_id)
        
        if target_id not in users_data:
            users_data[target_id] = {
                "баланс": 0, "prestige": 0, "пальма": 0, "завод": 0, "корпорация": 0,
                "время_сбора": current_time, "последняя_статья": 0, "последний_грабеж": 0
            }
            
        # Проверка КД при точечном налёте
        last_robbed_time = users_data[target_id].get("последний_грабеж", 0)
        if current_time - last_robbed_time < victim_cooldown:
            ctx.command.reset_cooldown(ctx)
            time_left = int(victim_cooldown - (current_time - last_robbed_time))
            hours = time_left // 3600
            minutes = (time_left % 3600) // 60
            await ctx.send(f"❌ На владения {target.mention} недавно уже нападали! Напасть можно через **{hours} ч. {minutes} мин.**")
            return

        if users_data[target_id]["баланс"] < 1000:
            ctx.command.reset_cooldown(ctx)
            await ctx.send(f"❌ У {target.display_name} меньше **1000** 🥥. Грабить бедняков запрещено!")
            return

    victim_data = users_data[target_id]
    outcome = random.choice([0, 1, 2])

    # 1. УСПЕШНОЕ ОГРАБЛЕНИЕ
    if outcome == 0:
        stolen_amount = random.randint(100, 1000)
        if victim_data["баланс"] < stolen_amount:
            stolen_amount = int(victim_data["баланс"])

        victim_data["баланс"] -= stolen_amount
        thief_data["баланс"] += stolen_amount
        victim_data["последний_грабеж"] = current_time
        save_data()

        embed = discord.Embed(
            title="🥷 УСПЕШНЫЙ НАЛЁТ!",
            description=f"⚔️ {ctx.author.mention} пробрался во владения к {target.mention} и утащил мешок, где было **{stolen_amount}** 🥥!",
            color=0x2ECC71
        )
        await ctx.send(embed=embed)

    # 2. НЕУДАЧА: ПОЙМАЛИ НА МЕСТЕ
    elif outcome == 1:
        fine = random.randint(200, 800)
        if thief_data["баланс"] < fine:
            fine = int(thief_data["баланс"])
            
        thief_data["баланс"] -= fine
        victim_data["баланс"] += fine
        save_data()

        embed = discord.Embed(
            title="🚨 ОГРАБЛЕНИЕ ПРОВАЛЕНО!",
            description=f"👮 {ctx.author.mention} был застигнут врасплох стражей {target.mention}!\n"
                        f"Налётчик выплачивает фиксированный штраф в размере **{fine}** 🥥 в пользу пострадавшего.",
            color=0xE74C3C
        )
        await ctx.send(embed=embed)

    # 3. НЕУДАЧА: ОБРОНИЛ КОКОСЫ ПРИ ПОБЕГЕ
    elif outcome == 2:
        dropped = random.randint(150, 600)
        if thief_data["баланс"] < dropped:
            dropped = int(thief_data["баланс"])
            
        thief_data["баланс"] -= dropped
        save_data()

        embed = discord.Embed(
            title="🏃💨 НЕУКЛЮЖИЙ ПОБЕГ!",
            description=f"😱 {ctx.author.mention} испугался диких шорохов на складе у {target.mention}!\n"
                        f"Убегая, он **обронил в глубокое болото {dropped}** 🥥 из своего кармана!",
            color=0xE67E22
        )
        await ctx.send(embed=embed)

# --- КАЗИНО: СЛОЖНЫЕ СБАЛАНСИРОВАННЫЕ СЛОТЫ ---
@bot.tree.command(name="барабан", description="🎰 Испытать удачу в имперских игровых автоматах!")
@app_commands.describe(ставка="Сколько кокосов ставишь?")
async def slash_slots(interaction: discord.Interaction, ставка: float):
    user_id = interaction.user.id
    update_passive_income(user_id)
    data = users_data[user_id]

    if ставка <= 0:
        await interaction.response.send_message("❌ Ставка должна быть больше 0!", ephemeral=True)
        return
    if data["баланс"] < ставка:
        await interaction.response.send_message(f"❌ Не хватает кокосов! Баланс: **{data['баланс']}** 🥥", ephemeral=True)
        return

    # Списываем ставку
    data["баланс"] -= ставка
    
    # МАТЕМАТИКА ХАРДКОРНОГО КАЗИНО
    emojis = [
        "🥥", 
        "🍉", "🍉", "🍉", 
        "🍌", "🍌", "🍌", "🍌", "🍌", 
        "🍒", "🍒", "🍒", "🍒", "🍒"
    ]
    
    slot1 = random.choice(emojis)
    slot2 = random.choice(emojis)
    slot3 = random.choice(emojis)
    
    win_multiplier = 0
    is_jackpot = False
    
    # 1. ПРОВЕРКА: ТРИ В РЯД (ДЖЕКПОТЫ)
    if slot1 == slot2 == slot3:
        is_jackpot = True
        if slot1 == "🥥":
            win_multiplier = 15     # 🥥 🥥 🥥 — Мега Кокосовый Джекпот (х15)
        else:
            win_multiplier = 5      # Любой другой три в ряд (х5)
            
    # 2. ПРОВЕРКА: ДВА В РЯД (УТЕШИТЕЛЬНЫЙ ПРИЗ)
    elif slot1 == slot2 or slot2 == slot3 or slot1 == slot3:
        if "🥥" in [slot1, slot2, slot3]:
            win_multiplier = 2.0    
        else:
            win_multiplier = 1.1    

    # Начисление баланса
    if win_multiplier > 0:
        win_amount = round(ставка * win_multiplier, 2)
        data["баланс"] = round(data["баланс"] + win_amount, 2)
    else:
        win_amount = 0
        data["баланс"] = round(data["баланс"], 2)

    save_data()

    # --- ДИЗАЙН EMBED-КАРТОЧЕК ---
    display_slots = f"【 {slot1} ┃ {slot2} ┃ {slot3} 】"

    if is_jackpot:
        # Золотой публичный Embed для джекпота
        embed = discord.Embed(
            title="💎 ВЕЛИКИЙ ДЖЕКПОТ КАЗИНО! 💎",
            description=f"👑 Игрок {interaction.user.mention} сорвал куш в игровом автомате!\n\n"
                        f"🎰 **БАРАБАНЫ:** `{display_slots}`\n\n"
                        f"💰 **Чистый выигрыш:** **+{win_amount}** 🥥 (Множитель х{win_multiplier})",
            color=0xF1C40F # Золотой цвет
        )
        embed.set_thumbnail(url="https://imgur.com") # Иконка джекпота (можно заменить)
        embed.set_footer(text="Это сообщение исчезнет через 30 секунд • Казна Империи")
        
        # Отвечаем игроку скрытно, чтобы подтвердить транзакцию
        await interaction.response.send_message(f"🏆 Поздравляем! Твой джекпот объявлен на весь сервер!", ephemeral=True)
        
        # Отправляем красивую карточку в общий канал и удаляем через 30 сек
        public_msg = await interaction.channel.send(embed=embed)
        await public_msg.delete(delay=30)
        
    else:
        # Скрытые карточки для обычных исходов
        if win_multiplier > 0:
            # Обычный выигрыш (Синий Embed)
            embed = discord.Embed(
                title="✨ Удача на барабанах! ✨",
                description=f"🎰 **РЕЗУЛЬТАТ:** `{display_slots}`\n\n"
                            f"💵 Вы вернули ставку и забрали **+{win_amount}** 🥥\n"
                            f"📈 Множитель комбинации: `х{win_multiplier}`",
                color=0x3498DB
            )
        else:
            # Проигрыш (Темно-серый/красноватый Embed)
            embed = discord.Embed(
                title="📉 Аппарат забирает монеты...",
                description=f"🎰 **РЕЗУЛЬТАТ:** `{display_slots}`\n\n"
                            f"Увы, комбинация пустая. Вы потеряли **-{ставка}** 🥥.\n"
                            f"*Фортуна обязательно улыбнется в следующий раз!*",
                color=0x2C2F33
            )
            
        embed.set_footer(text=f"Твой текущий баланс: {int(data['баланс'])} 🥥")
        await interaction.response.send_message(embed=embed, ephemeral=True)

bot.run(TOKEN)
