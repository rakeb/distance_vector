# Author Md Mazharul Islam Rakeb
# Email: mislam7@uncc.edu,
#        rakeb.mazharul@gmail.com

import operator
import pickle
import signal
import socket
import sys
import threading
from collections import namedtuple

import custom_utils

FREQUENCY = 5
output_number = 1
PORT_RANGE = list(range(10001, 20021))

input_file = None

host = socket.gethostname()
lock = threading.RLock()
data_file_name = None
ack_socket = None
ack_port = None
neighbours = []
neighbours_cost = None
neighbours_port_dict = {}
neighbours_port = []

all_router_port = {}
all_router = []
router_name = None

matrix_distance_vector = {}


def get_d_x_y(x, y):
    if x == y:
        return 0.0

    # {
    #     'x': {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)},
    #     'y': {'x': ('y', 3), 'y': ('y', 1), 'z': ('z', 5)},
    #     'z': {'x': ('z', 3), 'y': ('x', 5), 'z': ('y', 2)}
    # }
    global matrix_distance_vector
    cost = sys.float_info.max
    try:
        dvs = matrix_distance_vector[x]
        _tuple = dvs[y]
        cost = _tuple[1]
    except Exception as e:
        pass
    # print("From ", x, " to ", y, " Cost = ", cost)
    return cost


def bellman_ford(from_router, to_router, neighbour_of_from_router):
    global neighbours_cost
    _tuple = ()  # next hop, cost
    unsorted_dv = {}

    if from_router == to_router:
        _tuple = (from_router, 0.0)
        return _tuple

    # 𝑑𝑥(𝑦) = 𝑚𝑖𝑛_𝑣⁡{𝑐(𝑥, 𝑣) + 𝑑_𝑣(𝑦)}
    # Dx(y) = min {c(x, y) + Dy(y), c(x, z) + Dz(y)} = min {2 + 0, 7 + 1} = 2

    for router in neighbour_of_from_router:
        sum = neighbours_cost[router] + get_d_x_y(router, to_router)
        _tuple = (router, sum)
        unsorted_dv[sum] = _tuple

    sorted_dv = sorted(unsorted_dv.items(), key=operator.itemgetter(0))
    _tuple = sorted_dv[0]
    # print("bellman ford returns: ", _tuple)
    return _tuple[1]


def calculate_distance_vector():
    global input_file
    global neighbours_cost
    global neighbours
    global all_router_port
    global all_router
    global router_name
    global matrix_distance_vector  # {'x': {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)}, 'y': {'x': ('y', 3), 'y': ('y', 1), 'z': ('z', 5)}, 'z': {'x': ('z', 3), 'y': ('x', 5), 'z': ('y', 2)}}
    dvs = {}  # {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)}

    neighbours_cost = custom_utils.parse_input_file(input_file)  # {'y': 2.0, 'z': 7.0}
    neighbours = custom_utils.get_keys_from_dict(neighbours_cost)  # ['y', 'z']
    all_router = custom_utils.get_keys_from_dict(all_router_port)  # ['x', 'y', 'z']
    # all_router.append(router_name)

    # what will finally happen
    # print("all routers: ", all_router)
    for router in all_router:
        dvs[router] = bellman_ford(router_name, router, neighbours)  # prepare tuple for router
    matrix_distance_vector[router_name] = dvs

    return dvs


def send_dvs_to_neighbours(dv_list, ports):
    global router_name
    global host
    distance_vector_pkt = namedtuple('dvs_pkt', 'dvs router_name dv_list')
    # make handshaking packet
    dvs_pkt = distance_vector_pkt('dvs', router_name, dv_list)
    pkt_list = [dvs_pkt.dvs, dvs_pkt.router_name, dvs_pkt.dv_list]
    pkt = pickle.dumps(pkt_list)

    # print("broadcast dvs packet ", pkt_list)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a socket object
    for port in ports:
        if port != ack_port:
            s.sendto(pkt, (host, port))
    s.close()


def print_output(dv_list):
    global router_name
    global output_number
    print("output number ", output_number)
    output_number += 1

    # {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)}
    for router in dv_list:
        _tuple = dv_list[router]
        print("shortest path ", router_name, "-", router, ": the next hop is ", _tuple[0], " and the cost is ",
              _tuple[1])


# python signal handler, param unused but required as the handler fired by the system
def re_transmitter(signum, frame):
    global neighbours_port
    # print("neighbours_port_dict: ", neighbours_port_dict)
    # print("neighbours_port: ", neighbours_port)
    dv_list = calculate_distance_vector()

    # print("Calculated matrix: ")
    # print_dvs_matrix()

    send_dvs_to_neighbours(dv_list, neighbours_port)

    print_output(dv_list)


def broadcast():
    # handshake_pkt = namedtuple('handshake_pkt', 'protocol max_seq_num window_size total_packets')
    handshake_pkt = namedtuple('handshake_pkt', 'what_is_your_port router_name my_port')
    # make handshaking packet
    hs_pkt = handshake_pkt('what_is_your_port', router_name, ack_port)
    pkt_list = [hs_pkt.what_is_your_port, hs_pkt.router_name, hs_pkt.my_port]
    pkt = pickle.dumps(pkt_list)

    # print("broadcast packet ", pkt_list)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a socket object
    host = socket.gethostname()  # Get local machine name
    for port in PORT_RANGE:
        if port != ack_port:
            # print("broadcast port scanning to ", port)
            s.sendto(pkt, (host, port))

    s.close()


def send_my_port(data):
    global host
    global ack_port
    global router_name

    send_port_to = data[2]

    my_port_pkt = namedtuple('my_port_pkt', 'my_port router_name port_number ')
    mp_pkt = my_port_pkt('my_port', router_name, ack_port)
    pkt_list = [mp_pkt.my_port, mp_pkt.router_name, mp_pkt.port_number]
    pkt = pickle.dumps(pkt_list)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a socket object
    s.sendto(pkt, (host, send_port_to))
    s.close()


def update_neighbour_ports(data):
    global neighbours
    global neighbours_port_dict
    _router_name = data[1]
    _port_number = data[2]
    if _router_name in neighbours:
        neighbours_port_dict[_router_name] = _port_number
        neighbours_port.append(_port_number)

    all_router_port[_router_name] = _port_number

    # print("neighbours_port: ", neighbours_port_dict)


def update_distance_vector_matrix(data):
    global matrix_distance_vector
    received_router_name = data[1]
    received_dvs = data[2]
    current_dvs = None
    try:
        current_dvs = matrix_distance_vector[received_router_name]
    except Exception as e:
        pass
    # print("previous dvs: ", current_dvs)
    # print("received dvs: ", received_dvs)

    matrix_distance_vector[received_router_name] = received_dvs

    # print("Updated matrix: ")
    # print_dvs_matrix()


def asynchronous_receiver():
    global FREQUENCY
    # print("inside async received...")
    while True:
        # print(ack_port)
        data = pickle.loads(ack_socket.recv(100000))
        # print(ack_port)

        # print("Data: ", data)
        check_pkt = data[0]
        if check_pkt == 'what_is_your_port':
            send_my_port(data)
            update_neighbour_ports(data)
        if check_pkt == 'my_port':
            update_neighbour_ports(data)
        if check_pkt == 'dvs':
            update_distance_vector_matrix(data)


def set_ack_socket():
    global ack_socket
    global ack_port
    global host
    ack_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # UDP Foo

    for port in PORT_RANGE:
        try:
            ack_socket.bind((host, port))
            ack_port = port
            return ack_port
        except Exception as e:
            pass


def start_router_x():
    global ack_port
    global lock
    global FREQUENCY
    # print("before setting ", ack_port)
    # ack_port = get_my_port()
    set_ack_socket()  # temp port for receiving broadcast
    print("Router listening at port: ", ack_port)

    signal.signal(signal.SIGALRM, re_transmitter)

    lock.acquire()
    signal.setitimer(signal.ITIMER_REAL, FREQUENCY, FREQUENCY)  # start timer
    lock.release()

    threading.Thread(target=asynchronous_receiver, args=()).start()

    # print("after thread, boradcast...")

    broadcast()


def print_dvs_matrix():
    global matrix_distance_vector
    for key in matrix_distance_vector:
        print(key, " -> ", matrix_distance_vector[key])


def main():
    global neighbours_cost
    global router_name
    global input_file
    global neighbours
    input_file, router_name = custom_utils.parse_command_line_arguments()
    neighbours_cost = custom_utils.parse_input_file(input_file)

    print("Router started as: ", router_name)
    # print("Neighbours cost: ", neighbours_cost)

    neighbours = custom_utils.get_keys_from_dict(neighbours_cost)
    # print("Neighbours: ", neighbours)

    start_router_x()


if __name__ == "__main__":
    main()
