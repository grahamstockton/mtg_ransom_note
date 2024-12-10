import random
import time
import image_processing
import json
import marisa_trie
import os
import pickle
import ransom_note
from PIL import Image, ImageFile
from ransom_note import FragmentRecord

# main.py file provides an example of using the functions here. Will eventually build into a service
# so that we can put it in a website or discord bot or similar.

TRIE_FILE_NAME: str = "src/trie.marisa"
PICKLE_DATA_FILE_NAME: str = "src/data.pkl"
RAW_DATA_FILE_NAME: str = "src/data.json"
INPUT_STR: str = "pls chet"
MATCH_LIMIT: int = 20
NUM_TRIES_MATCHING: int = 5
CARD_FILE_NAME: str = "src/base.jpg"
TEXT_LINE_WIDTH: int = 500
TEXT_LINE_HEIGHT: int = 20
TEXT_STARTING_HEIGHT: int = 700
PADDING_BETWEEN_WORDS: int = 10
BEGINNING_OF_LINE_PADDING: int = 100

# This need to be constant, as otherwise the locations returned from the tree will be meaningless.
# If needed to be determined at runtime for some reason, could create a mapping system from id to
# field name
SRC_FIELD_NAMES: list[str] = ["name", "oracle_text", "flavor_text"]
SRC_LANGS: list[str] = ["en"]

print(os.getcwd())

def main():

    source_maps_list: list[dict] = None
    # load source map list
    if os.path.exists(PICKLE_DATA_FILE_NAME):
        print("loading pickled data...")
        try:
            with open(PICKLE_DATA_FILE_NAME, 'rb') as file:
                source_maps_list = pickle.load(file)
        except Exception as e:
            raise Exception("failed to load pickled data.", e)

    if source_maps_list == None and os.path.exists(RAW_DATA_FILE_NAME):
        # read in file
        print("loading json...")
        with open(RAW_DATA_FILE_NAME, 'r', encoding='utf8') as file:
            source_maps_list = json.load(file)

        # filter for languages
        print("filtering for languages...")
        source_maps_list = list(filter(lambda s: s["lang"] in SRC_LANGS, source_maps_list))

        # write pickle
        print("writing data to .pkl...")
        with open(PICKLE_DATA_FILE_NAME, 'wb') as file:
            pickle.dump(source_maps_list, file)
    
    if source_maps_list == None:
        raise Exception("failed to get source data")

    # load or generate trie
    print("loading trie from file...")
    trie: marisa_trie.RecordTrie = None
    if os.path.exists(TRIE_FILE_NAME):
        try:
            trie = marisa_trie.RecordTrie("<LH")
            trie.load(TRIE_FILE_NAME)
        except Exception as e:
            raise Exception("failed to load trie", e)
    else:
        print("trie not found. generating new trie")
        trie = ransom_note.generate_trie(source_maps_list, SRC_FIELD_NAMES)
        trie.save(TRIE_FILE_NAME)

    # filter non-alphabet non-whitespace characters
    input_str = "".join(i for i in INPUT_STR if (i.isalpha() or i.isspace())).lower()

    # tokenize
    print("tokenizing...")
    input_list = input_str.split()

    # get greedy result for each token
    print("getting results...")
    fragment_list: list[FragmentRecord] = []
    for i in input_list:
        fragment_list.extend(ransom_note.source_string_from_trie(i, trie, MATCH_LIMIT))

    # randomize
    for record in fragment_list:
        random.shuffle(record.sources)

    # look up cards
    print("sourcing fragments...")
    f_images: list[any] = []
    for f in fragment_list:
        f_img = find_word_with_retries(f, NUM_TRIES_MATCHING, source_maps_list)
        f_images.append(f_img)
        time.sleep(.1)

    # build new card
    print("building card...")
    card_file = open(CARD_FILE_NAME, 'rb')
    card_base: ImageFile = Image.open(card_file)
    final_card: ImageFile = image_processing.add_images_with_wrapping(card_base, \
                                            f_images, \
                                            TEXT_LINE_WIDTH, \
                                            BEGINNING_OF_LINE_PADDING, \
                                            TEXT_STARTING_HEIGHT, \
                                            TEXT_LINE_HEIGHT, \
                                            PADDING_BETWEEN_WORDS)

    # save result
    final_card.save("output" + str(time.time()) + ".png")
    final_card.show()

def find_word_with_retries(f: FragmentRecord, num_tries: int, src_map_list: list[dict]) -> ImageFile:
    for i in range(num_tries):
        try:
            img: ImageFile = image_processing.download_scryfall_img(src_map_list[f.sources[i][0]]["image_uris"]["normal"])
            res: ImageFile = image_processing.find_word_in_image(f.fragment, img)
            return res
        except Exception as e:
            print("Failed attempt number {} at finding word: {}".format(i + 1, e))
            if i == num_tries - 1:
                raise Exception("Failed attempt {} at finding word for fragment {}".format(num_tries, f))
            
    raise Exception("failed attempt to find fragment {}".format(f))
    
if __name__ == '__main__':
    main()