import { pipeline } from '@huggingface/transformers';

const pipe = await pipeline('text-generation', 'HuggingFaceTB/SmolLM2-135M-Instruct');

const messages = [
  { role: 'system', content: 'You are helpful assistant.' },
  { role: 'user', content: 'What is the capital of US?' },
];

// Generate a response
const output = await pipe(messages, { max_new_tokens: 128 });
console.log(output[0]?.generated_text.at(-1)?.content);
