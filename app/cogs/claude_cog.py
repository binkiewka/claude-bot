import discord
from discord.ext import commands
from typing import Optional
from datetime import datetime

from app.utils.permissions import is_admin_or_bot_owner, global_error_handler

class ClaudeCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if self.bot.user in message.mentions:
            start_time = datetime.now()
            
            self.bot.analytics_service.add_mention(
                message.channel.id,
                str(message.author.id),
                message.clean_content
            )
            
            # Check if channel is allowed for this server
            server_id = str(message.guild.id)
            server_channels = self.bot.allowed_channels.get(server_id, [])
            
            if message.channel.id not in server_channels:
                self.bot.logger.info(f"Channel {message.channel.id} not in allowed channels for server {message.guild.id}")
                return

            async def process_message():
                async with message.channel.typing():
                    response = await self.bot.get_claude_response(
                        str(message.author.id),
                        message.clean_content,
                        message.channel.id,
                        str(message.guild.id)
                    )
                    
                    try:
                        shared_response = await self.bot.file_share_service.share_long_content(response)
                        await message.reply(shared_response)
                    except Exception as e:
                        self.bot.logger.error(f"Sharing error: {e}")
                        self.bot.analytics_service.add_error("sharing", str(e))
                        await message.reply(response[:250] + "...")
                    
                    end_time = datetime.now()
                    response_time = (end_time - start_time).total_seconds()
                    self.bot.analytics_service.add_response_time(message.channel.id, response_time)

            await self.bot.queue_service.add_task(message.channel.id, process_message)

    @commands.command(name="clear_context")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def clear_context(self, ctx):
        await self.bot.clear_conversation_context(ctx.channel.id)
        await ctx.send("Conversation context cleared.")

    @commands.command(name="allow_channel")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def allow_channel(self, ctx, channel: Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        server_id = str(ctx.guild.id)
        
        # Initialize server's allowed channels if not exists
        if server_id not in self.bot.allowed_channels:
            self.bot.allowed_channels[server_id] = []
        
        # Add channel to server's allowed channels if not already present
        if channel.id not in self.bot.allowed_channels[server_id]:
            self.bot.allowed_channels[server_id].append(channel.id)
            await self.bot.save_allowed_channels()
            await ctx.send(f"Claude will now respond in {channel.mention}")
        else:
            await ctx.send(f"Claude is already allowed in {channel.mention}")

    @commands.command(name="disallow_channel")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def disallow_channel(self, ctx, channel: Optional[discord.TextChannel] = None):
        channel = channel or ctx.channel
        server_id = str(ctx.guild.id)
        
        if server_id in self.bot.allowed_channels:
            if channel.id in self.bot.allowed_channels[server_id]:
                self.bot.allowed_channels[server_id].remove(channel.id)
                if not self.bot.allowed_channels[server_id]:  # If no channels left
                    del self.bot.allowed_channels[server_id]
                await self.bot.save_allowed_channels()
                await ctx.send(f"Claude will no longer respond in {channel.mention}")
            else:
                await ctx.send(f"Claude was not allowed in {channel.mention}")
        else:
            await ctx.send(f"No channels are configured for this server.")

    @commands.command(name="list_channels")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def list_channels(self, ctx):
        server_id = str(ctx.guild.id)
        if server_id not in self.bot.allowed_channels or not self.bot.allowed_channels[server_id]:
            await ctx.send("Claude is not allowed in any channels in this server.")
            return

        channel_mentions = []
        for channel_id in self.bot.allowed_channels[server_id]:
            channel = ctx.guild.get_channel(channel_id)
            if channel:
                channel_mentions.append(channel.mention)

        await ctx.send("Claude is allowed in these channels:\n" + "\n".join(channel_mentions))

    @commands.Cog.listener()
    async def on_guild_channel_delete(self, channel):
        server_id = str(channel.guild.id)
        if server_id in self.bot.allowed_channels:
            if channel.id in self.bot.allowed_channels[server_id]:
                self.bot.allowed_channels[server_id].remove(channel.id)
                if not self.bot.allowed_channels[server_id]:  # If no channels left
                    del self.bot.allowed_channels[server_id]
                await self.bot.save_allowed_channels()

    @commands.command(name="reset")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def reset_claude(self, ctx):
        await self.bot.clear_conversation_context(ctx.channel.id)
        # Also clear the role for this server
        server_id = str(ctx.guild.id)
        if server_id in self.bot.claude_service.role_config.server_roles:
            del self.bot.claude_service.role_config.server_roles[server_id]
        await ctx.send("Claude's conversation history, context, and role have been reset for this server.")

    @commands.command(name="claude_status")
    @global_error_handler
    async def claude_status(self, ctx):
        server_id = str(ctx.guild.id)
        channel_id = ctx.channel.id
        
        is_active = (server_id in self.bot.allowed_channels and 
                    channel_id in self.bot.allowed_channels[server_id])
        
        current_role = self.bot.claude_service.role_config.get_server_role(server_id)
        
        embed = discord.Embed(
            title="Claude Status",
            color=discord.Color.green() if is_active else discord.Color.red()
        )
        
        embed.add_field(
            name="Status", 
            value="Active" if is_active else "Inactive", 
            inline=True
        )
        embed.add_field(
            name="Current Role", 
            value=current_role, 
            inline=True
        )
        
        if server_id in self.bot.allowed_channels:
            allowed_channels = []
            for channel_id in self.bot.allowed_channels[server_id]:
                channel = ctx.guild.get_channel(channel_id)
                if channel:
                    allowed_channels.append(channel.mention)
            if allowed_channels:
                embed.add_field(
                    name="Allowed Channels",
                    value="\n".join(allowed_channels),
                    inline=False
                )
        
        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(ClaudeCog(bot))
