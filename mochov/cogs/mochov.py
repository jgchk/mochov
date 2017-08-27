import discord
from discord.ext import commands
from markov.markov import Markov, EmptyModelError


def setup(bot):
    bot.add_cog(Mochov(bot))


def check_manage_server_permission(ctx):
    author = ctx.message.author
    channel = ctx.message.channel
    return author.permissions_in(channel).manage_server


class Mochov:
    def __init__(self, bot):
        self.bot = bot

        self.models = {}

    async def on_message(self, message):
        if message.author.bot:
            return

        if message.clean_content:
            if message.clean_content[0] == self.bot.command_prefix:
                return

            if message.author.id not in self.models:
                self.models[message.author.id] = Markov(prefix=message.author.id)

            self.models[message.author.id].add_line_to_index(message.clean_content.split())

    @commands.command(pass_context=True)
    async def mochov(self, ctx, member: discord.Member, *start_text):
        if member is None:
            member = ctx.message.author

        if member.id not in self.models:
            self.models[member.id] = Markov(prefix=member.id)

        try:
            if start_text:
                sentence = self.models[member.id].generate(max_words=100, seed=list(start_text))
            else:
                sentence = self.models[member.id].generate(max_words=100)
        except EmptyModelError:
            await self.bot.say("Not enough data for {}".format(member))
        else:
            await self.bot.say(" ".join(sentence))

    @commands.command(pass_context=True, aliases=["clear_model"])
    @commands.check(check_manage_server_permission)
    async def clear_models(self, ctx, member: discord.Member = None):
        if member:
            confirmation_msg = await self.bot.say("Are you sure you want to delete data for {}?".format(member))
        else:
            confirmation_msg = await self.bot.say("Are you sure you want to delete all data?")
        await self.bot.add_reaction(confirmation_msg, "✅")
        await self.bot.add_reaction(confirmation_msg, "❌")

        reaction = await self.bot.wait_for_reaction(["✅", "❌"], message=confirmation_msg, timeout=60,
                                                    user=ctx.message.author)
        await self.bot.delete_message(confirmation_msg)
        if reaction is None or reaction.reaction.emoji == "❌":
            return

        if member:
            self.models[member.id].flush()
        else:
            next(iter(self.models.values())).flush(all=True)
