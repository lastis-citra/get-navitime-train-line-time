import requests
from bs4 import BeautifulSoup
import sys
import time
import re

class Global:
    USE = False
    END = "横浜"

def main(args):
    if len(args) < 3:
        print("Usage: python main.py <uris> <dateInts> <dirs> [read_file] [sort_targets]")
        return

    uri_array = args[0].split(',')
    date_int_array = args[1].split(',')
    dir_array = args[2].split(',')
    read_file = len(args) > 3 and args[3] == "1"
    sort_target_array = args[4].split(',') if len(args) > 4 else []

    tmp_file_name = "tmp.csv"
    encode = "utf_8_sig"
    inputs = list(zip(uri_array, zip(date_int_array, dir_array)))

    if not read_file:
        tmp_name_time_tuple_list_list_buf_array = []
        for uri, (date_int_str, dir_str) in inputs:
            date_int = int(date_int_str)
            dir_int = int(dir_str)
            print(f"uri: {uri}, dateInt: {date_int}, dir: {dir_int}")
            result = main_process(uri, date_int, dir_int)
            tmp_name_time_tuple_list_list_buf_array.append(result)

        tmp_name_time_tuple_list_list_buf = [item for sublist in tmp_name_time_tuple_list_list_buf_array for item in sublist]

        # 中間データを出力
        with open(tmp_file_name, 'w', encoding=encode, newline='') as tmp_file:
            # writer = csv.writer(tmp_file)
            writer = tmp_file.write
            for name_time_tuple_list_list in tmp_name_time_tuple_list_list_buf:
                for name_time_tuple in name_time_tuple_list_list:
                    syubetsu, dest, name_time_seq = name_time_tuple
                    name_time_str = ','.join([f"{name}({time})" for name, time in name_time_seq])
                    writer(f"{syubetsu},{dest},{name_time_str}\n")

        name_time_tuple_list_list_buf_array = tmp_name_time_tuple_list_list_buf_array
    else:
        with open(tmp_file_name, 'r', encoding=encode) as source:
            lines = source.readlines()
        x = []
        for line in lines:
            line_array = line.strip().split(',')
            syubetsu = line_array[0]
            dest = line_array[1]
            name_time_string = ','.join(line_array[2:])
            tmp = name_time_string.split(')')
            name_time_tuple_seq = []
            for tmp2 in tmp:
                if tmp2:
                    tmp_array = tmp2.split('(')
                    if len(tmp_array) > 1:
                        name_time_array = tmp_array[1].split(',')
                        name_time_tuple_seq.append((name_time_array[0], name_time_array[1]))
            x.append((syubetsu, dest, name_time_tuple_seq))
        name_time_tuple_list_list_buf_array = [x]

    name_time_tuple_list_list_buf = [item for sublist in name_time_tuple_list_list_buf_array for item in sublist]

    # このテーブルに含まれるすべての列車の停車駅と時刻の組を取得
    name_time_table = [item for sublist in name_time_tuple_list_list_buf for item in sublist]

    for name_time_seq in name_time_table:
        print(f"{name_time_seq[0]} {name_time_seq[1]}: {name_time_seq[2]}")

    first_name_seq = create_first_name_seq(name_time_table)

    # このテーブルに含まれる列車のすべての停車駅のリストを作成
    all_name_seq = create_name_seq(first_name_seq, 0, name_time_table)

    # 種別と行き先のリスト
    syubetsu_dest_seq_pre = [(name_time_seq[0], name_time_seq[1]) for name_time_seq in name_time_table]

    # このテーブルに含まれる列車のすべての停車時刻のリストを作成
    time_seq_seq_pre = []
    for name_time_seq_t in name_time_table:
        name_time_seq = name_time_seq_t[2]
        check_name_seq = [name_time_tuple[0] for name_time_tuple in name_time_seq]
        time_seq = []
        for name in all_name_seq:
            if name in check_name_seq:
                point = len(check_name_seq) - 1 - check_name_seq[::-1].index(name)
                time = name_time_seq[point][1]
                if " " in time:
                    tmp = time.split(" ")
                    time_seq.append((tmp[0], tmp[1]))
                else:
                    time_seq.append((time, ""))
            else:
                time_seq.append(("", ""))
        time_seq_seq_pre.append(time_seq)

    # 一番，時刻が入っている数が多い駅を探したい
    count_seq = [0] * len(all_name_seq)
    for time_seq in time_seq_seq_pre:
        for i, time in enumerate(time_seq):
            if time[0] or time[1]:
                count_seq[i] += 1
    max_index = count_seq.index(max(count_seq))
    print(f"maxIndex: {max_index}, {all_name_seq[max_index]}")

    # 種別，行き先も一緒に並び替え，削除するために一度結合する
    name_time_table_pre = list(zip(syubetsu_dest_seq_pre, time_seq_seq_pre))

    # sortTargetArrayが入力されている場合は，そちらを採用し，入力されていない場合はmaxIndexを採用する
    sort_index_array = [all_name_seq.index(sort_target) for sort_target in sort_target_array] if sort_target_array else [max_index]

    # Indexの発車時刻でソート，発車時刻がない場合は到着時刻
    def sort_by_index_station(index, _name_time_table):
        if index >= 0:
            return sorted(_name_time_table, key=lambda a: a[1][index][1] if a[1][index][1] else a[1][index][0])
        return _name_time_table

    name_time_table_pre2 = name_time_table_pre
    for sort_index in sort_index_array:
        print(f"sortIndex: {sort_index}, {all_name_seq[sort_index]}")
        name_time_table_pre2 = sort_by_index_station(sort_index, name_time_table_pre2)

    # 同値を削除する（すべての発着時刻を文字列に結合して比較）
    seen = set()
    name_time_table_pre3 = []
    for item in name_time_table_pre2:
        key = ','.join([f"{t[0]},{t[1]}" for t in item[1]])
        if key not in seen:
            seen.add(key)
            name_time_table_pre3.append(item)

    time_seq_seq = [name_time[1] for name_time in name_time_table_pre3]
    syubetsu_dest_seq = [name_time[0] for name_time in name_time_table_pre3]

    # 通過駅の場合はレを入れる
    time_seq_seq2 = []
    for time_seq in time_seq_seq:
        tmp_seq = []
        for i in range(len(time_seq) - 1):
            if time_seq[i] == ("", ""):
                check_str_seq = time_seq[:i]
                check_str_string = ''.join([t[0] for t in check_str_seq])
                check_end_seq = time_seq[i+1:]
                check_end_string = ''.join([t[0] for t in check_end_seq])
                if check_end_string and check_str_string:
                    tmp_seq.append(("レ", "レ"))
                else:
                    tmp_seq.append(time_seq[i])
            else:
                tmp_seq.append(time_seq[i])
        tmp_seq.append(time_seq[-1])
        time_seq_seq2.append(tmp_seq)

    # 着発表示を作る
    all_str_end_seq = [check_str_end(i, time_seq_seq) for i in range(len(time_seq_seq[0]))]

    # 着発表示に合わせて駅名を調整する
    all_name_tuple_seq2 = [(all_name_seq[i], all_name_seq[i]) if all_str_end_seq[i][1] else (all_name_seq[i], "") for i in range(len(all_str_end_seq))]

    # timeSeqSeqに種別と行き先を足す
    syubetsu_dest_time_seq_seq = list(zip(syubetsu_dest_seq, time_seq_seq2))

    # ファイル出力用
    result_encode = "utf_8_sig"
    file_name = "result.csv"
    with open(file_name, 'w', encoding=result_encode) as w:
        def print_and_write(w, str_val):
            w.write(str_val)  # 手動で書き込み
            print(str_val, end='')

        # 表示用
        # 駅名
        print_and_write(w, ",,")
        for name_tuple in all_name_tuple_seq2:
            # 駅名の（福井県）や〔東福バス〕などを削除する
            # （も）も含まない0文字以上の文字列を（）で囲んだ文字列にマッチする正規表現
            # 〔〕も同様の処理
            rename = name_tuple[0]
            rename = re.sub('（[^（）]*）$', '', rename)
            rename = re.sub('〔[^〔〕]*〕$', '', rename)
            if name_tuple[1]:
                print_and_write(w, f"{rename},{rename},")
            else:
                print_and_write(w, f"{rename},")
        print_and_write(w, "\n,,")
        # 着発
        for str_end in all_str_end_seq:
            if str_end[1]:
                print_and_write(w, f"{str_end[0]},{str_end[1]},")
            else:
                print_and_write(w, f"{str_end[0]},")
        print_and_write(w, "\n")
        # 時刻
        for syubetsu_dest_time_seq in syubetsu_dest_time_seq_seq:
            syubetsu, dest = syubetsu_dest_time_seq[0]
            print_and_write(w, f"{syubetsu},{dest},")
            time_tuple_seq = syubetsu_dest_time_seq[1]
            for i in range(len(all_str_end_seq)):
                if all_str_end_seq[i][1] == "":
                    print_and_write(w, f"{time_tuple_seq[i][0]},")
                else:
                    if time_tuple_seq[i][1] == "":
                        check_str_seq = time_tuple_seq[:i]
                        check_str_string = ''.join([t[0] for t in check_str_seq])
                        check_end_seq = time_tuple_seq[i+1:]
                        check_end_string = ''.join([t[0] for t in check_end_seq])
                        if not check_str_string:
                            print_and_write(w, f",{time_tuple_seq[i][0]},")
                        elif check_end_string:
                            print_and_write(w, f"{time_tuple_seq[i][0]},{time_tuple_seq[i][0]},")
                        else:
                            print_and_write(w, f"{time_tuple_seq[i][0]},{time_tuple_seq[i][1]},")
                    else:
                        print_and_write(w, f"{time_tuple_seq[i][0]},{time_tuple_seq[i][1]},")
            print_and_write(w, "\n")

def main_process(uri, date_int, dir_int):
    doc = get_data(uri)

    date = "weekday" if date_int == 0 else "saturday" if date_int == 1 else "sunday"
    id_val = f"{date}-{dir_int}"
    id2 = f"segment-{dir_int}"

    div_eles = doc.find_all(attrs={"id": lambda x: x and id_val in x})
    if not div_eles:
        div_eles = doc.find_all(attrs={"id": lambda x: x and id2 in x})
    div_ele = div_eles[0] if div_eles else None

    if not div_ele:
        return []

    dl_eles = div_ele.find_all('dl')
    # print(len(dl_eles))

    name_time_tuple_list_list_buf = []
    for dl_ele in dl_eles:
        # 見やすくなるようスペース数を調整
        dl_ele_text = dl_ele.text.replace('\n', ' ').replace('       ', ' ').lstrip() 
        # 時を表示
        print(dl_ele_text)
        li_eles = dl_ele.find_all('li')
        name_time_tuple_list_buf = []
        for li_ele in li_eles:
            href = li_ele.find('a')['href'] if li_ele.find('a') else ""
            uri_detail = "https://www.navitime.co.jp" + href
            shubetsu2 = li_ele.get('data-long-name', '')
            number_pattern = re.compile(r'.*[0-9]+号.*')
            if number_pattern.match(shubetsu2):
                number_pattern2 = re.compile(r'[0-9]+号.*')
                match = number_pattern2.search(shubetsu2)
                if match:
                    number_string = match.group()
                    shubetsu_name = shubetsu2.replace(number_string, '')
                    shubetsu = f'"{shubetsu_name}\n{number_string}"'
                else:
                    shubetsu = li_ele.get('data-name', '')
            else:
                shubetsu = li_ele.get('data-name', '')

            # 駅名の（福井県）や〔東福バス〕などを削除する
            # （も）も含まない0文字以上の文字列を（）で囲んだ文字列にマッチする正規表現
            # 〔〕も同様の処理
            dest = li_ele.get('data-dest', '')
            dest = re.sub('（[^（）]*）$', '', dest)
            dest = re.sub('〔[^〔〕]*〕$', '', dest)
            print(uri_detail)
            name_time_tuple_list = get_one_page(uri_detail)
            name_time_tuple_list_buf.append((shubetsu, dest, name_time_tuple_list))
        name_time_tuple_list_list_buf.append(name_time_tuple_list_buf)
    return name_time_tuple_list_list_buf

def create_first_name_seq(name_time_table):
    size_seq = []
    for name_time_seq_t in name_time_table:
        stop_station_seq = [nt[0] for nt in name_time_seq_t[2]]
        if Global.USE:
            size = len(name_time_seq_t[2]) if Global.END in stop_station_seq else 0
        else:
            size = len(name_time_seq_t[2])
        size_seq.append(size)
    max_size = max(size_seq)

    max_size_name_seq = []
    for name_time_seq_t in name_time_table:
        if len(name_time_seq_t[2]) == max_size:
            max_size_name_seq.append([nt[0] for nt in name_time_seq_t[2]])
    return max_size_name_seq[0] if max_size_name_seq else []

def create_name_seq(old_name_seq, check_point, name_time_table):
    if check_point >= len(name_time_table):
        return old_name_seq
    check_name_time_seq = name_time_table[check_point][2]
    check_name_seq = [cnt[0] for cnt in check_name_time_seq]
    new_name_seq = create_name_seq_one(old_name_seq, 0, check_name_seq)
    return create_name_seq(new_name_seq, check_point + 1, name_time_table)

def create_name_seq_one(old_name_seq, check_point, check_name_seq):
    if check_point >= len(check_name_seq):
        return old_name_seq
    check_name = check_name_seq[check_point]
    new_name_seq = old_name_seq
    if check_name not in old_name_seq:
        check_point_in_check = check_name_seq.index(check_name)
        if check_point_in_check > 0:
            pre_check_name = check_name_seq[check_point_in_check - 1]
            if pre_check_name in old_name_seq:
                split_point = old_name_seq.index(pre_check_name)
                new_name_seq = old_name_seq[:split_point + 1] + [check_name] + old_name_seq[split_point + 1:]
            else:
                new_name_seq = [check_name] + old_name_seq
        else:
            new_name_seq = [check_name] + old_name_seq
    return create_name_seq_one(new_name_seq, check_point + 1, check_name_seq)

def check_str_end(i, time_seq_seq):
    check_str_seq = [time_seq[i][1] != "" for time_seq in time_seq_seq]
    if any(check_str_seq):
        return ("着", "発")
    else:
        if i == len(time_seq_seq[0]) - 1:
            return ("着", "")
        else:
            return ("発", "")

def get_one_page(uri):
    time.sleep(0.5)
    doc = get_data(uri)
    div_ele = doc.find_all(class_="stops-area")
    # print("div_ele:", div_ele)
    # if not div_ele:
    #     return []
    # table_eles = div_ele[0].find_all()
    table_eles = div_ele[0].find_all(class_="stops")
    # print("table_eles:", table_eles)
    name_time_tuple_buf = []
    for table_ele in table_eles:
        # print("table_ele:", table_ele)
        name = table_ele.find(class_="station-name")
        if not name:
            continue
        # name = name.text.replace("\n", "") if name else ""
        name = name.text.replace("\n", "")
        # print("name:", name)
        time_ele = table_ele.find(class_="time")
        if time_ele:
            time_val = time_ele.text.replace("発", "").replace("着", "").replace("\n", "")
        else:
            from_to_time = table_ele.find(class_="from-to-time")
            time_val = from_to_time.text.replace("発", "").replace("着", " ").replace("\n", "")
        # print("time_val:", time_val)
        name_time_tuple_buf.append((name, time_val))
    # print("name_time_tuple_buf:", name_time_tuple_buf)
    return name_time_tuple_buf

def get_data(uri):
    try:
        response = requests.get(uri)
        response.raise_for_status()
        return BeautifulSoup(response.text, 'html.parser')
    except Exception as e:
        print(e)
        return get_data(uri)

if __name__ == "__main__":
    main(sys.argv[1:])