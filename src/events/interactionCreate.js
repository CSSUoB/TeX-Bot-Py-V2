module.exports = {
	name: 'interactionCreate',
	execute(interaction) {
		console.log(
			`${interaction.user.tag} in #${interaction.channel.name} triggered an interaction.`,
		);

		if (!interaction.isChatInputCommand()) return;

		const command = interaction.client.commands.get(
			interaction.commandName,
		);

		if (!command) return;

		try {
			command.execute(interaction);
		}
		catch (err) {
			console.error(err);
			interaction.reply({
				content: 'There was an errour while executing this command.',
				ephemeral: true,
			});
		}
	},
};
