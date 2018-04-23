#!/usr/bin/env python
# -*- coding: utf-8 -*-

import random
import math
# import array
from tool_lib import Tool
import time

phy_server = [16, 128, 1200]
predict_result = {1: 200, 2: 40, 3: 20, 4: 10, 5: 40, 6: 40, 7: 15, 13: 10, 14: 20}
cpu_if = 1
virtual_info = {1: [1, 1], 2: [1, 2], 3: [1, 4], 4: [2, 2], 5: [2, 4], 6: [2, 8], 7: [4, 4], 13: [16, 16], 14: [16, 32]}


class Server(object):

    def __init__(self, cpu, mem):
        self.free_cpu = cpu
        self.total_cpu = cpu
        self.free_mem = mem
        self.total_mem = mem
        self.flavors = []

    def __str__(self):
        return str(self.flavors)

    def put_flavor(self, flavor):
        if self.free_cpu >= flavor[1] and self.free_mem >= flavor[2]:
            self.free_cpu -= flavor[1]
            self.free_mem -= flavor[2]
            self.flavors.append(flavor[0])
            return True
        return False

    def get_cpu_usage_rate(self):
        return float(1 - self.free_cpu / self.total_cpu)

    def get_mem_usage_rate(self):
        return float(1 - self.free_mem / self.total_mem)


def deploy_flavor(predict_result, virtual_info, phy_server, cpu_if):
    count, flavors = Tool.predict_process(predict_result, virtual_info)
    # print count, type(flavors)
    min_score = len(flavors) + 1
    best_result = []
    T = 100
    Tmin = 1
    r = 0.999
    dice = [i for i in range(count)]
    # print dice
    while T > Tmin:
        if len(dice) > 1:
            temp = random.sample(dice, 2)
            flavors[temp[0]], flavors[temp[1]] = flavors[temp[1]], flavors[temp[0]]
        else:
            pass
        servers = []
        firstserver = Server(phy_server[0], phy_server[1])
        servers.append(firstserver)

        for i in range(len(flavors)):
            for j in range(len(servers)):
                if servers[j].put_flavor(flavors[i]):
                    break
                if j == len(servers) - 1:
                    newserver = Server(phy_server[0], phy_server[1])
                    newserver.put_flavor(flavors[i])
                    servers.append(newserver)

        if cpu_if == 1:
            server_score = sum(servers[i].get_cpu_usage_rate() for i in range(len(servers)))
        else:
            server_score = sum(servers[i].get_mem_usage_rate() for i in range(len(servers)))
        # if cpu_if == 1:
        #     server_score = len(servers) - 1 + servers[-1].get_cpu_usage_rate()
        # else:
        #     server_score = len(servers) - 1 + servers[-1].get_mem_usage_rate()
        if server_score < min_score:
            min_score = server_score
            best_result = servers
        else:
            if math.exp(min_score - server_score) / T > random.random():
                min_score = server_score
                best_result = servers
        T = r * T
    final_result = []
    for i in range(len(best_result)):
        # charArray.append(array.array('B', best_result[i].flavors))
        final_result.append(best_result[i].flavors)
    return final_result


if __name__ == '__main__':
    time1 = time.time()
    result = deploy_flavor(predict_result, virtual_info, phy_server, cpu_if)
    # bag_result = Tool.bag(predict_result, cpu_if, virtual_info, phy_server)
    # print bag_result
    print result
    print time.time()-time1