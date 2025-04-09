import ast
import glob
import json
import os
from collections import OrderedDict

I18N_JSON_DIR   : os.PathLike = os.path.join(os.path.dirname(os.path.relpath(__file__)), 'locale')
DEFAULT_LANGUAGE: str         = "en_US" # default language
TITLE_LEN       : int         = 60      # Title display length
KEY_LEN         : int         = 30      # Key Name Display Length
SHOW_KEYS       : bool        = False   # Whether to display key information
SORT_KEYS       : bool        = False   # Whether to write to a file by global key name

def extract_i18n_strings(node):
    i18n_strings = []

    if (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "i18n"
    ):
        for arg in node.args:
            if isinstance(arg, ast.Str):
                i18n_strings.append(arg.s)

    for child_node in ast.iter_child_nodes(node):
        i18n_strings.extend(extract_i18n_strings(child_node))

    return i18n_strings

def scan_i18n_strings():
    """
    scan the directory for all .py files (recursively)
    for each file, parse the code into an AST
    for each AST, extract the i18n strings
    """
    strings = []
    print(" Scanning Files and Extracting i18n Strings ".center(TITLE_LEN, "="))
    for filename in glob.iglob("**/*.py", recursive=True):
        try:
            with open(filename, "r", encoding="utf-8") as f:
                code = f.read()
                if "I18nAuto" in code:
                    tree = ast.parse(code)
                    i18n_strings = extract_i18n_strings(tree)
                    print(f"{filename.ljust(KEY_LEN*3//2)}: {len(i18n_strings)}")
                    if SHOW_KEYS:
                        print("\n".join([s for s in i18n_strings]))
                    strings.extend(i18n_strings)
        except Exception as e:
            print(f"\033[31m[Failed] Error occur at {filename}: {e}\033[0m")

    code_keys = set(strings)
    print(f"{'Total Unique'.ljust(KEY_LEN*3//2)}: {len(code_keys)}")
    return code_keys

def update_i18n_json(json_file, standard_keys):
    standard_keys = sorted(standard_keys)
    print(f" Process {json_file} ".center(TITLE_LEN, "="))
    # Reading JSON files
    with open(json_file, "r", encoding="utf-8") as f:
        json_data = json.load(f, object_pairs_hook=OrderedDict)
    # Number of JSON entries before printing
    len_before = len(json_data)
    print(f"{'Total Keys'.ljust(KEY_LEN)}: {len_before}")
    # Identify missing keys and complete them
    miss_keys = set(standard_keys) - set(json_data.keys())
    if len(miss_keys) > 0:
        print(f"{'Missing Keys (+)'.ljust(KEY_LEN)}: {len(miss_keys)}")
        for key in miss_keys:
            if DEFAULT_LANGUAGE in json_file:
                # The default language has the same keys.
                json_data[key] = key
            else:
                # The value for other languages is set to #! + key names to mark them as untranslated.
                json_data[key] = "#!" + key
            if SHOW_KEYS:
                print(f"{'Added Missing Key'.ljust(KEY_LEN)}: {key}")
    # Recognize redundant keys and delete them
    diff_keys = set(json_data.keys()) - set(standard_keys)
    if len(diff_keys) > 0:
        print(f"{'Unused Keys  (-)'.ljust(KEY_LEN)}: {len(diff_keys)}")
        for key in diff_keys:
            del json_data[key]
            if SHOW_KEYS:
                print(f"{'Removed Unused Key'.ljust(KEY_LEN)}: {key}")
    # Sort by key order
    json_data = OrderedDict(
        sorted(
            json_data.items(),
            key=lambda x: (
                list(standard_keys).index(x[0]) if x[0] in standard_keys and not x[1].startswith('#!') else len(json_data),
            )
        )
    )
    # Prints the number of processed JSON entries
    if len(miss_keys) != 0 or len(diff_keys) != 0:
        print(f"{'Total Keys (After)'.ljust(KEY_LEN)}: {len(json_data)}")
    # Identify keys to be translated
    num_miss_translation = 0
    duplicate_items = {}
    for key, value in json_data.items():
        if value.startswith("#!"):
            num_miss_translation += 1
            if SHOW_KEYS:
                print(f"{'Missing Translation'.ljust(KEY_LEN)}: {key}")
        if value in duplicate_items:
            duplicate_items[value].append(key)
        else:
            duplicate_items[value] = [key]
    # Prints whether there are duplicate values
    for value, keys in duplicate_items.items():
        if len(keys) > 1:
            print("\n".join([f"\033[31m{'[Failed] Duplicate Value'.ljust(KEY_LEN)}: {key} -> {value}\033[0m" for key in keys]))

    if num_miss_translation > 0:
        print(f"\033[31m{'[Failed] Missing Translation'.ljust(KEY_LEN)}: {num_miss_translation}\033[0m")
    else:
        print(f"\033[32m[Passed] All Keys Translated\033[0m")
    # Write the processed results to a JSON file
    with open(json_file, "w", encoding="utf-8") as f:
        json.dump(json_data, f, ensure_ascii=False, indent=4, sort_keys=SORT_KEYS)
        f.write("\n")
    print(f" Updated {json_file} ".center(TITLE_LEN, "=") + '\n')

if __name__ == "__main__":
    code_keys = scan_i18n_strings()
    for json_file in os.listdir(I18N_JSON_DIR):
        if json_file.endswith(r".json"):
            json_file = os.path.join(I18N_JSON_DIR, json_file)
            update_i18n_json(json_file, code_keys)