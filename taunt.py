from random import shuffle

from nextcord import (
    SelectOption,
    utils,
    AllowedMentions,
)

from src.common.common import *


class TauntDropdown(ui.Select):
    def __init__(
        self,
        ctx: CustomContext,
        num_1: int,
        num_2: int,
        answering_clan: str,
    ):
        self.ctx: CustomContext = ctx
        self.correct_answer: int = num_1 * num_2
        self.receiving_clan: str = answering_clan

        wrong_answers: List[int] = []

        while len(wrong_answers) < 4:
            # List of possible numbers excluding the correct answer
            possible_numbers = [
                x
                for x in range(self.correct_answer // 2, self.correct_answer * 2)
                if x != self.correct_answer
            ]

            # All possible answers added
            if len(wrong_answers) >= len(possible_numbers):
                break

            # Add random number
            num = randint(min(possible_numbers), max(possible_numbers))
            if num not in wrong_answers:
                wrong_answers.append(num)

        # Create options from chosen numbers, then randomise order
        options: List[SelectOption] = [
            SelectOption(label=str(x))
            for x in set(wrong_answers + [self.correct_answer])
        ]
        shuffle(options)

        super().__init__(
            placeholder=f"What's {num_1} * {num_2}?",
            min_values=1,
            max_values=1,
            options=options,
        )

    async def callback(self, interaction: CustomInteraction) -> None:
        """
        Callback for when a user selects an option.
        If the user selects the correct answer, the taunt will run; if not, the user will be told so.

        :param interaction: The interaction to handle.
        """
        chosen_answer: int = int(self.values[0])
        sent_by: Union[Member, User] = self.ctx.author
        answered_by: Union[Member, User] = interaction.user

        # Correct
        if chosen_answer == self.correct_answer:
            # Check if the user has already responded to their maximum amount of taunts
            # DB interaction omitted for security purposes
            ...

            # If the user has not reached their maximum amount of taunts, or if Eagle Eyes is active, run the taunt
            # DB interaction omitted for security purposes
            if ...:
                self.view.is_answered = True
                await execute_taunt(
                    self.ctx,
                    sent_by,
                    answered_by,
                    get_user_clan(sent_by),
                    get_user_clan(answered_by),
                    interaction=interaction,
                )
                self.view.answered_by = answered_by
                await self.view.disable()
            # Otherwise, send an error message
            else:
                await interaction.error(
                    f"You can only respond to {get_cmd_cap(answered_by)} taunts each day!",
                )
        # Incorrect
        else:
            await interaction.error(
                f"That's not right.",
            )


class TauntMenu(ui.View):
    """Menu for taunting a clan, including a dropdown for answers."""

    def __init__(
        self,
        ctx: CustomContext,
        num_1: int,
        num_2: int,
        sending_clan: str,
        receiving_clan: str,
    ):
        super().__init__(
            timeout=None,
        )

        self.message: Optional[Message] = None
        self.ctx: CustomContext = ctx
        self.sending_clan: str = sending_clan.capitalize()
        self.answering_clan: str = receiving_clan.capitalize()
        self.answered_by: Optional[Union[Member, User]] = None
        self.is_answered: bool = False

        self.add_item(
            TauntDropdown(
                ctx=ctx,
                num_1=num_1,
                num_2=num_2,
                answering_clan=self.answering_clan,
            )
        )

    async def disable(self):
        """Disables the view."""
        self.is_answered = True

        # Remove all children
        # Updates with message.edit()
        self.children = []

        if self.message:
            embed = self.message.embeds[0]
            embed.description = f"{self.answered_by.mention} entered the fight against {self.sending_clan}!"

            # Update message to show that the taunt has been answered
            await self.message.edit(embed=embed, view=self)

        # Stop listening for interactions
        self.stop()

    async def interaction_check(self, interaction: CustomInteraction) -> bool:
        """
        Checks whether a user is allowed to interact.

        :param interaction: The interaction to check.
        :returns: Whether the user is allowed to interact.
        """
        # Check if the taunt has already been answered
        if self.is_answered:
            await interaction.error("This taunt has already been answered.")

            # View should already be disabled, but just in case
            await self.disable()
            return False

        # Check if the user is in the correct clan
        if get_user_clan(interaction.user) == self.answering_clan:
            return True
        else:
            # The role to mention. Make sure to use allowed_mentions if not using the role in an embed,
            # as otherwise the role will be pinged
            role = utils.get(interaction.guild.roles, name=self.answering_clan)

            await interaction.error(f"This taunt is for {role.mention}!")
            return False
