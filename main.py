import discord
from discord.ext import commands
import time
import os

TOKEN = os.getenv("TOKEN")

# 🔒 Приватный канал заявок
MOD_CHANNEL_ID = 1507380201057947678

# 📢 Публичный канал ивентов
PUBLIC_CHANNEL_ID = 1507340192455987261

# 🛡 Роль модераторов
MOD_ROLE_ID = 1507354160570306630

intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ⚡ GIF панели
MAIN_GIF = "https://media.discordapp.net/attachments/1490423692616798340/1507362248023347281/asgard_strong_lightning.gif"

# 🎮 Игры
GAMES = {
    "Minecraft": {
        "role": "MINECRAFT",
        "image": "https://media.discordapp.net/attachments/1493622297834033345/1507367751860359168/4253646a7db18fb2cf5ed8e4ba839c81.jpg"
    },

    "Dota": {
        "role": "DOTA",
        "image": "https://media.discordapp.net/attachments/1493622297834033345/1507369870340391072/d954079e9b49ecd72a2dfc352c832145.jpg"
    },

    "CS2": {
        "role": "CS2",
        "image": "https://media.discordapp.net/attachments/1493622297834033345/1507370541948866721/35f6591f1dadd090ace2a9d1e0bc30b6.jpg"
    },

    "Total War 2": {
        "role": "TOTAL WAR 2",
        "image": "https://media.discordapp.net/attachments/1493622297834033345/1507370716272525433/2834f46d7686bac5852cc7bedd2b0e36.jpg"
    },

    "GeoGuessr": {
        "role": "GEOGUESSR",
        "image": "https://media.discordapp.net/attachments/1493622297834033345/1507371973909680320/cc0349078784d702a3714dab56cf8b1f.jpg"
    }
}

user_data = {}

# ⏱ антиспам
cooldowns = {}
COOLDOWN = 120


# 🎮 Выбор игры
class GameSelect(discord.ui.Select):
    def __init__(self):

        options = [
            discord.SelectOption(label=game)
            for game in GAMES.keys()
        ]

        super().__init__(
            placeholder="🎮 Выбери игру",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        user_data.setdefault(interaction.user.id, {})
        user_data[interaction.user.id]["game"] = self.values[0]

        await interaction.response.send_message(
            f"✔ Выбрано: {self.values[0]}",
            ephemeral=True
        )


# 🔊 Выбор войса
class VoiceSelect(discord.ui.Select):
    def __init__(self, bot):

        options = []

        for channel in bot.get_all_channels():

            if isinstance(channel, discord.VoiceChannel):

                options.append(
                    discord.SelectOption(
                        label=channel.name,
                        value=str(channel.id)
                    )
                )

        options = options[:25]

        super().__init__(
            placeholder="🔊 Выбери войс",
            options=options
        )

    async def callback(self, interaction: discord.Interaction):

        user_data.setdefault(interaction.user.id, {})
        user_data[interaction.user.id]["voice"] = self.values[0]

        await interaction.response.send_message(
            "✔ Войс выбран",
            ephemeral=True
        )


# 📘 Панель
class MainPanel(discord.ui.View):
    def __init__(self, bot):
        super().__init__(timeout=None)

        self.add_item(GameSelect())
        self.add_item(VoiceSelect(bot))

    @discord.ui.button(
        label="Создать ивент",
        style=discord.ButtonStyle.success
    )
    async def create(self, interaction, button):

        await interaction.response.send_modal(
            EventModal()
        )


# 📝 Модалка
class EventModal(discord.ui.Modal, title="Создание ивента"):

    time_input = discord.ui.TextInput(
        label="⏰ Время"
    )

    desc_input = discord.ui.TextInput(
        label="📝 Описание",
        style=discord.TextStyle.paragraph
    )

    async def on_submit(self, interaction: discord.Interaction):

        now = time.time()

        # ⏱ антиспам
        if interaction.user.id in cooldowns:

            if now - cooldowns[interaction.user.id] < COOLDOWN:

                return await interaction.response.send_message(
                    "❌ Подожди перед новой заявкой",
                    ephemeral=True
                )

        cooldowns[interaction.user.id] = now

        data = user_data.get(interaction.user.id)

        if not data:
            return await interaction.response.send_message(
                "❌ Выбери игру и войс",
                ephemeral=True
            )

        if "game" not in data or "voice" not in data:
            return await interaction.response.send_message(
                "❌ Выбери игру и войс",
                ephemeral=True
            )

        game = data["game"]
        voice = data["voice"]

        game_data = GAMES[game]

        embed = discord.Embed(
            title=f"🎮 {game} — ЗАЯВКА",
            description=(
                f"⏰ {self.time_input.value}\n"
                f"📝 {self.desc_input.value}\n"
                f"🔊 <#{voice}>"
            ),
            color=discord.Color.orange()
        )

        # 🎮 картинка игры
        embed.set_image(url=game_data["image"])

        mod_channel = bot.get_channel(MOD_CHANNEL_ID)

        await mod_channel.send(
            embed=embed,
            view=ApproveView(
                game,
                voice,
                self.time_input.value,
                self.desc_input.value
            )
        )

        await interaction.response.send_message(
            "✔ Заявка отправлена модерации",
            ephemeral=True
        )


# 🧠 Модерация
class ApproveView(discord.ui.View):

    def __init__(self, game, voice, time_text, desc_text):
        super().__init__(timeout=None)

        self.game = game
        self.voice = voice
        self.time_text = time_text
        self.desc_text = desc_text

        self.done = False

    @discord.ui.button(
        label="Одобрить",
        style=discord.ButtonStyle.success
    )
    async def approve(self, interaction, button):

        # 🔒 уже обработано
        if self.done:
            return await interaction.response.send_message(
                "❌ Уже обработано",
                ephemeral=True
            )

        # 🔒 проверка прав
        if not any(r.id == MOD_ROLE_ID for r in interaction.user.roles):

            return await interaction.response.send_message(
                "❌ Нет прав",
                ephemeral=True
            )

        self.done = True

        game_data = GAMES[self.game]

        role = discord.utils.get(
            interaction.guild.roles,
            name=game_data["role"]
        )

        embed = discord.Embed(
            title=f"🎮 {self.game} ИВЕНТ",
            description=(
                f"⏰ {self.time_text}\n"
                f"📝 {self.desc_text}\n"
                f"🔊 <#{self.voice}>"
            ),
            color=discord.Color.green()
        )

        embed.set_image(url=game_data["image"])

        public_channel = bot.get_channel(PUBLIC_CHANNEL_ID)

        await public_channel.send(
            content=f"{role.mention if role else self.game}",
            embed=embed,
            view=JoinView()
        )

        # 🧹 удаляем заявку
        await interaction.message.delete()

        await interaction.response.send_message(
            "✔ Ивент опубликован",
            ephemeral=True
        )

    @discord.ui.button(
        label="Отклонить",
        style=discord.ButtonStyle.danger
    )
    async def deny(self, interaction, button):

        if self.done:
            return await interaction.response.send_message(
                "❌ Уже обработано",
                ephemeral=True
            )

        if not any(r.id == MOD_ROLE_ID for r in interaction.user.roles):

            return await interaction.response.send_message(
                "❌ Нет прав",
                ephemeral=True
            )

        self.done = True

        await interaction.message.delete()

        await interaction.response.send_message(
            "❌ Заявка отклонена",
            ephemeral=True
        )


# 🔥 Join кнопка
class JoinView(discord.ui.View):

    @discord.ui.button(
        label="Присоединиться",
        style=discord.ButtonStyle.success
    )
    async def join(self, interaction, button):

        await interaction.response.send_message(
            "👍 Ты присоединился",
            ephemeral=True
        )


# 🚀 Запуск
@bot.event
async def on_ready():

    print(f"Бот запущен: {bot.user}")

    channel = bot.get_channel(PUBLIC_CHANNEL_ID)

    # 🧹 удаляем старую панель
    async for message in channel.history(limit=20):

        if message.author == bot.user:

            if message.embeds:

                embed = message.embeds[0]

                if embed.title == "📘 Ивенты":

                    await message.delete()

    # 📘 новая панель
    embed = discord.Embed(
        title="📘 Ивенты",
        description="Выбери игру → войс → создай ивент",
        color=discord.Color.blurple()
    )

    embed.set_image(url=MAIN_GIF)

    await channel.send(
        embed=embed,
        view=MainPanel(bot)
    )


bot.run(TOKEN)
