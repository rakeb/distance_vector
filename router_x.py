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

import time as T_T
from time import time

import custom_utils

FREQUENCY = 15
CHECK_ROUTER_DEAD = 5
output_number = 1
PORT_RANGE = list(range(10001, 20021))

input_file = None

host = socket.gethostname()
lock = threading.RLock()
data_file_name = None
ack_socket = None
ack_port = None

alive_neighbours_dict = {}
dead_router_dict = {}
neighbours_cost_dict = None
neighbours_port_dict = {}
neighbours_port = []
all_router_port_dict = {}

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


def bellman_ford(from_router, to_router, neighbours_of_from_router):
    global neighbours_cost_dict
    _tuple = ()  # next hop, cost
    unsorted_dv = {}

    if from_router == to_router:
        _tuple = (from_router, 0.0)
        return _tuple

    # 𝑑𝑥(𝑦) = 𝑚𝑖𝑛_𝑣⁡{𝑐(𝑥, 𝑣) + 𝑑_𝑣(𝑦)}
    # Dx(y) = min {c(x, y) + Dy(y), c(x, z) + Dz(y)} = min {2 + 0, 7 + 1} = 2

    for router in neighbours_of_from_router:
        try:
            sum = neighbours_cost_dict[router] + get_d_x_y(router, to_router)
            _tuple = (router, sum)
            unsorted_dv[sum] = _tuple
        except Exception as e:
            pass  # skipping if router dead

    sorted_dv = sorted(unsorted_dv.items(), key=operator.itemgetter(0))
    _tuple = sorted_dv[0]
    # print("bellman ford returns: ", _tuple)
    return _tuple[1]


def bellman_ford_updated(from_router, to_router, neighbours_of_from_router, alive_neighbour_cost_dict):
    _tuple = ()  # next hop, cost
    unsorted_dv = {}

    if from_router == to_router:
        _tuple = (from_router, 0.0)
        return _tuple

    # 𝑑𝑥(𝑦) = 𝑚𝑖𝑛_𝑣⁡{𝑐(𝑥, 𝑣) + 𝑑_𝑣(𝑦)}
    # Dx(y) = min {c(x, y) + Dy(y), c(x, z) + Dz(y)} = min {2 + 0, 7 + 1} = 2

    print("neighbours_of_from_router :", neighbours_of_from_router)
    print("alive_neighbour_cost_dict :", alive_neighbour_cost_dict)

    for router in neighbours_of_from_router:
        try:
            sum = alive_neighbour_cost_dict[router] + get_d_x_y(router, to_router)
            _tuple = (router, sum)
            unsorted_dv[sum] = _tuple
        except Exception as e:
            pass  # skipping if router dead

    sorted_dv = sorted(unsorted_dv.items(), key=operator.itemgetter(0))
    _tuple = sorted_dv[0]
    # print("bellman ford returns: ", _tuple)
    return _tuple[1]


def calculate_distance_vector():
    global input_file
    global neighbours_cost_dict
    global all_router_port_dict
    global router_name
    global matrix_distance_vector  # {'x': {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)}, 'y': {'x': ('y', 3), 'y': ('y', 1), 'z': ('z', 5)}, 'z': {'x': ('z', 3), 'y': ('x', 5), 'z': ('y', 2)}}
    dvs = {}  # {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)}

    neighbours_cost_dict = custom_utils.parse_input_file(input_file)  # {'y': 2.0, 'z': 7.0}
    neighbours = custom_utils.get_keys_from_dict(neighbours_cost_dict)  # ['y', 'z']
    all_router = custom_utils.get_keys_from_dict(all_router_port_dict)  # ['x', 'y', 'z']
    # all_router.append(router_name)

    # what will finally happen
    # print("all routers: ", all_router)
    for router in all_router:
        dvs[router] = bellman_ford(router_name, router, neighbours)  # prepare tuple for router
    matrix_distance_vector[router_name] = dvs

    return dvs


def calculate_distance_vector_updated():
    global dead_router_dict
    global input_file
    global neighbours_cost_dict
    global alive_neighbours_dict
    global all_router_port_dict
    global router_name
    global matrix_distance_vector  # {'x': {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)}, 'y': {'x': ('y', 3), 'y': ('y', 1), 'z': ('z', 5)}, 'z': {'x': ('z', 3), 'y': ('x', 5), 'z': ('y', 2)}}
    dvs = {}  # {'x': ('y', 2.0), 'y': ('y', 2.0), 'z': ('y', 2.0)}

    from_file_neighbours_cost_dict = custom_utils.parse_input_file(input_file)  # {'y': 2.0, 'z': 7.0}
    # print("from_file_neighbours_cost_dict: ", from_file_neighbours_cost_dict)

    dead_router_list = custom_utils.get_keys_from_dict(dead_router_dict)
    # print("dead_router_list: ", dead_router_list)
    for dead_router in dead_router_list:
        try:
            del from_file_neighbours_cost_dict[dead_router]
        except Exception as e:
            pass

    neighbours = custom_utils.get_keys_from_dict(from_file_neighbours_cost_dict)  # ['y', 'z']

    all_router = custom_utils.get_keys_from_dict(all_router_port_dict)  # ['x', 'y', 'z']
    # all_router.append(router_name)

    # what will finally happen
    # print("all routers: ", all_router)
    for router in all_router:
        dvs[router] = bellman_ford_updated(router_name, router, neighbours,
                                           from_file_neighbours_cost_dict)  # prepare tuple for router
    matrix_distance_vector[router_name] = dvs

    return dvs


def send_dvs_to_neighbours(dv_list, ports):
    global router_name
    global host
    distance_vector_pkt = namedtuple('dvs_pkt', 'dvs router_name dv_list')
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


def send_recursion_free_dvs(dv_list):
    global router_name
    global host
    global neighbours_port_dict
    distance_vector_pkt = namedtuple('dvs_pkt', 'dvs router_name dv_list')
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a socket object

    # print("broadcast dvs packet ", pkt_list)

    # print("neighbours_port_dict ", neighbours_port_dict)

    dvs_pkt = distance_vector_pkt('dvs', router_name, dv_list)
    pkt_list = [dvs_pkt.dvs, dvs_pkt.router_name, dvs_pkt.dv_list]
    pkt = pickle.dumps(pkt_list)
    send_modified_pkt = None

    for neighbour_router_name, port in neighbours_port_dict.items():
        if port != ack_port:
            send_modified_pkt = False
            copy_dv_list = dv_list.copy()
            for going_to_router, _tuple in dv_list.items():
                next_hop = _tuple[0]
                # cost = _tuple[1]
                if neighbour_router_name == next_hop:
                    _tuple = (next_hop, sys.float_info.max)
                    copy_dv_list[going_to_router] = _tuple
                    send_modified_pkt = True
            if send_modified_pkt:
                m_dvs_pkt = distance_vector_pkt('dvs', router_name, copy_dv_list)
                m_pkt_list = [m_dvs_pkt.dvs, m_dvs_pkt.router_name, m_dvs_pkt.dv_list]
                m_pkt = pickle.dumps(m_pkt_list)
                # print("broadcast dvs packet, router: ", neighbour_router_name, " packet: ", m_pkt_list)
                s.sendto(m_pkt, (host, port))
            else:
                # print("broadcast dvs packet, router: ", neighbour_router_name, " packet: ", pkt_list)
                s.sendto(pkt, (host, port))

    s.close()


# python signal handler, param unused but required as the handler fired by the system
def re_transmitter(signum, frame):
    global neighbours_port
    # print("neighbours_port_dict: ", neighbours_port_dict)
    # print("neighbours_port: ", neighbours_port)
    dv_list = calculate_distance_vector_updated()

    # print("Calculated dv_list: ", dv_list)
    # print_dvs_matrix()
    remove_recursion = custom_utils.read_config()
    if remove_recursion == "True":
        send_recursion_free_dvs(dv_list)
    else:
        send_dvs_to_neighbours(dv_list, neighbours_port)

    print_output(dv_list)


def broadcast():
    global host
    # handshake_pkt = namedtuple('handshake_pkt', 'protocol max_seq_num window_size total_packets')
    handshake_pkt = namedtuple('handshake_pkt', 'what_is_your_port router_name my_port')
    # make handshaking packet
    hs_pkt = handshake_pkt('what_is_your_port', router_name, ack_port)
    pkt_list = [hs_pkt.what_is_your_port, hs_pkt.router_name, hs_pkt.my_port]
    pkt = pickle.dumps(pkt_list)

    # print("broadcast packet ", pkt_list)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a socket object
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


# neighbours_port_dict and all_router_port get updated here
def update_neighbour_ports(data):
    global dead_router_dict
    global neighbours_port
    global neighbours_port_dict
    global all_router_port_dict
    _router_name = data[1]
    _port_number = data[2]

    neighbours = custom_utils.get_keys_from_dict(neighbours_cost_dict)

    if _router_name in neighbours:
        neighbours_port_dict[_router_name] = _port_number
        neighbours_port.append(_port_number)

    all_router_port_dict[_router_name] = _port_number

    try:
        del dead_router_dict[_router_name]
    except Exception as e:
        pass

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


def update_liveliness_of_router(data):
    global alive_neighbours_dict
    received_router_name = data[1]
    alive_neighbours_dict[received_router_name] = time()


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
            update_liveliness_of_router(data)
        if check_pkt == 'router_dead':
            remove_router_from_network(data[1])


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


def remove_router_from_network(r_name):
    global dead_router_dict

    global neighbours_cost_dict
    global neighbours_port_dict
    global all_router_port_dict
    global alive_neighbours_dict
    # print("**** Router name will be deleted: ", r_name)

    # print("before removing neighbours_cost_dict", neighbours_cost_dict)
    # print("before removing neighbours_port_dict", neighbours_port_dict)
    # print("before removing all_router_port_dict", all_router_port_dict)
    # print("before removing alive_neighbours_dict", alive_neighbours_dict)

    dead_router_dict[r_name] = True

    try:
        del neighbours_cost_dict[r_name]
        del neighbours_port_dict[r_name]
        del all_router_port_dict[r_name]
        del alive_neighbours_dict[r_name]
    except Exception as e:
        pass

    # print("after removing neighbours_cost_dict", neighbours_cost_dict)
    # print("after removing neighbours_port_dict", neighbours_port_dict)
    # print("after removing all_router_port_dict", all_router_port_dict)
    # print("after removing alive_neighbours_dict", alive_neighbours_dict)


def broadcast_router_dead(r_name):
    global all_router_port_dict
    global host
    router_dead_pkt_tuple = namedtuple('router_dead_pkt', 'router_dead router_name')
    router_dead_pkt = router_dead_pkt_tuple('router_dead', r_name)
    pkt_list = [router_dead_pkt.router_dead, router_dead_pkt.router_name]
    pkt = pickle.dumps(pkt_list)

    # print("broadcast packet ", pkt_list)

    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # Create a socket object
    for router_name, port in all_router_port_dict.items():
        if port != ack_port:
            # print("broadcast port scanning to ", port)
            s.sendto(pkt, (host, port))

    s.close()


def check_neighbour_alive():
    global alive_neighbours_dict
    while True:
        dead_routers = []
        # print("alive_neighbours_dict ", alive_neighbours_dict)
        for r_name, start_time in alive_neighbours_dict.items():
            end_time = time()
            time_taken = end_time - start_time  # time_taken is in seconds
            if time_taken > CHECK_ROUTER_DEAD:
                dead_routers.append(r_name)
        for r_name in dead_routers:
            remove_router_from_network(r_name)
            broadcast_router_dead(r_name)
        T_T.sleep(CHECK_ROUTER_DEAD + 2)


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
    threading.Thread(target=check_neighbour_alive, args=()).start()

    # print("after thread, boradcast...")

    broadcast()


def print_dvs_matrix():
    global matrix_distance_vector
    for key in matrix_distance_vector:
        print(key, " -> ", matrix_distance_vector[key])


def main():
    global neighbours_cost_dict
    global router_name
    global input_file
    input_file, router_name = custom_utils.parse_command_line_arguments()
    neighbours_cost_dict = custom_utils.parse_input_file(input_file)

    print("Router started as: ", router_name)
    # print("Neighbours cost: ", neighbours_cost)

    # neighbours = custom_utils.get_keys_from_dict(neighbours_cost_dict)
    # print("Neighbours: ", neighbours)

    start_router_x()


if __name__ == "__main__":
    main()
