USI_PIECES = {
    "歩": "P",
    "香": "L",
    "桂": "N",
    "銀": "S",
    "金": "G",
    "角": "B",
    "飛": "R",
    "王": "K",
}


trans_file1 = {'一': "a", '二': "b", '三': "c", '四': "d", '五': "e", '六': "f", '七': "g", '八': "h", '九': "i"}
trans_file2 = {'1': "a", '2': "b", '3': "c", '4': "d", '5': "e", '6': "f", '7': "g", '8': "h", '9': "i"}
trans_file3 = {'１': "1", '２': "2", '３': "3", '４': "4", '５': "5", '６': "6", '７': "7", '８': "8", '９': "9"}

def process_sfen(lines):
    result = "position startpos moves "
    for line in lines:
        space_index = line.index(" ")
        moved_file = line[space_index + 1]  #使う
        moved_rank = line[space_index + 2]

        if line[space_index + 4] == "(":
            before_file = line[space_index + 5]  #使う
            before_rank = line[space_index + 6]
        else:
            before_file = line[space_index + 6]
            before_rank = line[space_index + 7]

        result_moved_file = trans_file3.get(moved_file)
        result_moved = trans_file1.get(moved_rank)
        result_before = trans_file2.get(before_rank)
        

        print(result_moved_file, moved_rank, before_file, before_rank)
    
        if "打" in line:
            piece = USI_PIECES.get(line[space_index + 3])
            made_line = str(piece) + "*" + str(result_moved_file) + str(result_moved) + " "

        else:
            made_line = str(before_file) + str(result_before) + str(result_moved_file) + str(result_moved)

            if "成(" in line:
                made_line += "+ "

            else :
                made_line += " "
                
        result += made_line
        
    return result
    

with open("translated_kifs/cleaned_kif.txt", "r", encoding="utf-8") as f:
    lines = f.readlines()

changed_sfen = process_sfen(lines)

with open("translated_kifs/output.sfen", "w", encoding="utf-8") as f:
    f.write(changed_sfen)

