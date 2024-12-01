import itertools
import marisa_trie

# Represents a fragment of the desired sentence and the sourced pieces used to build that fragment
class FragmentRecord:
    def __init__(self, fragment: str, sources: list[tuple[int, int]]) -> None:
        self.fragment = fragment
        self.sources = sources
    def __repr__(self):
        return "{{fragment: {}, sources: {}}}".format(self.fragment, self.sources)

# Create a trie with each node representing a letter in a text sequence
#
# Params:
#     - src_maps_list: list of maps containing our target data as values
#     - src_field_names: list of key values which are to be used for scanning those maps
# Output:
#     - marisa_trie.RecordTrie
# Trie maps from string content to location (index, field) in src_maps_list. Will give multiple results for the same string
def generate_trie(src_maps_list: list[dict[str, any]], src_field_names: list[str]) -> marisa_trie.RecordTrie:
    input_list: list[tuple[str, tuple[int, int]]] = []
    for idx, map in enumerate(src_maps_list):
        for fidx, field in enumerate(src_field_names):
            if field in map:
                # trie needs to work for any starting point
                content: str = map[field].lower()
                for i in range(len(content)):
                    input_list.append((content[i:], (idx, fidx)))

    return marisa_trie.RecordTrie("<LH", input_list)

# recursive method to build a string from pieces present in the tree and return the locations of all of those pieces
# applies a limit for the number of those pieces, so we don't get thousands of results for a single character
def source_string_from_trie(desired_string: str,
                            trie: marisa_trie.RecordTrie,
                            match_limit: int
                            ) -> list[FragmentRecord]:
    # check if whole string matches -- this is a special case
    if desired_string in trie:
        results = [desired_string]
    else:
        results = source_string_helper(desired_string, trie)

    return list(map(lambda s: FragmentRecord(s, get_vals_for_keys_w_limit(s, trie, match_limit)), results))

# recursive algorithm to get all substrings
def source_string_helper(desired_string: str, trie: marisa_trie.RecordTrie) -> list[str]:
    # find the longest substring that is in trie
    longest, start, end = "", None, None
    for i in range(len(desired_string)):
        for j in range(i + 1, len(desired_string) + 1):

            # only consider strings longer than longest found
            if j - i <= len(longest):
                continue

            # if match not found, don't look for even longer matches
            candidate = desired_string[i:j]
            if trie.keys(candidate):
                longest = candidate
                start = i
                end = j
            else:
                break

    if longest == "":
        raise Exception("Message not found in source:", desired_string)
    
    return_list = []
    # if longest doesn't include beginning
    if start > 0:
        return_list.extend(source_string_helper(desired_string[:start], trie))

    # add string found in this method
    return_list.append(longest)

    # if longest doesn't include end
    if end < len(desired_string):
        return_list.extend(source_string_helper(desired_string[end:], trie))

    return return_list

# get values for all superstrings
def get_vals_for_keys_w_limit(desired_str: str, trie: marisa_trie.RecordTrie, limit: int):
    return_list = []
    keys = itertools.islice(trie.iterkeys(desired_str), limit)
    for k in keys:
        return_list.extend(trie[k])

    return return_list