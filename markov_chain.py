import json


class MarkovChain:
    def __init__(self) -> None:
        self.chain: dict[str, dict[str, int]] = {
            "__START__": {},
        }

    def process_words(self, words: list[str]):
        if not words:
            return

        for i, word in enumerate(words):
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

    def save(self):
        with open("data.json", "w") as f:
            json.dump(self.chain, f, indent=2)

    def load(self):
        with open("data.json", "r") as f:
            self.chain = json.load(f)
