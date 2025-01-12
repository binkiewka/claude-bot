import discord
from discord.ext import commands
from app.utils.permissions import is_admin_or_bot_owner, global_error_handler

class AdminCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(name="ping")
    @global_error_handler
    async def ping(self, ctx):
        latency = round(self.bot.latency * 1000, 2)
        await ctx.send(f"🏓 Pong! Latency: {latency}ms")

    @commands.command(name="status")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def status(self, ctx):
        stats = self.bot.analytics_service.get_stats()
        guild_id = ctx.guild.id
        
        embed = discord.Embed(
            title=f"🤖 Claude Bot Status - {ctx.guild.name}",
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Uptime", value=stats['uptime'], inline=True)
        
        guild_channels = [channel.id for channel in ctx.guild.channels]
        guild_mentions = sum(1 for mention in stats['most_active_channels'] 
                        if mention[0] in guild_channels)
        
        embed.add_field(name="Server Interactions", value=guild_mentions, inline=True)
        
        guild_response_times = {
            channel_id: time for channel_id, time 
            in stats['avg_response_times'].items()
            if channel_id in guild_channels
        }
        
        if guild_response_times:
            avg_times = []
            for channel_id, avg_time in guild_response_times.items():
                channel = self.bot.get_channel(channel_id)
                if channel:
                    avg_times.append(f"{channel.mention}: {avg_time:.2f}s")
            
            if avg_times:
                embed.add_field(
                    name="Response Times",
                    value="\n".join(avg_times),
                    inline=False
                )

        current_role = self.bot.claude_service.role_config.get_server_role(str(ctx.guild.id))
        embed.add_field(name="Current AI Role", value=current_role, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="setrole")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def set_role(self, ctx, role_name: str):
        """Set the AI role for responses in this server"""
        if self.bot.claude_service.role_config.set_server_role(str(ctx.guild.id), role_name):
            await ctx.send(f"AI role for this server set to: {role_name}")
        else:
            available_roles = ", ".join(self.bot.claude_service.role_config.roles.keys())
            await ctx.send(f"Invalid role. Available roles: {available_roles}")

    @commands.command(name="getrole")
    @commands.check(is_admin_or_bot_owner())
    @global_error_handler
    async def get_role(self, ctx):
        """Get the current AI role for this server"""
        current_role = self.bot.claude_service.role_config.get_server_role(str(ctx.guild.id))
        await ctx.send(f"Current AI role for this server: {current_role}")

    @commands.command(name="listroles")
    @global_error_handler
    async def list_roles(self, ctx):
        """List available AI roles"""
        roles = self.bot.claude_service.role_config.roles
        embed = discord.Embed(
            title="Available AI Roles",
            color=discord.Color.blue()
        )
        for role, prompt in roles.items():
            preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
            embed.add_field(
                name=role,
                value=preview,
                inline=False
            )
        await ctx.send(embed=embed)

    @commands.command(name="admin_status")
    @is_admin_or_bot_owner()
    @global_error_handler
    async def admin_status(self, ctx):
        """Display detailed bot admin status"""
        config = self.bot.config.get_safe_config()
        
        embed = discord.Embed(
            title="🤖 Claude Bot Admin Status", 
            color=discord.Color.blue()
        )
        
        embed.add_field(name="Allowed Guilds", value=len(config['allowed_guilds']), inline=True)
        embed.add_field(name="Bot Owners", value=len(config['bot_owners']), inline=True)
        embed.add_field(name="Rate Limit", value=f"{config['max_messages_per_minute']} msg/min", inline=True)
        embed.add_field(name="Total Servers", value=len(self.bot.guilds), inline=True)
        embed.add_field(name="Total Users", value=sum(guild.member_count for guild in self.bot.guilds), inline=True)
        embed.add_field(name="Current AI Role", value=self.bot.claude_service.role_config.get_server_role(str(ctx.guild.id)), inline=True)
        
        error_rate = self.bot.analytics_service.get_stats()['error_rate']
        embed.add_field(name="Error Rate", value=error_rate, inline=True)
        
        await ctx.send(embed=embed)

    @commands.command(name="setchan")
    @is_admin_or_bot_owner()
    @global_error_handler
    async def set_channel(self, ctx, channel: discord.TextChannel = None):
        """Set allowed channel for bot responses"""
        channel = channel or ctx.channel
        self.bot.allowed_channels[str(ctx.guild.id)] = channel.id
        await self.bot.save_allowed_channels()
        await ctx.send(f"Bot will now respond in {channel.mention}")

    @commands.command(name="clearchan")
    @is_admin_or_bot_owner()
    @global_error_handler
    async def clear_channel(self, ctx):
        """Clear channel restrictions for this server"""
        if str(ctx.guild.id) in self.bot.allowed_channels:
            del self.bot.allowed_channels[str(ctx.guild.id)]
        await self.bot.save_allowed_channels()
        await ctx.send("Bot will now respond in all channels of this server.")

    @commands.command(name="listchannels")
    @is_admin_or_bot_owner()
    @global_error_handler
    async def list_channels(self, ctx):
        """List all channels where bot is allowed to respond"""
        if not self.bot.allowed_channels:
            await ctx.send("No channels are currently set as allowed.")
            return

        embed = discord.Embed(
            title="🔒 Allowed Channels", 
            color=discord.Color.blue()
        )

        for guild_id, channel_id in self.bot.allowed_channels.items():
            guild = self.bot.get_guild(int(guild_id))
            channel = guild.get_channel(channel_id) if guild else None
            
            if channel:
                embed.add_field(
                    name=f"Guild: {guild.name}", 
                    value=f"Channel: {channel.mention}", 
                    inline=False
                )

        await ctx.send(embed=embed)

async def setup(bot):
    await bot.add_cog(AdminCog(bot))
