import json
import os
import random


class MarkovChain:
    def __init__(self) -> None:
        self.chain: dict[str, dict[str, int]] = {
            "__START__": {},
        }

    def process_words(self, words: list[str]):
        if not words:
            return

        for i, word in enumerate(words):
            if not word.strip() or word == "__START__" or word == "__END__":
                continue

            if not word in self.chain:
                self.chain[word] = {}

            if i == 0:
                self.chain["__START__"][word] = self.chain["__START__"].get(word, 0) + 1

            if i < len(words) - 1:
                next_word = words[i + 1]
                self.chain[word][next_word] = self.chain[word].get(next_word, 0) + 1
            else:
                self.chain[word]["__END__"] = self.chain[word].get("__END__", 0) + 1

        self.save()

    def generate_message(self, max_length: int) -> str:
        if not self.chain["__START__"]:
            raise Exception("The word chain is empty")

        START_WORD_TYPE = os.environ["START_WORD_TYPE"]

        if START_WORD_TYPE == "freq":
            start_words = list(self.chain["__START__"].keys())
            weights = list(self.chain["__START__"].values())
            first_word = random.choices(start_words, weights, k=1)[0]
        elif START_WORD_TYPE == "random":
            words = list(self.chain.keys())
            words.remove("__START__")
            first_word = random.choice(words)
        else:
            raise Exception("START_WORD_TYPE must be either freq or random")

        message = [first_word]

        i = 0

        while len(message) <= max_length:
            current_word = message[i]

            next_words = list(self.chain[current_word].keys())
            weights = list(self.chain[current_word].values())
            next_word = random.choices(next_words, weights, k=1)[0]

            if next_word == "__END__":
                break

            message.append(next_word)
            i += 1

        return " ".join(message)

    def save(self):
        with open("data.json", "w", encoding="utf8") as f:
            json.dump(self.chain, f, indent=2, ensure_ascii=False)

    def load(self):
        if not os.path.isfile("data.json"):
            self.save()

        with open("data.json", "r", encoding="utf8") as f:
            self.chain = json.load(f)
