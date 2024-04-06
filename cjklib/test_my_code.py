# -*- coding: utf-8 -*-
import pandas as pd
import os

def flatten(alist):
    if len(alist) == 1 and not isinstance(alist, list):
        return alist
    newlist = []
    for sublist in alist:
        for el in flatten(sublist):
            newlist.append(el)
    return newlist


def decompositionFromString(decomposition):
    """
    returned List of str and tuple of shape (str, int)\n
    Inside the returned list:\n
    str: IDS Operator\n
    tuple of shape (str, int): Chinese character
    """
    # some parts of code have been deleted. please refer to the original cjklib if needed.
    componentsList = []
    index = 0 # cursor of which under process.
    while index < len(decomposition):
        char = decomposition[index]
        if char in (['⿰', '⿱', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻'] + ['⿲', '⿳']):
            componentsList.append(char)
        else:
            if index+1 < len(decomposition)\
                and decomposition[index+1] == '[':
                # extract glyph information
                # Sometimes the parts of a character have other glyphs, which are noted inside []. For example, "鵢","⿰身[1]鳥"
                endIndex = decomposition.index(']', index+1)
                charGlyph = int(decomposition[index+2:endIndex])
                index = endIndex
            else:
                # take default glyph if none specified
                charGlyph = 0
            componentsList.append((char, charGlyph))
        index = index + 1
    return componentsList


def getTableData(csv_file_path):
    table_data = []
    with open(csv_file_path, encoding="utf-8") as f:
        lines = f.readlines()
    columns = None
    for i, line in enumerate(lines):
        if line.startswith("#"):
            continue
        else:
            if columns is None:
                columns = lines[i - 1].strip("#").strip().split(", ")
        if os.path.basename == "charactershanghaineseipa.csv":
            after_split = line.strip().split()
        else:
            after_split = line.strip().split(",")
        assert len(after_split) == len(columns), f"num of columns doesn't match the data"
        if "ChineseCharacter" in columns:
            after_split[columns.index("ChineseCharacter")] = after_split[columns.index("ChineseCharacter")].strip("\"")
        if "StrokeOrder" in columns:
            after_split[columns.index("StrokeOrder")] = after_split[columns.index("StrokeOrder")].strip("\"")
        if "Decomposition" in columns:
            after_split[columns.index("Decomposition")] = after_split[columns.index("Decomposition")].strip("\"")
        if "Glyph" in columns:
            after_split[columns.index("Glyph")] = int(after_split[columns.index("Glyph")])
        table_data.append(after_split)
    table_data = pd.DataFrame(table_data, columns=columns)
    return table_data

df_character_decomposition = getTableData("data/characterdecomposition.csv")
df_stroke_order = getTableData("data/strokeorder.csv")
df_stroke_abbr = getTableData("data/strokes.csv")

with open(r"C:\Users\79437\OneDrive\Desktop\FudanOCR\character-profile-matching\data\decompose.txt", encoding="utf-8") as f:
    lines = f.readlines()
chinese_character_list2 = []
decomposition_list2 = []
for line in lines:
    if "&" in line or ";" in line:
        continue
    char, decomposition = line.split(":")
    decomposition = decomposition.strip("\n").replace(" ", "")
    if len(decomposition) == 1: # otherwise LOOPING
        continue
    chinese_character_list2.append(char)
    decomposition_list2.append(decomposition)
character_decomposition2 = {"ChineseCharacter": chinese_character_list2, "Decomposition": decomposition_list2}
df_character_decomposition2 = pd.DataFrame(character_decomposition2)

def getDecompositionEntries(char, glyph=0):
    """
    returned list of decompositions, each of which is also a list of Chinese character or IDS Operator\n
    Each decomposition is a possible decomposition for this character of this glyph, and \n
    ONLY IF one entry succeeds everything is OK.
    """
    # selected_decomposition = None
    result = df_character_decomposition[(df_character_decomposition["ChineseCharacter"] == char) 
                                        & (df_character_decomposition["Glyph"] == glyph)]["Decomposition"].tolist()

    # additional data taken from FudanOCR ACPM
    result2 = df_character_decomposition2[(df_character_decomposition2["ChineseCharacter"] == char)]["Decomposition"].tolist()
    result.extend(result2)
    return [decompositionFromString(decomposition) for decomposition in result]


def getStrokeOrderEntry(char, glyph=0):
    result = df_stroke_order[(df_stroke_order["ChineseCharacter"] == char) & (df_stroke_order["Glyph"] == glyph)]["StrokeOrder"].tolist()
    assert len(result) <= 1, "one char with one glyph is supposed to have only one stroke order"
    return result[0] if result else ""


def buildStrokeOrder(char, glyph, includePartial=False, cache=None):
    def getFromDecomposition(char, glyph):
        def getFromEntry(subTree, index=0):
            strokeOrder = []
            if type(subTree[index]) != type(()): # not tuple, then IDS operator
                # IDS operator
                character = subTree[index]
                if character in ['⿰', '⿱', '⿴', '⿵', '⿶', '⿷', '⿸', '⿹', '⿺', '⿻']:
                    # check for IDS operators we can't make any order
                    # assumption about
                    if character in ['⿻']:
                        return None, index
                    # ⿴ should only occur for 囗
                    elif character == '⿴':
                        so, newindex = getFromEntry(subTree, index+1)
                        if not so: 
                            return None, index
                        strokes = [order.replace(' ', '-').split('-')
                            for order in so]
                        if strokes != [['S', 'HZ', 'H']]:
                            import warnings
                            warnings.warn(
                                "Invalid decomposition entry %r" % subTree)
                            return None, index
                        strokeOrder.append('S-HZ')
                        so, index = getFromEntry(subTree, newindex+1)
                        if not so: 
                            return None, index
                        strokeOrder.extend(so)
                        strokeOrder.append('H')
                    # ⿷ should only occur for ⼕ and ⼖
                    elif character == '⿷':
                        so, newindex = getFromEntry(subTree, index+1)
                        if not so: 
                            return None, index
                        strokes = [order.replace(' ', '-').split('-')
                            for order in so]
                        if strokes not in ([['H', 'SZ']], [['H', 'SW']]):
                            import warnings
                            warnings.warn(
                                "Invalid decomposition entry %r" % subTree)
                            return None, index
                        strokeOrder.append(strokes[0][0])
                        so, index = getFromEntry(subTree, newindex+1)
                        if not so: 
                            return None, index
                        strokeOrder.extend(so)
                        strokeOrder.append(strokes[0][1])
                    else:
                        if (character == '⿶'
                            or (character == '⿺'
                                and type(subTree[index+1]) == type(())
                                and subTree[index+1][0] in '辶廴乙')):
                            # IDS operators with order right one first
                            subSequence = [1, 0]
                        else:
                            # IDS operators with order left one first
                            subSequence = [0, 1]
                        # Get stroke order for both components
                        subStrokeOrder = []
                        for _ in range(0, 2):
                            so, index = getFromEntry(subTree, index+1)
                            if not so:
                                return None, index
                            subStrokeOrder.append(so)
                        # Append in proper order
                        for seq in subSequence:
                            strokeOrder.extend(subStrokeOrder[seq])
                elif character in ['⿲', '⿳']:
                    # Get stroke order for three components
                    for _ in range(0, 3):
                        so, index = getFromEntry(subTree, index+1)
                        if not so:
                            return None, index 
                        strokeOrder.extend(so)
                else:
                    assert False, f'{character} is not an IDS character'
            else:
                # no IDS operator but character
                char, charGlyph = subTree[index]
                # if the character is unknown or there is none, raise
                if char == '？':
                    return None, index
                else:
                    # recursion
                    so = buildStrokeOrder(char, charGlyph,
                        includePartial, cache)
                    if not so:
                        """
                        The process is simplified. For the complete please refer to project cjklib.
                        """
                        return None, index
                    strokeOrder.append(so)
            return (strokeOrder, index) 

        # Try to find a partition without unknown components
        for decomposition in getDecompositionEntries(char, glyph):
            so, _ = getFromEntry(decomposition)
            if so:
                """
                ONLY IF one kind of decompositions is doable, the function returns.
                """
                return ' '.join(so)

    if cache is None:
        cache = {}
    if (char, glyph) not in cache:
        # if there is an entry for the whole character return it
        order = getStrokeOrderEntry(char, glyph)
        if not order: # not existing in 
            order = getFromDecomposition(char, glyph)
        cache[(char, glyph)] = order
    return cache[(char, glyph)]

def strokeabbr2idx(strokeorder_list):
    indexed_strokeorder_list = []
    for strokeabbr_list in strokeorder_list:
        if strokeabbr_list is None:
            indexed_strokeorder_list.append("UNDEFINED")
        else:
            stroke_idx_list = []
            strokeabbr_list = strokeabbr_list.replace(" ", "-").split("-")
            for strokeabbr in strokeabbr_list:
                query_result = df_stroke_abbr[df_stroke_abbr["StrokeAbbrev"] == strokeabbr]
                assert len(query_result) == 1, "query result num is not one."
                stroke_idx = query_result.index[0]
                stroke_idx_list.append(stroke_idx)
            indexed_strokeorder_list.append(stroke_idx_list)
    return indexed_strokeorder_list
    
trainval_character_table = pd.read_csv("trainval_character_table.csv")


def main():
    strokeorder_list = []
    the_cache = {}
    for i in range(len(trainval_character_table)):
        for glyph_idx in range(4):
            if glyph_idx >= 1 and the_cache[(trainval_character_table.iloc[i]["字"], glyph_idx - 1)] is not None:
                break
            if glyph_idx >= 1:
                del the_cache[(trainval_character_table.iloc[i]["字"], glyph_idx - 1)]
            buildStrokeOrder(trainval_character_table.iloc[i]["字"], glyph_idx, cache=the_cache)

    for i in range(len(trainval_character_table)):
        for glyph_idx in range(4):
            if (trainval_character_table.iloc[i]["字"], glyph_idx) in the_cache.keys():
                strokeorder_list.append(the_cache[(trainval_character_table.iloc[i]["字"], glyph_idx)])
                break
        
    
    character_list = trainval_character_table["字"].tolist()
    
    # generating intermediate file
    intermediate_df = pd.DataFrame({"char": character_list, "strokeorder": strokeorder_list})
    intermediate_df.to_csv("intermediate.csv")

    # generating output file
    indexed_strokeorder_list = strokeabbr2idx(strokeorder_list)
    output_df = pd.DataFrame({"char": character_list, "strokeorder": indexed_strokeorder_list})
    output_df.to_csv("output.csv")

    # the_cache = {}
    # 字 = "丽"
    # for glyph_idx in range(4):
    #     if glyph_idx >= 1 and the_cache[(字, glyph_idx - 1)] is not None:
    #         break
    #     if glyph_idx >= 1:
    #         del the_cache[(字, glyph_idx - 1)]

if __name__ == "__main__":
    main()