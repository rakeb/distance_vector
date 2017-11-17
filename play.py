import operator
from collections import namedtuple


def play():
    distance_vector = namedtuple('d_v', 'router distance_vector')
    neighbours = ['x', 'y', 'z']
    next_hop = 'y'
    cost = 2.0
    touple = (next_hop, cost)

    my_router_name = 'x'
    dvs = {}
    for n in neighbours:
        dvs[n] = touple  # prepare touple for n

    matrix_distance_vector = {
        'x': {
            'x': ('x', 0),
            'y': ('y', 2),
            'z': ('z', 7),
        },
        'y': {
            'x': ('y', 3),
            'y': ('y', 1),
            'z': ('z', 5),
        },
        'z': {
            'x': ('z', 3),
            'y': ('x', 5),
            'z': ('y', 2),
        },
    }
    print(matrix_distance_vector)

    matrix_distance_vector[my_router_name] = dvs

    print(matrix_distance_vector)

    for key in matrix_distance_vector:
        print(key, " -> ", matrix_distance_vector[key])

    x = {1: 2, 3: 4, 4: 3, 2: 1, -1: 0}
    sorted_x = sorted(x.items(), key=operator.itemgetter(0))
    print(sorted_x[0])


if __name__ == '__main__':
    play()
