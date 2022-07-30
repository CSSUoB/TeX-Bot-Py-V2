import { Client, GatewayIntentBits } from 'discord.js';
import env from 'dotenv';

env.config();

const client = new Client({ intents: [GatewayIntentBits.Guilds] });

client.once('ready', () => {
	console.log('Ready!');
});

client.login();
