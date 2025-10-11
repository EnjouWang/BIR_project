import re

def compute_text_stat(text: str, keyword: str) -> dict:
    """
    text: article content
    keyword: the word that user searched
    dict: result is saved as dict
    """

    char_count = len(text)
    char_count_no_spaces = len(re.sub(r"\s", "", text))

    words = text.split()
    words_count = len(words)

    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text.strip())
    # sentences = sent_tokenize(text)
    sentences_count = len([s for s in sentences if s.strip()])

    non_ascii_chars = [ch for ch in text if ord(ch)> 127]
    non_ascii_chars_count = len(non_ascii_chars)

    non_ascii_words = [w for w in words if any(ord(ch) > 127 for ch in w)]
    non_ascii_word_count = len(non_ascii_words)

    keyword_count = len(re.findall(re.escape(keyword), text, re.IGNORECASE))

    return {
        "characters_including_spaces": char_count,
        "characters_excluding_spaces": char_count_no_spaces,
        "words": words_count,
        "sentences": sentences_count,
        "non_ascii_characters": non_ascii_chars_count,
        "non_ascii_words": non_ascii_word_count,
        "keyword_counts": keyword_count
    }

if __name__ == "__main__":
    text = "This essay focuses on themes in Explaining Cancer: Finding Order in Disorder (2018) by Anya Plutynski, a monograph that has important things to say about both the peculiarities of cancers and our theories about them. Cancer's agents of destruction are human cells that have been recruited and to some extent transformed into pathological organisms or the building blocks of tumors. Cancers both undermine and exploit mechanisms of multicellular organization, and understanding them gives rise to difficult philosophical problems. In addition to sketching Plutynski's discussion of these problems, this essay defends Christopher Boorse's account of disease from Plutynski's criticisms, and it expresses some qualms about her treatment of scientific explanation."
    stats = compute_text_stat(text, keyword="cancer")
    for k, v in stats.items():
        print(f"{k}: {v}")