# Author Md Mazharul Islam Rakeb
# Email: mislam7@uncc.edu,
#        rakeb.mazharul@gmail.com

import configparser
import pickle
import sys


def parse_command_line_arguments():
    try:
        input_file = sys.argv[1]
        # print(input_file)
        router_name = input_file.split('/')[1].split('.')[0]
        # print(router_name)

    except:
        print("Provide <file_name> <port_number> and <number_of_packets> as argument")
        exit(0)

    return input_file, router_name


def parse_input_file(input_file):
    try:
        with open(input_file, 'r') as f:
            content = f.readlines()

    except:
        sys.exit("Failed to open file!")

    content = [x.strip() for x in content]

    neighbours = {}
    num_of_neighbours = int(content[0])
    for i in range(1, num_of_neighbours + 1):
        key = content[i].split(" ")[0]
        value = float(content[i].split(" ")[1])
        neighbours[key] = value
        # print(value)
    # print(neighbours)

    return neighbours


def read_config():
    config = configparser.ConfigParser()
    config.read('config.ini')
    default_config = config['DEFAULT']
    remove_recursion = default_config['remove_recursion']

    return remove_recursion


def get_keys_from_dict(_dict):
    _list = []
    for key in _dict:
        _list.append(key)
    return _list
