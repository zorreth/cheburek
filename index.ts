import {
  ActionRowBuilder,
  ButtonBuilder,
  ButtonStyle,
  Client,
  Events,
  GatewayIntentBits,
} from 'discord.js';
import { Database } from 'bun:sqlite';
import { join } from 'path';
import { mkdirSync, existsSync } from 'fs';

const DATA_DIR = join(import.meta.dir, 'data');
if (!existsSync(DATA_DIR)) {
  mkdirSync(DATA_DIR, { recursive: true });
}

const db = new Database(`${DATA_DIR}/database.db`, { create: true });

db.run(`
  CREATE TABLE IF NOT EXISTS words (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    word TEXT UNIQUE,
    usage_count INTEGER DEFAULT 1,
    start_count INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
  );

  CREATE TABLE IF NOT EXISTS markov_chain (
    word1_id INTEGER,
    word2_id INTEGER,
    count INTEGER DEFAULT 1,
    PRIMARY KEY (word1_id, word2_id),
    FOREIGN KEY(word1_id) REFERENCES words(id),
    FOREIGN KEY(word2_id) REFERENCES words(id)
  );
`);

const upsertWord = db.prepare(`
  INSERT INTO words (word) 
  VALUES ($word)
  ON CONFLICT(word) DO UPDATE SET 
    usage_count = usage_count + 1
  RETURNING id;
`);

const upsertChain = db.prepare(`
  INSERT INTO markov_chain (word1_id, word2_id) 
  VALUES ($w1, $w2)
  ON CONFLICT(word1_id, word2_id) DO UPDATE SET count = count + 1;
`);

const getNextWords = db.prepare(`
  SELECT w.word as next_word, m.count 
  FROM markov_chain m
  JOIN words w ON m.word2_id = w.id
  WHERE m.word1_id = (SELECT id FROM words WHERE word = $word1);
`);

const checkWordExists = db.prepare(`
  SELECT word FROM words WHERE word = $word LIMIT 1;
`);

const getRandomStartWord = db.prepare(`
  SELECT word 
  FROM words 
  ORDER BY RANDOM() 
  LIMIT 1;
`);

const getStatsQuery = db.prepare(`
  SELECT 
    (SELECT COUNT(*) FROM words) as total_words,
    (SELECT SUM(count) FROM markov_chain) as total_links,
    (SELECT COUNT(*) FROM words WHERE date(created_at) = date('now')) as added_today,
    (SELECT COUNT(*) FROM words WHERE strftime('%Y-%m', created_at) = strftime('%Y-%m', 'now')) as added_this_month
`);

export function learnFromText(text: string) {
  const words = text.trim().split(/\s+/);
  if (words.length < 2) return;

  const transaction = db.transaction(() => {
    let prevId: number | null = null;

    for (let i = 0; i < words.length; i++) {
      const cleanWord = words[i]!.toLowerCase();

      const row = upsertWord.get({ $word: cleanWord }) as { id: number };
      const currentId = row.id;

      if (prevId !== null) {
        upsertChain.run({ $w1: prevId, $w2: currentId });
      }
      prevId = currentId;
    }
  });

  transaction();
}

function pickNextWord(rows: { next_word: string; count: number }[]): string | null {
  if (rows.length === 0) return null;
  const totalWeight = rows.reduce((sum, row) => sum + row.count, 0);
  let random = Math.random() * totalWeight;
  for (const row of rows) {
    random -= row.count;
    if (random <= 0) return row.next_word;
  }
  return rows[0]!.next_word;
}

export function generateMessage(startWord: string, maxLength: number = 15): string {
  let currentWord = startWord.toLowerCase();
  const result: string[] = [currentWord];

  for (let i = 0; i < maxLength - 1; i++) {
    const nextWords = getNextWords.all({ $word1: currentWord }) as {
      next_word: string;
      count: number;
    }[];
    const nextWord = pickNextWord(nextWords);

    if (!nextWord) break;

    result.push(nextWord);
    currentWord = nextWord;
  }

  return result.join(' ');
}

export function generateContextualMessage(userMessage: string, maxLength: number = 15): string {
  const userWords = userMessage.trim().split(/\s+/);

  const shuffledWords = userWords.sort(() => 0.5 - Math.random());

  let startWord = null;

  for (const word of shuffledWords) {
    const cleanWord = word.toLowerCase();
    const row = checkWordExists.get({ $word: cleanWord }) as { word: string } | undefined;

    if (row) {
      startWord = row.word;
      break;
    }
  }

  if (!startWord) {
    startWord = pickRandomStartWord();
  }

  return generateMessage(startWord, maxLength);
}

export function pickRandomStartWord(): string {
  const row = getRandomStartWord.get() as { word: string } | undefined;
  return row ? row.word : 'привет';
}

export function getBotStatistics() {
  const stats = getStatsQuery.get() as {
    total_words: number;
    total_links: number;
    added_today: number;
    added_this_month: number;
  };

  return `📊 **Статистика бота:**
- Словарный запас: **${stats.total_words}** слов
- Изучено связей: **${stats.total_links}**
- Новых слов сегодня: **${stats.added_today}**
- Новых слов за этот месяц: **${stats.added_this_month}**`;
}

function generateResponse() {
  const startWord = pickRandomStartWord();
  const generatedText = generateMessage(startWord, 12);
  return generatedText.charAt(0).toUpperCase() + generatedText.slice(1);
}

const client = new Client({
  intents: [
    GatewayIntentBits.Guilds,
    GatewayIntentBits.GuildMessages,
    GatewayIntentBits.MessageContent,
  ],
});

client.on(Events.ClientReady, (readyClient) => {
  console.log(`Logged in as ${readyClient.user.tag}!`);
});

client.on(Events.MessageCreate, async (message) => {
  if (message.author.bot) return;

  const textToLearn = message.cleanContent.replace(/(https?:\/\/[^\s]+)/g, '').trim();

  if (textToLearn.length > 0) {
    learnFromText(textToLearn);
  }

  const RANDOM_CHANCE = 0.05;
  if (Math.random() < RANDOM_CHANCE) {
    const reply = generateContextualMessage(textToLearn, 8);

    if (reply) {
      const formattedReply = reply.charAt(0).toUpperCase() + reply.slice(1);

      try {
        await message.channel.send(formattedReply);
      } catch (error: any) {
        console.error('Failed to send message:', error.message);
      }
    }
  }
});

client.on(Events.InteractionCreate, async (interaction) => {
  if (interaction.isChatInputCommand()) {
    switch (interaction.commandName) {
      case 'generate':
        const response = generateResponse();

        const repeatButton = new ButtonBuilder()
          .setCustomId('repeat_button')
          .setStyle(ButtonStyle.Primary)
          .setLabel('Перегенерировать')
          .setEmoji('🔁');

        const frescoButton = new ButtonBuilder()
          .setCustomId('fresco_button')
          .setStyle(ButtonStyle.Secondary)
          .setLabel('Жак Фреско')
          .setEmoji('👴');

        const row = new ActionRowBuilder<ButtonBuilder>().addComponents(repeatButton, frescoButton);

        try {
          await interaction.reply({ content: response, components: [row] });
        } catch (error: any) {
          console.error('Failed to reply interaction:', error.message);
        }
        break;

      case 'stats':
        const statsText = getBotStatistics();
        try {
          await interaction.reply(statsText);
        } catch (error: any) {
          console.error('Failed to reply interaction:', error.message);
        }
        break;
    }
  } else if (interaction.isButton()) {
    switch (interaction.customId) {
      case 'repeat_button':
        const newResponse = generateResponse();

        try {
          await interaction.update(newResponse);
        } catch (error: any) {
          console.error('Failed to update interaction:', error.message);
        }
        break;

      case 'fresco_button':
        break;
    }
  }
});

client.login(process.env.TOKEN!);
