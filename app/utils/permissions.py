from functools import wraps
from typing import Callable, Any
from discord.ext import commands
import traceback
import discord
from app.database.models import ServerRole

def is_admin_or_bot_owner():
    """
    Check if the user is a bot owner or has administrator permissions in the guild.
    This is a command check decorator.
    
    Returns:
        commands.check: A command check that validates admin/owner status
    """
    async def predicate(ctx: commands.Context) -> bool:
        # Check if user is bot owner
        if await ctx.bot.is_owner(ctx.author):
            return True
        
        # Check if user has admin permissions in a guild
        if ctx.guild and ctx.author.guild_permissions.administrator:
            return True
            
        # If neither condition is met, deny permission
        return False
    
    return commands.check(predicate)

def global_error_handler(func: Callable) -> Callable:
    """
    A decorator that wraps commands to handle errors globally.
    
    Args:
        func (Callable): The command function to wrap
        
    Returns:
        Callable: The wrapped function with error handling
    """
    @wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            ctx = args[1] if len(args) > 1 else None
            if ctx and hasattr(ctx, 'send'):
                error_message = f"An error occurred: {str(e)}"
                await ctx.send(error_message)
            
            # Log the full error traceback
            print(f"Error in {func.__name__}: {str(e)}")
            print(traceback.format_exc())
            
    return wrapper

def is_in_guild():
    """
    Check if the command is being used in a guild (server) and not in DMs.
    
    Returns:
        commands.check: A command check that validates guild context
    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            await ctx.send("This command can only be used in a server, not in DMs.")
            return False
        return True
    
    return commands.check(predicate)

async def has_server_role(ctx: commands.Context) -> bool:
    """
    Check if the user has the required role for the current server
    
    Args:
        ctx (commands.Context): The command context
        
    Returns:
        bool: True if user has required role or no role is set, False otherwise
    """
    # Skip check in DMs
    if not ctx.guild:
        return True
        
    # Always allow admins and bot owners
    if ctx.author.guild_permissions.administrator or await ctx.bot.is_owner(ctx.author):
        return True
        
    try:
        async with ctx.bot.db_manager.get_session() as session:
            # Get server role configuration
            server_role = await session.query(ServerRole).filter(
                ServerRole.server_id == str(ctx.guild.id)
            ).first()
            
            # If no role is configured, allow access
            if not server_role:
                return True
                
            # Get the role object
            role = ctx.guild.get_role(int(server_role.role_id))
            
            # If role doesn't exist anymore, allow access
            if not role:
                return True
                
            # Check if user has the role
            return role in ctx.author.roles
                
    except Exception as e:
        print(f"Error checking server role: {e}")
        print(traceback.format_exc())
        # On error, default to allowing access
        return True

def requires_server_role():
    """
    Decorator to check for server-specific role requirement
    
    Returns:
        commands.check: A command check that validates role membership
    """
    async def predicate(ctx: commands.Context) -> bool:
        return await has_server_role(ctx)
        
    return commands.check(predicate)

def has_required_role(role_name: str):
    """
    Check if the user has a specific role.
    
    Args:
        role_name (str): The name of the required role
        
    Returns:
        commands.check: A command check that validates role membership
    """
    async def predicate(ctx: commands.Context) -> bool:
        if ctx.guild is None:
            return False
            
        role = discord.utils.get(ctx.author.roles, name=role_name)
        if role is None:
            await ctx.send(f"You need the '{role_name}' role to use this command.")
            return False
            
        return True
        
    return commands.check(predicate)
