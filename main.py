import discord
from discord.ext import commands
import os
import io
import chat_exporter  # Не забудь добавить в requirements.txt

# === ТВОИ НАСТРОЙКИ ===
TICKET_CATEGORY_ID = 1479932038223106181
LOG_CHANNEL_ID = 1479933718834708480
ADMIN_ROLE_IDS = [
    1483162621719871559,
    1483162304710312056,
    1479933119338381404,
    1477586592754569276
]

GIF_URL = "https://media.discordapp.net/attachments/1483812220499398717/1491483610291634418/standard_6.gif"


class CloseTicketView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Закрыть тикет", style=discord.ButtonStyle.red, custom_id="close_ticket")
    async def close_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("⌛ Логи сохраняются, канал удаляется...", ephemeral=True)

        # Создание лога всей переписки
        transcript = await chat_exporter.export(interaction.channel)
        if transcript:
            file = discord.File(
                io.BytesIO(transcript.encode()),
                filename=f"ticket-{interaction.channel.name}.html"
            )
            log_channel = interaction.guild.get_channel(LOG_CHANNEL_ID)
            if log_channel:
                await log_channel.send(
                    f"📑 **Тикет закрыт**\n**Канал:** `{interaction.channel.name}`\n**Кто закрыл:** {interaction.user.mention}",
                    file=file
                )

        await interaction.channel.delete()


class TicketCreateView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Создать тикет", style=discord.ButtonStyle.primary, emoji="📩", custom_id="create_ticket")
    async def create_ticket(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        category = guild.get_channel(TICKET_CATEGORY_ID)

        # Настройка прав: автор видит, остальные (кроме админов) — нет
        overwrites = {
            guild.default_role: discord.PermissionOverwrite(read_messages=False),
            interaction.user: discord.PermissionOverwrite(read_messages=True, send_messages=True, attach_files=True)
        }

        # Выдаем права всем твоим ролям админов
        for role_id in ADMIN_ROLE_IDS:
            role = guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(read_messages=True, send_messages=True,
                                                               attach_files=True)

        channel = await guild.create_text_channel(
            name=f"ticket-{interaction.user.name}",
            category=category,
            overwrites=overwrites
        )

        await interaction.response.send_message(f"✅ Тикет создан: {channel.mention}", ephemeral=True)

        embed = discord.Embed(
            title="🎫 Поддержка",
            description=f"Привет {interaction.user.mention}! Опиши свою проблему, и администрация скоро ответит.",
            color=discord.Color.blue()
        )
        await channel.send(embed=embed, view=CloseTicketView())


class MyBot(commands.Bot):
    def __init__(self):
        # Включаем все интенты для работы с каналами и ролями
        intents = discord.Intents.all()
        super().__init__(command_prefix="!", intents=intents)

    async def setup_hook(self):
        # Регистрация кнопок, чтобы работали после перезагрузки
        self.add_view(TicketCreateView())
        self.add_view(CloseTicketView())

    async def on_ready(self):
        print(f"✅ Бот-тикет {self.user} запущен!")


bot = MyBot()


@bot.command()
@commands.has_permissions(administrator=True)
async def setup_tickets(ctx):
    """Отправляет сообщение с кнопкой создания тикета"""
    embed = discord.Embed(
        title="📩 Техническая поддержка",
        description="Нажмите на кнопку ниже, чтобы создать приватный тикет для связи с администрацией.",
        color=0x3498db
    )
    embed.set_image(url=GIF_URL)
    await ctx.send(embed=embed, view=TicketCreateView())


# Запуск бота через токен из переменных Railway
TOKEN = os.getenv("TOKEN")
bot.run(TOKEN)
