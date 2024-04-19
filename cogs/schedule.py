import io

import discord
import pytz
from discord.ext import commands
from discord import app_commands
import datetime
import config


class ScheduleShift(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

    @app_commands.command(name='schedule', description="Schedules a shift.")
    @app_commands.describe(title="Title of the shift",
                           date_time="Example: Day.Month.Year Hours:Minutes, (UTC)"
                                    'Example: "**24.12.2023 23:56**"',
                           duration="Shift duration (in minutes)",
                           description='Description for the shift. You **can** use markdown and emojis here.',
                           ping_everyone="Should the bot ping @everyone?", map='Example: MLV6', )
    async def schedule(self, interaction: discord.Interaction, title: str, date_time: str, duration: int = 150, description: str = "",
                       ping_everyone: bool = False, map: str = "MLV6"):

        user = interaction.user
        guild = interaction.guild
        channel = guild.get_channel(config.ANNOUNCEMENTS_CHANNEL_ID)

        # Minimum role / Permissions check
        minimum_role = guild.get_role(config.MINIMUM_ADMIN_ROLE_ID)
        if user.top_role.position < minimum_role.position:
            await interaction.response.send_message(ephemeral=True,
                                                    content="❌ Unfortunately you cannot use this command.")
            return

        # Datetime conversion
        if interaction.user.guild_permissions.administrator:
            formats = ["%d.%m.%Y %H:%M", "%d-%m-%Y %H:%M", "%d/%m/%Y %H:%M"]
            for fmt in formats:
                try:
                    datetime_obj = datetime.datetime.strptime(date_time, fmt)
                    break
                except ValueError:
                    pass
            else:
                await interaction.response.send_message("❌ Invalid date/time format",
                                                        ephemeral=True)
                return

            try:
                timezone_obj = pytz.timezone("Europe/Berlin")
            except pytz.UnknownTimeZoneError:
                await interaction.response.send_message("❌ Invalid time zone.\nList of all valid timezones: "
                                                        "https://en.wikipedia.org/wiki/List_of_tz_database_time_zones",
                                                        ephemeral=True)
                return

        # Convert datetime_obj to UTC time
        datetime_obj = timezone_obj.localize(datetime_obj)
        datetime_obj_end = datetime_obj + datetime.timedelta(minutes=duration)

        embed = discord.Embed(
            title=f"**New shift: {title}**",
            description=description,
            colour=discord.Colour.green()
        )
        embed.set_thumbnail(url=interaction.guild.icon)
        embed.add_field(
            name="**Date & Time:**",
            value=f'<t:{int(datetime.datetime.timestamp(datetime_obj))}>',
            inline=False,
        )
        embed.add_field(
            name="**Map:**",
            value=map,
            inline=False,
        )

        # Send a shift announcement
        if ping_everyone:
            await channel.send(embed=embed, content="@everyone")
        else:
            await channel.send(embed=embed)

        # Convert the background image to bytes
        with open("zsskimage.png", "rb") as image:
            f = image.read()
            b = bytearray(f)

            # Schedule a discord event
            await interaction.guild.create_scheduled_event(name=title, start_time=datetime_obj, end_time=datetime_obj_end,
                                                           description=description, location=map,
                                                           entity_type=discord.EntityType.external,
                                                           privacy_level=discord.PrivacyLevel.guild_only,
                                                           image=b)

            await interaction.response.send_message("✅ Shift successfully scheduled!")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(ScheduleShift(client))
